// Inicialización de Socket.IO
const socket = io();

// Configuración del gráfico
let queueChart;
const ctx = document.getElementById('queueChart').getContext('2d');

// Colores para los estudios
const colors = [
    'rgb(75, 192, 192)',   // Turquesa
    'rgb(255, 99, 132)',   // Rosa
    'rgb(54, 162, 235)',   // Azul
    'rgb(255, 206, 86)',   // Amarillo
    'rgb(153, 102, 255)',  // Púrpura
    'rgb(255, 159, 64)',   // Naranja
    'rgb(199, 199, 199)',  // Gris
    'rgb(83, 102, 255)',   // Azul oscuro
    'rgb(40, 159, 64)',    // Verde
    'rgb(210, 199, 199)',  // Gris claro
    'rgb(78, 205, 196)'    // Verde azulado
];

// Datos iniciales para el gráfico
const initialData = {
    labels: [],
    datasets: []
};

// Configuración del gráfico
const config = {
    type: 'line',
    data: initialData,
    options: {
        responsive: true,
        animation: {
            duration: 0 // Disable animations for better performance
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Número de Personas en Cola'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Tiempo (minutos)'
                }
            }
        },
        plugins: {
            legend: {
                position: 'right',
                labels: {
                    boxWidth: 12
                }
            }
        }
    }
};

// Inicializar el gráfico
queueChart = new Chart(ctx, config);

// Elementos del DOM
const sucursalSelect = document.getElementById('sucursalSelect');
const startButton = document.getElementById('startSimulation');
const stopButton = document.getElementById('stopSimulation');
const queueStatsList = document.getElementById('queueStatsList');

// Manejar cambios en la selección de sucursal
sucursalSelect.addEventListener('change', () => {
    startButton.disabled = !sucursalSelect.value;
    stopButton.disabled = true;
});

// Manejo de eventos de los botones
startButton.addEventListener('click', () => {
    const sucursal = sucursalSelect.value;
    if (sucursal) {
        socket.emit('start_simulation', { sucursal });
        startButton.disabled = true;
        stopButton.disabled = false;
        sucursalSelect.disabled = true;
    }
});

stopButton.addEventListener('click', () => {
    socket.emit('stop_simulation');
    startButton.disabled = false;
    stopButton.disabled = true;
    sucursalSelect.disabled = false;
});

// Función para actualizar las estadísticas de cola
function updateQueueStats(queueLengths) {
    // Limpiar lista actual
    queueStatsList.innerHTML = '';
    
    // Crear elementos para cada modalidad
    Object.entries(queueLengths).forEach(([estudio, length]) => {
        const div = document.createElement('div');
        div.className = 'd-flex justify-content-between align-items-center mb-1';
        div.innerHTML = `
            <span class="badge" style="background-color: ${colors[queueChart.data.datasets.findIndex(d => d.label === estudio) % colors.length]}; color: black;">
                ${estudio}
            </span>
            <span>${length}</span>
        `;
        queueStatsList.appendChild(div);
    });
}

// Manejo de eventos del servidor
let updateTimeout = null;
socket.on('queue_update', (data) => {
    // Actualizar el gráfico
    queueChart.data.labels.push(data.time);
    
    // Si es la primera actualización, inicializar los datasets
    if (queueChart.data.datasets.length === 0) {
        const estudios = Object.keys(data.queue_lengths);
        estudios.forEach((estudio, index) => {
            queueChart.data.datasets.push({
                label: estudio,
                data: [],
                borderColor: colors[index % colors.length],
                tension: 0.1
            });
        });
    }
    
    // Actualizar datos para cada estudio
    Object.entries(data.queue_lengths).forEach(([estudio, length], index) => {
        queueChart.data.datasets[index].data.push(length);
    });
    
    // Mantener solo los últimos 60 puntos (1 hora de simulación)
    if (queueChart.data.labels.length > 60) {
        queueChart.data.labels.shift();
        queueChart.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }
    
    // Debounce chart updates to prevent performance issues
    if (updateTimeout) {
        clearTimeout(updateTimeout);
    }
    updateTimeout = setTimeout(() => {
        queueChart.update('none'); // Use 'none' mode for faster updates
    }, 100); // Update every 100ms at most
    
    // Actualizar estadísticas
    document.getElementById('simulatedTime').textContent = data.time;
    document.getElementById('totalQueueCount').textContent = 
        Object.values(data.queue_lengths).reduce((a, b) => a + b, 0);
    
    // Actualizar estadísticas por modalidad
    updateQueueStats(data.queue_lengths);
});

// Manejo de conexión/desconexión
socket.on('connect', () => {
    console.log('Conectado al servidor');
});

socket.on('disconnect', () => {
    console.log('Desconectado del servidor');
    startButton.disabled = false;
    stopButton.disabled = true;
    sucursalSelect.disabled = false;
}); 