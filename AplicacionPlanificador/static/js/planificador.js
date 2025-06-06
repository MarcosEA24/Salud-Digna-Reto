let medias = {};
let filas = {};
let estudiosSeleccionados = [];

const sucursalSelect = document.getElementById('sucursalSelect');
const mediaSucursalDiv = document.getElementById('mediaSucursal');
const rutaGeneradaDiv = document.getElementById('rutaGenerada');
const generarRutaBtn = document.getElementById('generarRutaBtn');
const refrescarFilasBtn = document.getElementById('refrescarFilasBtn');
const barChartCanvas = document.getElementById('barChart');

// Obtener estudios
const estudiosCheckboxes = Array.from(document.querySelectorAll('.form-check-input'));

// Inicializar gráfico de barras
let barChart;

function actualizarGrafico() {
    const labels = Object.keys(filas);
    const data = Object.values(filas);
    if (!barChart) {
        barChart = new Chart(barChartCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Personas en fila',
                    data: data,
                    backgroundColor: 'rgba(54, 162, 235, 0.7)'
                }]
            },
            options: {
                indexAxis: 'y',
                scales: {
                    x: { beginAtZero: true }
                }
            }
        });
    } else {
        barChart.data.labels = labels;
        barChart.data.datasets[0].data = data;
        barChart.update();
    }
}

function cargarMediasSucursal(sucursal) {
    if (!sucursal) {
        mediaSucursalDiv.textContent = '';
        return;
    }
    fetch(`/get_medias?sucursal=${encodeURIComponent(sucursal)}`)
        .then(res => res.json())
        .then(data => {
            if (data.media) {
                mediaSucursalDiv.innerHTML = `<strong>Media de atención:</strong> ${data.media} minutos`;
            } else {
                mediaSucursalDiv.textContent = '';
            }
        });
}

function cargarFilasRandom() {
    fetch('/get_random_queues')
        .then(res => res.json())
        .then(data => {
            filas = data;
            actualizarGrafico();
        });
}

sucursalSelect.addEventListener('change', (e) => {
    cargarMediasSucursal(e.target.value);
});

refrescarFilasBtn.addEventListener('click', () => {
    cargarFilasRandom();
});

generarRutaBtn.addEventListener('click', () => {
    const sucursal = sucursalSelect.value;
    estudiosSeleccionados = estudiosCheckboxes.filter(cb => cb.checked).map(cb => cb.value);
    if (!sucursal || estudiosSeleccionados.length === 0) {
        rutaGeneradaDiv.classList.remove('alert-success');
        rutaGeneradaDiv.classList.add('alert-danger');
        rutaGeneradaDiv.textContent = 'Selecciona una sucursal y al menos un estudio.';
        rutaGeneradaDiv.classList.remove('d-none');
        return;
    }
    fetch('/generar_ruta', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sucursal: sucursal,
            estudios: estudiosSeleccionados,
            filas: filas
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.ruta) {
            rutaGeneradaDiv.classList.remove('alert-danger');
            rutaGeneradaDiv.classList.add('alert-success');
            let detalleHtml = `<strong>Ruta generada:</strong> ${data.ruta.join(' → ')}<br>`;
            detalleHtml += `<strong>Tiempo estimado total:</strong> ${data.tiempo_estimado_total.toFixed(2)} minutos<br><br>`;
            detalleHtml += `<table class='table table-sm'><thead><tr><th>Estudio</th><th>Espera (min)</th><th>Atención (min)</th><th>Total (min)</th></tr></thead><tbody>`;
            data.detalle.forEach(d => {
                detalleHtml += `<tr><td>${d.estudio}</td><td>${d.espera.toFixed(2)}</td><td>${d.tap.toFixed(2)}</td><td>${d.total.toFixed(2)}</td></tr>`;
            });
            detalleHtml += `</tbody></table>`;
            rutaGeneradaDiv.innerHTML = detalleHtml;
            rutaGeneradaDiv.classList.remove('d-none');
        } else {
            rutaGeneradaDiv.classList.remove('alert-success');
            rutaGeneradaDiv.classList.add('alert-danger');
            rutaGeneradaDiv.textContent = 'No se pudo generar la ruta.';
            rutaGeneradaDiv.classList.remove('d-none');
        }
    });
});

// Inicialización
window.onload = () => {
    cargarFilasRandom();
}; 