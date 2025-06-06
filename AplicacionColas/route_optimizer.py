import pandas as pd
import numpy as np
import random
import ast
import heapq
from collections import Counter
from itertools import permutations
from typing import List, Tuple, Dict

# Parámetros de variabilidad
SIGMA_ARR = 2.0    # min – desviación estándar en la hora de llegada
CV_TAP = 0.30      # sin unidad – coef. de variación del TAP
SIGMA_WALK = 0.5   # min – desviación estándar en desplazamiento
BASE_TRANSIT = 1.5 # min – tiempo medio de caminar entre áreas
MU_PREP = 1.0      # min – tiempo medio de preparación previa
SIGMA_PREP = 0.5   # min – desviación estándar de preparación
PROB_REPETIR = 0.03 # 3% de estudios se repiten

class RouteOptimizer:
    def __init__(self, seed=None):
        self.rng = np.random.default_rng(seed)
        self.cabinas = {}
        self.tap_base = {}
        self.agenda = []
        self.queue_lengths = {}  # Para tracking de colas por estudio
        self.current_time = 0

    def _simula_ruta(self, ruta: Tuple[str, ...], arrival: float,
                    tap: Dict[str, float], cabinas_snapshot: Dict[str, List[float]]) -> float:
        cabinas = {e: t.copy() for e, t in cabinas_snapshot.items()}
        t = arrival
        for est_tag in ruta:
            base = est_tag.split('#')[0]
            dur = tap[est_tag]
            idx = min(range(len(cabinas[base])), key=cabinas[base].__getitem__)
            start = max(t, cabinas[base][idx])
            end = start + dur
            cabinas[base][idx] = end
            t = end
        return t - arrival

    def _mut_swap(self, ind):
        if len(ind) < 2:
            return ind
        i, j = random.sample(range(len(ind)), 2)
        ind = list(ind)
        ind[i], ind[j] = ind[j], ind[i]
        return tuple(ind)

    def _ox(self, p1, p2):
        k = len(p1)
        a, b = sorted(random.sample(range(k), 2))
        child1 = [None] * k
        child1[a:b] = p1[a:b]
        need, have = Counter(p1), Counter(child1[a:b])
        pos = b
        for g in p2:
            if have[g] >= need[g]:
                continue
            while child1[pos % k] is not None:
                pos += 1
            child1[pos % k] = g
            have[g] += 1
            pos += 1
        child2 = [None] * k
        child2[a:b] = p2[a:b]
        need, have = Counter(p2), Counter(child2[a:b])
        pos = b
        for g in p1:
            if have[g] >= need[g]:
                continue
            while child2[pos % k] is not None:
                pos += 1
            child2[pos % k] = g
            have[g] += 1
            pos += 1
        return tuple(child1), tuple(child2)

    def _mejor_ruta_exhaustiva(self, estudios: List[str], arrival, tap, cabinas_snapshot):
        best, best_t = None, float('inf')
        for perm in permutations(estudios):
            tat = self._simula_ruta(perm, arrival, tap, cabinas_snapshot)
            if tat < best_t:
                best, best_t = perm, tat
        return best, best_t

    def _ga_ruta(self, estudios: List[str], arrival, tap, cabinas_snapshot,
                N=40, G=120, pc=0.9, pm=None):
        if pm is None:
            pm = 1 / len(estudios)

        def fitness(r): return 1.0 / self._simula_ruta(r, arrival, tap, cabinas_snapshot)
        def torneo(pop): return max(random.sample(pop, 3), key=fitness)

        pobl = [tuple(random.sample(estudios, len(estudios))) for _ in range(N)]
        best = min(pobl, key=fitness)
        for _ in range(G):
            nueva = [best]
            while len(nueva) < N:
                p1, p2 = torneo(pobl), torneo(pobl)
                h1, h2 = self._ox(p1, p2) if random.random() < pc else (p1, p2)
                if random.random() < pm: h1 = self._mut_swap(h1)
                if random.random() < pm: h2 = self._mut_swap(h2)
                nueva.extend((h1, h2))
            pobl = nueva[:N]
            cand = min(pobl, key=fitness)
            if fitness(cand) < fitness(best):
                best = cand
        return best, self._simula_ruta(best, arrival, tap, cabinas_snapshot)

    def planificar_dia(self, pacientes_df: pd.DataFrame,
                      cabinas_por_sucursal: Dict[str, Dict[str, int]],
                      tap_df: pd.DataFrame) -> pd.DataFrame:
        
        df = pacientes_df.sort_values('LlegadaMin').reset_index(drop=True)
        df['Estudios'] = df['Estudios'].apply(
            lambda x: ast.literal_eval(x) if not isinstance(x, list) else x
        )

        sucursal = df['Sucursal'].iloc[0]
        capacidad = cabinas_por_sucursal[sucursal]
        self.cabinas = {e: [0.0] * capacidad[e] for e in capacidad}

        self.tap_base = (tap_df.query("Sucursal == @sucursal")
                               .set_index('EstudioModalidad')['TAPMinutos']
                               .to_dict())

        agenda, rutas = [], {}
        self.queue_lengths = {estudio: [] for estudio in self.tap_base.keys()}

        # Planificar rutas
        for _, pac in df.iterrows():
            k = len(pac['Estudios'])
            if k <= 5:
                ruta, _ = self._mejor_ruta_exhaustiva(pac['Estudios'],
                                                    pac['LlegadaMin'], self.tap_base, self.cabinas)
            else:
                ruta, _ = self._ga_ruta(pac['Estudios'],
                                      pac['LlegadaMin'], self.tap_base, self.cabinas)
            rutas[pac['PacienteID']] = ruta

        # Simular eventos
        event_q = []
        for _, pac in df.iterrows():
            arr = max(0.0, pac['LlegadaMin'] + self.rng.normal(0, SIGMA_ARR))
            heapq.heappush(event_q, (arr, 'arrival',
                                   pac['PacienteID'], 0, pac['Fecha']))

        llegada_estudio = {}
        dur_estudio = {}
        inicio_estudio = {}
        espera_estudio = {}  # Para trackear el tiempo de espera

        def tap_real(est):
            base = self.tap_base[est]
            sample = self.rng.normal(base, base * CV_TAP)
            return max(base, sample)

        while event_q:
            t, kind, pid, idx, fecha = heapq.heappop(event_q)
            self.current_time = t
            est = rutas[pid][idx]

            # Actualizar longitudes de cola
            for estudio in self.queue_lengths:
                count = 0
                for (p, i), q_time in llegada_estudio.items():
                    if rutas[p][i] == estudio:
                        # Si el paciente está esperando (no ha comenzado su atención)
                        if (p, i) in espera_estudio and espera_estudio[(p, i)] > t:
                            count += 1
                self.queue_lengths[estudio].append(count)

            if kind == 'arrival':
                q_time = t + max(0, BASE_TRANSIT + self.rng.normal(0, SIGMA_WALK))
                llegada_estudio[(pid, idx)] = q_time
                heapq.heappush(event_q, (q_time, 'start', pid, idx, fecha))

            elif kind == 'start':
                idx_cab = min(range(len(self.cabinas[est])), key=self.cabinas[est].__getitem__)
                dur = tap_real(est)
                prep_time = max(0, self.rng.normal(MU_PREP, SIGMA_PREP))
                start = max(t + prep_time, self.cabinas[est][idx_cab])
                fin = start + dur
                self.cabinas[est][idx_cab] = fin
                dur_estudio[(pid, idx)] = dur
                inicio_estudio[(pid, idx)] = start
                # Registrar el tiempo de espera
                espera_estudio[(pid, idx)] = start
                heapq.heappush(event_q, (fin, 'finish', pid, idx, fecha))

            else:  # finish
                q_time = llegada_estudio.pop((pid, idx))
                start = inicio_estudio.pop((pid, idx))
                dur = dur_estudio.pop((pid, idx))
                espera_estudio.pop((pid, idx))  # Eliminar el registro de espera

                agenda.append({
                    'PacienteID': pid,
                    'Sucursal': sucursal,
                    'Estudio': est,
                    'Llegada': q_time,
                    'Inicio': start,
                    'Fin': t,
                    'Tiempo de espera': start - q_time,
                    'Tiempo de atencion': dur,
                    'Ruta': rutas[pid],
                    'Fecha': fecha
                })

                # Verifica si hay que repetir el estudio
                if self.rng.random() < PROB_REPETIR:
                    q_reintento = t + max(0, BASE_TRANSIT + self.rng.normal(0, SIGMA_WALK))
                    llegada_estudio[(pid, idx)] = q_reintento
                    heapq.heappush(event_q, (q_reintento, 'start', pid, idx, fecha))
                    continue

                # Si no hay repetición, avanza al siguiente
                if idx + 1 < len(rutas[pid]):
                    q_next = t + max(0, BASE_TRANSIT + self.rng.normal(0, SIGMA_WALK))
                    llegada_estudio[(pid, idx + 1)] = q_next
                    heapq.heappush(event_q, (q_next, 'start', pid, idx + 1, fecha))

        return pd.DataFrame(agenda), self.queue_lengths 