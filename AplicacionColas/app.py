import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from simulation import QueueSimulation
from config import SUCURSALES

# Inicialización de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Crear instancia de la simulación
simulation = QueueSimulation(socketio)

# Rutas principales
@app.route('/')
def index():
    return render_template('index.html', sucursales=SUCURSALES)

@app.route('/get_agenda')
def get_agenda():
    agenda = simulation.get_agenda()
    if agenda is None:
        return jsonify({'error': 'No hay agenda disponible'}), 404
    return jsonify(agenda.to_dict(orient='records'))

# Manejo de eventos WebSocket
@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')

@socketio.on('start_simulation')
def handle_start_simulation(data):
    sucursal = data.get('sucursal')
    if not sucursal:
        print('❌ Error: No se especificó una sucursal')
        return
    
    print(f'✅ Iniciando simulación para la sucursal: {sucursal}')
    simulation.start(sucursal)

@socketio.on('stop_simulation')
def handle_stop_simulation():
    print('Deteniendo simulación')
    simulation.stop()

if __name__ == '__main__':
    socketio.run(app, debug=True) 