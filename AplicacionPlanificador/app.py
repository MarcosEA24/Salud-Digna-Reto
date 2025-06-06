from flask import Flask, render_template, jsonify, request
from config import SUCURSALES, ESTUDIOS, MEDIAS, TAP, cabinas_por_sucursal
import random
import itertools
from collections import Counter

app = Flask(__name__)

def simula_ruta(ruta, filas, tap, cabinas_dict):
    # Simula el tiempo total de la ruta dada el estado de las filas, los TAPs y las cabinas
    # Inicializa el estado de las cabinas para cada estudio
    cabinas = {e: [0.0] * cabinas_dict.get(e, 1) for e in cabinas_dict}
    t = 0
    detail = []
    for estudio in ruta:
        tap_val = tap.get(estudio, 10)
        n_cab = len(cabinas.get(estudio, [0.0]))
        # Simula la espera inicial por las personas en fila
        espera = 0
        if n_cab > 0:
            # Calcula el tiempo en el que estará libre la cabina más próxima
            cabina_idx = min(range(n_cab), key=lambda i: cabinas[estudio][i])
            # El paciente debe esperar a que terminen los que están antes en la fila
            espera_fila = filas.get(estudio, 0) * tap_val
            # El tiempo de inicio es el máximo entre el tiempo actual + espera_fila y la cabina disponible
            start = max(t + espera_fila, cabinas[estudio][cabina_idx])
            fin = start + tap_val
            cabinas[estudio][cabina_idx] = fin
            espera = start - t
            t = fin
        else:
            # Si no hay cabinas, solo suma el tap y la espera de fila
            espera = filas.get(estudio, 0) * tap_val
            t += espera + tap_val
        detail.append({'estudio': estudio, 'espera': espera, 'tap': tap_val, 'total': espera + tap_val})
    return t, detail

def mut_swap(ind):
    if len(ind) < 2:
        return ind
    i, j = random.sample(range(len(ind)), 2)
    ind = list(ind)
    ind[i], ind[j] = ind[j], ind[i]
    return tuple(ind)

def ox(p1, p2):
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

def mejor_ruta_exhaustiva(estudios, filas, tap, cabinas_dict):
    best, best_t, best_detail = None, float('inf'), None
    for perm in itertools.permutations(estudios):
        tat, detail = simula_ruta(perm, filas, tap, cabinas_dict)
        if tat < best_t:
            best, best_t, best_detail = perm, tat, detail
    return best, best_t, best_detail

def ga_ruta(estudios, filas, tap, cabinas_dict, N=40, G=120, pc=0.9, pm=None):
    if pm is None:
        pm = 1 / len(estudios)
    def fitness(r):
        return 1.0 / simula_ruta(r, filas, tap, cabinas_dict)[0]
    def torneo(pop):
        return max(random.sample(pop, 3), key=fitness)
    pobl = [tuple(random.sample(estudios, len(estudios))) for _ in range(N)]
    best = min(pobl, key=lambda r: simula_ruta(r, filas, tap, cabinas_dict)[0])
    for _ in range(G):
        nueva = [best]
        while len(nueva) < N:
            p1, p2 = torneo(pobl), torneo(pobl)
            h1, h2 = ox(p1, p2) if random.random() < pc else (p1, p2)
            if random.random() < pm: h1 = mut_swap(h1)
            if random.random() < pm: h2 = mut_swap(h2)
            nueva.extend((h1, h2))
        pobl = nueva[:N]
        cand = min(pobl, key=lambda r: simula_ruta(r, filas, tap, cabinas_dict)[0])
        if simula_ruta(cand, filas, tap, cabinas_dict)[0] < simula_ruta(best, filas, tap, cabinas_dict)[0]:
            best = cand
    best_t, best_detail = simula_ruta(best, filas, tap, cabinas_dict)
    return best, best_t, best_detail

@app.route('/')
def index():
    return render_template('planificador.html', sucursales=SUCURSALES, estudios=ESTUDIOS)

@app.route('/get_medias', methods=['GET'])
def get_medias():
    sucursal = request.args.get('sucursal')
    if not sucursal or sucursal not in MEDIAS:
        return jsonify({'error': 'Sucursal no válida'}), 400
    return jsonify({'media': MEDIAS[sucursal]})

@app.route('/get_random_queues', methods=['GET'])
def get_random_queues():
    filas = {estudio: random.randint(0, 5) for estudio in ESTUDIOS}
    return jsonify(filas)

@app.route('/generar_ruta', methods=['POST'])
def generar_ruta():
    data = request.json
    sucursal = data.get('sucursal')
    estudios = data.get('estudios', [])
    filas = data.get('filas', {})
    if not sucursal or not estudios or not filas:
        return jsonify({'error': 'Datos insuficientes'}), 400
    tap_sucursal = TAP.get(sucursal, {})
    cabinas_dict = cabinas_por_sucursal.get(sucursal, {})
    if len(estudios) <= 5:
        best_perm, best_time, best_detail = mejor_ruta_exhaustiva(estudios, filas, tap_sucursal, cabinas_dict)
    else:
        best_perm, best_time, best_detail = ga_ruta(estudios, filas, tap_sucursal, cabinas_dict)
    return jsonify({
        'ruta': list(best_perm),
        'detalle': best_detail,
        'tiempo_estimado_total': best_time
    })

if __name__ == '__main__':
    app.run(debug=True) 