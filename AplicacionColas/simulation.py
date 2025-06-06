import time
from threading import Thread, Event
import random
from config import load_distribution_data, CABINAS_POR_SUCURSAL, calcular_probabilities, generar_pacientes
from route_optimizer import RouteOptimizer

class QueueSimulation:
    def __init__(self, socketio):
        self.socketio = socketio
        self.running = False
        self.stop_event = Event()
        self.simulation_thread = None
        self.current_time = 0
        self.queue_lengths = {}
        self.pacientes = None
        self.sucursal = None
        self.optimizer = None
        self.agenda = None  # Para almacenar el DataFrame de la agenda
        self.simulation_speed = 0.15  # 0.3 segundos reales = 1 minuto simulado
        
        # Cargar datos de configuración
        self.config_data = load_distribution_data()
        if self.config_data is None:
            raise Exception("No se pudieron cargar los datos de configuración")

    def start(self, sucursal):
        if not self.running:
            print(f"Generando datos para la sucursal: {sucursal}")
            try:
                # Generar datos de pacientes
                self.pacientes = generar_pacientes(sucursal)
                print(f"✅ Datos generados exitosamente: {len(self.pacientes)} pacientes")
                
                # Inicializar optimizador y planificar rutas
                self.optimizer = RouteOptimizer()
                self.agenda, self.queue_lengths = self.optimizer.planificar_dia(
                    self.pacientes,
                    CABINAS_POR_SUCURSAL,
                    self.config_data['media_tiempo_atencion']
                )
                print("✅ Rutas optimizadas y planificadas")
                print(f"✅ Agenda generada con {len(self.agenda)} registros")
                
                self.sucursal = sucursal
                self.running = True
                self.stop_event.clear()
                self.simulation_thread = Thread(target=self._run_simulation)
                self.simulation_thread.start()
            except Exception as e:
                print(f"❌ Error al generar datos: {str(e)}")
                self.running = False

    def stop(self):
        if self.running:
            self.running = False
            self.stop_event.set()
            if self.simulation_thread:
                self.simulation_thread.join()
            self.pacientes = None
            self.sucursal = None
            self.optimizer = None
            self.queue_lengths = {}
            # No limpiamos self.agenda para mantener los resultados

    def get_agenda(self):
        """Retorna el DataFrame de la agenda si está disponible."""
        return self.agenda

    def _run_simulation(self):
        while not self.stop_event.is_set():
            # Simular un minuto
            self.current_time += 1
            
            # Enviar actualización de colas por estudio
            self.socketio.emit('queue_update', {
                'time': self.current_time,
                'queue_lengths': {
                    estudio: self.queue_lengths[estudio][min(self.current_time, len(self.queue_lengths[estudio])-1)]
                    for estudio in self.queue_lengths
                }
            })
            
            # Esperar 0.3 segundos reales (equivalente a 1 minuto simulado)
            time.sleep(self.simulation_speed) 