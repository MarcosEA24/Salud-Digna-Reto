import pandas as pd
import os
import numpy as np
from scipy.stats import weibull_min
import random
from typing import List

# Definir la ruta base para los archivos de datos
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# Lista de sucursales disponibles
SUCURSALES = [
    "COYOACAN",
    "CULIACAN",
    "CULIACAN CAÑADAS",
    "CULIACAN COLEGIO MILITAR",
    "CULIACAN LA CONQUISTA",
    "CULIACAN LAS TORRES",
    "CULIACAN NAKAYAMA",
    "CULIACAN UNIVERSITARIOS"
]

# Cargar datos de distribución
def load_distribution_data():
    try:
        print("\nVerificando carga de datos...")
        
        # Verificar que los archivos existan
        required_files = [
            "distribucion_llegada.csv",
            "distribucion_cantidad_estudios.csv",
            "promedio_estudios.csv",
            "medias_por_estudio_sucursal.xlsx"
        ]
        
        for file in required_files:
            file_path = os.path.join(DATA_DIR, file)
            if not os.path.exists(file_path):
                print(f"❌ Error: No se encuentra el archivo {file}")
                return None
            print(f"✅ Archivo encontrado: {file}")
        
        # Cargar los datos
        distribucion_llegada = pd.read_csv(os.path.join(DATA_DIR, "distribucion_llegada.csv"))
        print(f"✅ Distribución de llegada cargada: {len(distribucion_llegada)} filas")
        
        distribucion_cantidad_estudios = pd.read_csv(os.path.join(DATA_DIR, "distribucion_cantidad_estudios.csv"))
        print(f"✅ Distribución de cantidad de estudios cargada: {len(distribucion_cantidad_estudios)} filas")
        
        probabilidad_estudios = pd.read_csv(os.path.join(DATA_DIR, "promedio_estudios.csv"))
        print(f"✅ Probabilidad de estudios cargada: {len(probabilidad_estudios)} filas")
        
        media_tiempo_atencion = pd.read_excel(os.path.join(DATA_DIR, "medias_por_estudio_sucursal.xlsx"))
        media_tiempo_atencion = media_tiempo_atencion[["Sucursal", "EstudioModalidad", "TAPMinutos"]]
        print(f"✅ Medias de tiempo de atención cargadas: {len(media_tiempo_atencion)} filas")
        
        print("\nTodos los datos se cargaron correctamente! ✅\n")
        
        return {
            'distribucion_llegada': distribucion_llegada,
            'distribucion_cantidad_estudios': distribucion_cantidad_estudios,
            'probabilidad_estudios': probabilidad_estudios,
            'media_tiempo_atencion': media_tiempo_atencion
        }
    except Exception as e:
        print(f"❌ Error al cargar los datos: {str(e)}")
        return None

# Funciones de generación de datos
def filtrar_por_sucursal(df: pd.DataFrame, sucursal: str) -> pd.DataFrame:
    """Devuelve solo las filas de la sucursal y resetea el índice."""
    return df[df["Sucursal"] == sucursal].reset_index(drop=True)

def ajustar_parametros_weibull(tabla_llegadas: pd.DataFrame):
    """Ajusta una distribución Weibull a los datos de llegadas por intervalo."""
    datos = tabla_llegadas["Cantidad"].values
    params = weibull_min.fit(datos, floc=0)
    return params

def generar_llegadas(tabla_llegadas: pd.DataFrame) -> List[float]:
    """Genera tiempos de llegada simulados usando parámetros ajustados de una distribución Weibull."""
    forma, loc, escala = ajustar_parametros_weibull(tabla_llegadas)
    tiempos = []
    for _, fila in tabla_llegadas.iterrows():
        base = pd.to_timedelta(fila["Hora"]).total_seconds() / 60
        cantidad = int(weibull_min.rvs(c=forma, loc=loc, scale=escala))
        for _ in range(cantidad):
            tiempos.append(base + random.uniform(0, 10))
    return sorted(tiempos)

def sortear_k(tabla_k: pd.DataFrame) -> int:
    """Sortea la cantidad de estudios según la distribución."""
    valores = tabla_k["CantidadEstudios"].values
    probs = tabla_k["Probabilidad"].values
    return int(np.random.choice(valores, p=probs))

def sortear_estudios(tabla_prob: pd.DataFrame, k: int) -> List[str]:
    """Sortea k estudios distintos según las probabilidades."""
    est = tabla_prob["EstudioModalidad"].values
    p = tabla_prob["Probabilidad"].values
    p = p / p.sum()
    k = min(k, len(est))
    elegidos = np.random.choice(est, size=k, replace=False, p=p)
    return list(elegidos)

def calcular_probabilities(distribucion_cantidad_estudios):
    """Calcula las probabilidades para cada fila en la distribución de cantidad de estudios"""
    total_pacientes_por_sucursal = distribucion_cantidad_estudios.groupby("Sucursal")["NumPacientes"].transform('sum')
    distribucion_cantidad_estudios["Probabilidad"] = distribucion_cantidad_estudios["NumPacientes"] / total_pacientes_por_sucursal
    return distribucion_cantidad_estudios 

def generar_pacientes(sucursal: str, fecha: str = "2025-07-01") -> pd.DataFrame:
    """Genera los datos de pacientes para una sucursal específica."""
    config_data = load_distribution_data()
    if config_data is None:
        raise Exception("No se pudieron cargar los datos de configuración")
    
    # Filtrar datos por sucursal
    llegadas_suc = filtrar_por_sucursal(config_data['distribucion_llegada'], sucursal)
    dist_k_suc = filtrar_por_sucursal(config_data['distribucion_cantidad_estudios'], sucursal)
    prob_est_suc = filtrar_por_sucursal(config_data['probabilidad_estudios'], sucursal)

    # Calcular probabilidades para la distribución de cantidad de estudios
    dist_k_suc = calcular_probabilities(dist_k_suc)

    # Generar llegadas
    tiempos = generar_llegadas(llegadas_suc)

    # Generar pacientes
    pacientes = []
    for pid, t in enumerate(tiempos):
        k = sortear_k(dist_k_suc)
        estudios = sortear_estudios(prob_est_suc, k)
        pacientes.append({
            "PacienteID": pid,
            "LlegadaMin": t,
            "Sucursal": sucursal,
            "CantidadEstudios": k,
            "Estudios": estudios,
            "Fecha": fecha
        })

    return pd.DataFrame(pacientes)

# Diccionario de cabinas por sucursal
CABINAS_POR_SUCURSAL = {
    "COYOACAN": {
        "PAPANICOLAOU": 1,
        "NUTRICION": 2,
        "LABORATORIO": 13,
        "RAYOS X": 2,
        "TOMOGRAFIA": 1,
        "ULTRASONIDO": 7,
        "MASTOGRAFIA": 3,
        "OPTOMETRIA": 6,
        "RESONANCIA MAGNETICA": 1,
        "ELECTROCARDIOGRAMA": 2,
        "DENSITOMETRIA": 2
    },
    "CULIACAN": {
        "PAPANICOLAOU": 1,
        "NUTRICION": 4,
        "LABORATORIO": 7,
        "RAYOS X": 1,
        "TOMOGRAFIA": 1,
        "ULTRASONIDO": 6,
        "MASTOGRAFIA": 1,
        "OPTOMETRIA": 4,
        "RESONANCIA MAGNETICA": 1,
        "ELECTROCARDIOGRAMA": 1,
        "DENSITOMETRIA": 1
    },
    "CULIACAN CAÑADAS": {
        "PAPANICOLAOU": 1,
        "NUTRICION": 1,
        "LABORATORIO": 5,
        "RAYOS X": 1,
        "TOMOGRAFIA": 0,
        "ULTRASONIDO": 3,
        "MASTOGRAFIA": 1,
        "OPTOMETRIA": 2,
        "RESONANCIA MAGNETICA": 0,
        "ELECTROCARDIOGRAMA": 1,
        "DENSITOMETRIA": 1
    },
    "CULIACAN COLEGIO MILITAR": {
        "PAPANICOLAOU": 1,
        "NUTRICION": 0,
        "LABORATORIO": 4,
        "RAYOS X": 1,
        "TOMOGRAFIA": 1,
        "ULTRASONIDO": 3,
        "MASTOGRAFIA": 1,
        "OPTOMETRIA": 2,
        "RESONANCIA MAGNETICA": 1,
        "ELECTROCARDIOGRAMA": 1,
        "DENSITOMETRIA": 1
    },
    "CULIACAN LA CONQUISTA": {
        "PAPANICOLAOU": 1,
        "NUTRICION": 0,
        "LABORATORIO": 2,
        "RAYOS X": 1,
        "TOMOGRAFIA": 0,
        "ULTRASONIDO": 1,
        "MASTOGRAFIA": 0,
        "OPTOMETRIA": 1,
        "RESONANCIA MAGNETICA": 0,
        "ELECTROCARDIOGRAMA": 1,
        "DENSITOMETRIA": 0
    },
    "CULIACAN LAS TORRES": {
        "PAPANICOLAOU": 1,
        "NUTRICION": 2,
        "LABORATORIO": 4,
        "RAYOS X": 1,
        "TOMOGRAFIA": 0,
        "ULTRASONIDO": 2,
        "MASTOGRAFIA": 1,
        "OPTOMETRIA": 2,
        "RESONANCIA MAGNETICA": 0,
        "ELECTROCARDIOGRAMA": 1,
        "DENSITOMETRIA": 1
    },
    "CULIACAN NAKAYAMA": {
        "PAPANICOLAOU": 1,
        "NUTRICION": 0,
        "LABORATORIO": 3,
        "RAYOS X": 0,
        "TOMOGRAFIA": 0,
        "ULTRASONIDO": 1,
        "MASTOGRAFIA": 0,
        "OPTOMETRIA": 1,
        "RESONANCIA MAGNETICA": 0,
        "ELECTROCARDIOGRAMA": 1,
        "DENSITOMETRIA": 0
    },
    "CULIACAN UNIVERSITARIOS": {
        "PAPANICOLAOU": 1,
        "NUTRICION": 2,
        "LABORATORIO": 4,
        "RAYOS X": 1,
        "TOMOGRAFIA": 0,
        "ULTRASONIDO": 2,
        "MASTOGRAFIA": 1,
        "OPTOMETRIA": 2,
        "RESONANCIA MAGNETICA": 0,
        "ELECTROCARDIOGRAMA": 1,
        "DENSITOMETRIA": 1
    }
} 