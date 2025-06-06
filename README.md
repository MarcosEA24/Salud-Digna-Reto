# Salud-Digna-Reto
Este es un repositorio para el socio formador "Salud Digna" con todo el desarrollo del proyecto realizado por el equipo 5 de la generación 2021-2025 de la carrera de Ingeniería en Ciencias de Datos y Matemáticas del Tec de Monterrey

Este proyecto implementa un sistema completo para la simulación y planificación de servicios médicos, incluyendo análisis de datos, simulación de colas y una aplicación de planificación.

## Estructura del Proyecto

### Notebooks de Análisis y Procesamiento
- `DataPreprocessingTiempos.ipynb`: Procesamiento y análisis de datos de tiempos de servicio de las modalidades
- `DataPreprocessingTurnos.ipynb`: Procesamiento y análisis de datos de turnos
- `ParámetrosSimulacion.ipynb`: Análisis y definición de parámetros para la simulación
- `construcción_simulación.ipynb`: Implementación de la simulación del sistema

### Aplicaciones
- `AplicacionColas/`: Aplicación para simulación y análisis de colas
- `AplicacionPlanificador/`: Aplicación para planificación de servicios (Ejemplo de posible implementación)

### Datos
#### Archivos CSV
- `distribucion_cantidad_estudios.csv`: Distribución de la cantidad de estudios por pacienten por sucursal
- `promedio_estudios.csv`: Probabilidad de cada estudio por cada sucursal
- `distribucion_llegada.csv`: Distribución de llegadas de pacientes por sucursal

#### Archivos Excel
- `Tiempos Pacientes.xlsx`: Datos detallados de tiempos de servicio
- `Tiempos Pacientes Limpios.xlsx`: Datos procesados de tiempos de servicio
- `Turnos Pacientes.xlsx`: Datos de turnos de pacientes
- `Turnos Pacientes Limpios.xlsx`: Datos procesados de turnos
- `medias_por_sucursal.xlsx`: Medias de tiempos en caja de espera atención por sucursal
- `medias_por_estudio_sucursal.xlsx`: Medias de tiempos de espera y atención por estudio y sucursal

## Requisitos

Para ejecutar este proyecto, necesitarás:

- Python 3.8 o superior
- Jupyter Notebook
- Bibliotecas principales:
  - pandas, numpy, matplotlib, scipy (análisis de datos)
  - flask y sus extensiones (para las aplicaciones)
  - openpyxl (para manejo de archivos Excel)

## Instalación

1. Clona este repositorio
2. Crea un entorno virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Análisis de Datos
1. Ejecuta los notebooks en el siguiente orden:
   - `DataPreprocessingTiempos.ipynb`
   - `DataPreprocessingTurnos.ipynb`
   - `ParámetrosSimulacion.ipynb`
   - `construcción_simulación.ipynb`

### Aplicaciones Web
1. Para la aplicación de colas:
```bash
cd AplicacionColas
python app.py
```

2. Para la aplicación de planificación:
```bash
cd AplicacionPlanificador
python app.py
```
## Características Principales

- Análisis detallado de tiempos de servicio
- Simulación de colas para optimización de recursos
- Planificación de rutas de servicios
- Visualización de datos y resultados
- Interfaz de usuario intuitiva para ambas aplicaciones
- Interfaz web responsive

## Estructura de las Aplicaciones Web

### AplicacionColas
- Frontend: HTML, CSS, JavaScript
- Backend: Flask
- Base de datos: archicos .csv y .xlsx (Pruebas)
- Características:
  - Simulación en tiempo real
  - Visualización del estado de las colas

### AplicacionPlanificador
- Frontend: HTML, CSS, JavaScript
- Backend: Flask
- Base de datos: archicos .csv y .xlsx (Pruebas)
- Características:
  - Planificación de rutas
  - Tiempos estimados de espera
  - Tiempos estimados de atención
 
