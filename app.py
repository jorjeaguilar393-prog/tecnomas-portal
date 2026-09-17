from datetime import datetime
from flask import Flask, redirect, render_template_string, request, session, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'tecnomas_clave_secreta_taller'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tecnomas_taller.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Orden(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    equipo = db.Column(db.String(120), nullable=False)
    falla = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(50), default='Pendiente')
    notas = db.Column(db.Text, default='')
    costo_repuestos = db.Column(db.Float, default=0.0)
    mano_obra = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    estado_pago = db.Column(db.String(20), default='Pendiente')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

ESTADOS_PERMITIDOS = [
    'Pendiente',
    'En diagnóstico',
    'Esperando repuesto',
    'En reparación',
    'Listo para entregar',
    'Entregado'
]

# Credenciales de Administrador
ADMIN_USER = "admin"
ADMIN_PASS = "tecnomas2026"

HTML_HEADER_CLIENTE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tecnomás - Portal de Clientes</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark shadow-sm mb-4">
        <div class="container px-4">
            <a class="navbar-brand fw-bold" href="/"><i class="bi bi-tools text-warning"></i> Tecnomás <span class="text-muted fs-6">| Portal de Clientes</span></a>
            <a href="/login" class="btn btn-outline-warning btn-sm"><i class="bi bi-lock-fill"></i> Acceso Técnico</a>
        </div>
    </nav>
    <div class="container px-4">
"""

HTML_FOOTER = """
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# 1. PORTAL PÚBLICO: REGISTRO Y CONSULTA PARA CLIENTES (ACTUALIZADO)
TEMPLATE_CLIENTE = HTML_HEADER_CLIENTE + """
<div class="row justify-content-center mt-4">
    <div class="col-lg-10">
        <div class="text-center mb-4">
            <h1 class="fw-bold text-dark">Bienvenido a Tecnomás</h1>
            <p class="text-muted">Registra tu dispositivo para reparación o consulta el estado de tu orden actual.</p>
        </div>

        <div class="row g-4">
            <!-- FORMULARIO DE REGISTRO PARA EL CLIENTE -->
            <div class="col-md-6">
                <div class="card shadow-sm border-0 h-100">
                    <div class="card-body p-4">
                        <h4 class="fw-bold text-primary mb-3"><i class="bi bi-plus-circle-fill"></i> Registrar mi Dispositivo</h4>
                        <form method="POST" action="/registrar_cliente">
                            <div class="mb-3">
                                <label class="form-label fw-semibold">Nombre Completo</label>
                                <input type="text" class="form-control" name="cliente" required placeholder="Tu nombre">
                            </div>
                            <div class="mb-3">
                                <label class="form-label fw-semibold">Teléfono / WhatsApp</label>
                                <input type="text" class="form-control" name="telefono" required placeholder="Ej. 89649798">
                            </div>
                            <div class="mb-3">
                                <label class="form-label fw-semibold">Equipo / Modelo</label>
                                <input type="text" class="form-control" name="equipo" required placeholder="Ej. Samsung A51, Laptop Dell...">
                            </div>
                            <div class="mb-3">
                                <label class="form-label fw-semibold">Falla o Servicio Solicitado</label>
                                <textarea class="form-control" name="falla" rows="3" required placeholder="¿Qué problema presenta?"></textarea>
                            </div>
                            <button type="submit" class="btn btn-success w-100 fw-bold"><i class="bi bi-send-fill"></i> Registrar Equipo</button>
                        </form>
                    </div>
                </div>
            </div>

            <!-- FORMULARIO DE CONSULTA PARA EL CLIENTE -->
            <div class="col-md-6">
                <div class="card shadow-sm border-0 h-100">
                    <div class="card-body p-4">
                        <h4 class="fw-bold text-secondary mb-3"><i class="bi bi-search"></i> Consultar mi Orden</h4>
                        <p class="text-muted small">Introduce tu número de teléfono para verificar el avance de tu dispositivo.</p>
                        <form method="GET" action="/" class="mb-4">
                            <div class="input-group">
                                <input type="text" class="form-control" name="telefono" value="{{ telefono_buscado }}" required placeholder="Número de teléfono...">
                                <button type="submit" class="btn btn-primary fw-bold"><i class="bi bi-search"></i> Buscar</button>
                            </div>
                        </form>

                        {% if telefono_buscado %}
                            <hr>
                            <h5 class="fw-bold text-secondary mb-3">Resultados para: {{ telefono_buscado }}</h5>
                            {% if ordenes %}
                                {% for orden in ordenes %}
                                <div class="card bg-light border-0 mb-3 shadow-sm">
                                    <div class="card-body">
                                        <div class="d-flex justify-content-between align-items-center mb-2">
                                            <span class="badge bg-dark">Orden #{{ orden.id }}</span>
                                            <span class="text-muted small"><i class="bi bi-calendar"></i> {{ orden.fecha.strftime('%d/%m/%Y %H:%M') }}</span>
                                        </div>
                                        <h6 class="fw-bold text-primary mb-1">{{ orden.equipo }}</h6>
                                        <p class="mb-2 small"><strong>Falla:</strong> {{ orden.falla }}</p>
                                        
                                        <div class="d-flex justify-content-between align-items-center mt-2">
                                            <span class="badge {% if orden.estado == 'Listo para entregar' %}bg-success{% elif orden.estado == 'Entregado' %}bg-secondary{% else %}bg-warning text-dark{% endif %}">
                                                {{ orden.estado }}
                                            </span>
                                            <span class="fw-bold text-dark">Total: L. {{ "%.2f"|format(orden.total) }}</span>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            {% else %}
                                <div class="alert alert-warning text-center small" role="alert">
                                    No se encontró ningún equipo registrado con el número <strong>{{ telefono_buscado }}</strong>.
                                </div>
                            {% endif %}
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
""" + HTML_FOOTER

# 2. PANTALLA DE LOGIN TIPO ROUTER
TEMPLATE_LOGIN = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Tecnomás - Acceso Restringido</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
</head>
<body class="bg-dark d-flex align-items-center justify-content-center" style="height: 100vh;">
    <div class="card shadow-lg border-0 p-4" style="width: 100%; max-width: 400px;">
        <div class="text-center mb-4">
            <i class="bi bi-shield-lock-fill text-warning fs-1"></i>
            <h3 class="fw-bold mt-2">Acceso Técnico</h3>
            <p class="text-muted small">Tecnomás - Panel de Administración</p>
        </div>

        {% if error %}
        <div class="alert alert-danger py-2 text-center" role="alert">
            <small>{{ error }}</small>
        </div>
        {% endif %}

        <form method="POST" action="/login">
            <div class="mb-3">
                <label class="form-label fw-semibold">Usuario</label>
                <input type="text" class="form-control" name="usuario" required autofocus placeholder="Usuario admin">
            </div>
            <div class="mb-3">
                <label class="form-label fw-semibold">Contraseña</label>
                <input type="password" class="form-control" name="password" required placeholder="Contraseña">
            </div>
            <button type="submit" class="btn btn-warning w-100 fw-bold py-2 mb-2"><i class="bi bi-box-arrow-in-right"></i> Ingresar al Sistema</button>
            <a href="/" class="btn btn-outline-secondary w-100 btn-sm"><i class="bi bi-arrow-left"></i> Regresar al Portal Público</a>
        </form>
    </div>
</body>
</html>
"""

# 3. PANEL PRIVADO DE ADMINISTRACIÓN
TEMPLATE_ADMIN = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tecnomás - Panel de Administración</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <style>
        @media print {
            .no-print { display: none !important; }
            body { background: white !important; }
        }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark shadow-sm mb-4">
        <div class="container-fluid px-4">
            <a class="navbar-brand fw-bold" href="/admin"><i class="bi bi-tools text-warning"></i> Tecnomás <span class="text-muted fs-6">| Panel de Técnico</span></a>
            <div class="d-flex gap-2">
                <a href="/" class="btn btn-outline-light btn-sm" target="_blank"><i class="bi bi-eye"></i> Ver Portal Público</a>
                <a href="/logout" class="btn btn-danger btn-sm"><i class="bi bi-power"></i> Cerrar Sesión</a>
            </div>
        </div>
    </nav>
    <div class="container-fluid px-4">
    
    <!-- Estadísticas -->
    <div class="row g-3 mb-4">
        <div class="col-md-3">
            <div class="card border-0 shadow-sm bg-primary text-white">
                <div class="card-body">
                    <h6 class="text-uppercase fw-semibold">Órdenes Totales</h6>
                    <h3 class="fw-bold mb-0">{{ total_ordenes }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-0 shadow-sm bg-warning text-dark">
                <div class="card-body">
                    <h6 class="text-uppercase fw-semibold">En Proceso / Reparación</h6>
                    <h3 class="fw-bold mb-0">{{ en_proceso }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-0 shadow-sm bg-success text-white">
                <div class="card-body">
                    <h6 class="text-uppercase fw-semibold">Listos para Entregar</h6>
                    <h3 class="fw-bold mb-0">{{ listos }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-0 shadow-sm bg-dark text-white">
                <div class="card-body">
                    <h6 class="text-uppercase fw-semibold">Ingresos Totales (Cobrado)</h6>
                    <h3 class="fw-bold mb-0">L. {{ "%.2f"|format(ingresos_totales) }}</h3>
                </div>
            </div>
        </div>
    </div>

    <div class="row g-4">
        <!-- Formulario Nueva Orden Admin -->
        <div class="col-lg-4">
            <div class="card shadow-sm border-0">
                <div class="card-body">
                    <h4 class="card-title fw-bold text-primary mb-3"><i class="bi bi-plus-circle"></i> Nueva Orden (Interna)</h4>
                    <form method="POST" action="/admin/agregar">
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Cliente</label>
                            <input type="text" class="form-control" name="cliente" required placeholder="Nombre completo">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Teléfono</label>
                            <input type="text" class="form-control" name="telefono" required placeholder="Ej. 99000000">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Equipo / Modelo</label>
                            <input type="text" class="form-control" name="equipo" required placeholder="Ej. Laptop Dell Latitude / Honor X5c">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-semibold">Falla reportada</label>
                            <textarea class="form-control" name="falla" rows="3" required placeholder="Descripción del problema..."></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary w-100 fw-bold py-2"><i class="bi bi-save"></i> Registrar Orden</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- Listado y Filtros Admin -->
        <div class="col-lg-8">
            <div class="card shadow-sm border-0">
                <div class="card-body">
                    <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
                        <h4 class="card-title fw-bold text-secondary m-0"><i class="bi bi-list-check"></i> Gestión de Órdenes</h4>
                        <form method="GET" action="/admin" class="d-flex gap-2">
                            <input type="text" class="form-control form-control-sm" name="q" value="{{ busqueda }}" placeholder="Buscar cliente o equipo...">
                            <button class="btn btn-outline-secondary btn-sm" type="submit"><i class="bi bi-search"></i></button>
                        </form>
                    </div>

                    <div class="d-flex flex-wrap gap-1 mb-3">
                        <a href="/admin" class="btn btn-sm {% if not filtro %}btn-dark{% else %}btn-outline-dark{% endif %}">Todas</a>
                        <a href="/admin?filtro=Pendiente" class="btn btn-sm {% if filtro == 'Pendiente' %}btn-primary{% else %}btn-outline-primary{% endif %}">Pendientes</a>
                        <a href="/admin?filtro=En reparación" class="btn btn-sm {% if filtro == 'En reparación' %}btn-warning text-dark{% else %}btn-outline-warning text-dark{% endif %}">En Reparación</a>
                        <a href="/admin?filtro=Listo para entregar" class="btn btn-sm {% if filtro == 'Listo para entregar' %}btn-success{% else %}btn-outline-success{% endif %}">Listos</a>
                        <a href="/admin?filtro=Entregado" class="btn btn-sm {% if filtro == 'Entregado' %}btn-secondary{% else %}btn-outline-secondary{% endif %}">Entregados</a>
                    </div>

                    <div class="table-responsive">
                        <table class="table table-hover align-middle">
                            <thead class="table-dark">
                                <tr>
                                    <th>#</th>
                                    <th>Cliente / Tel.</th>
                                    <th>Equipo</th>
                                    <th>Total / Pago</th>
                                    <th>Estado / Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for orden in ordenes %}
                                <tr>
                                    <td class="fw-bold">#{{ orden.id }}</td>
                                    <td>
                                        <div class="fw-bold">{{ orden.cliente }}</div>
                                        <small class="text-muted"><i class="bi bi-telephone"></i> {{ orden.telefono }}</small>
                                    </td>
                                    <td>
                                        <div>{{ orden.equipo }}</div>
                                        <small class="text-truncate d-inline-block text-muted" style="max-width: 130px;">{{ orden.falla }}</small>
                                    </td>
                                    <td>
                                        <div class="fw-bold text-success">L. {{ "%.2f"|format(orden.total) }}</div>
                                        {% if orden.estado_pago == 'Pagado' %}
                                        <span class="badge bg-success">Pagado</span>
                                        {% else %}
                                        <span class="badge bg-danger">Pendiente</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <form method="POST" action="/admin/actualizar/{{ orden.id }}" class="d-flex flex-column gap-1">
                                            <div class="input-group input-group-sm">
                                                <select name="estado" class="form-select form-select-sm">
                                                    {% for est in estados %}
                                                    <option value="{{ est }}" {% if orden.estado == est %}selected{% endif %}>{{ est }}</option>
                                                    {% endfor %}
                                                </select>
                                                <button class="btn btn-dark btn-sm" type="submit" title="Actualizar Estado"><i class="bi bi-check-lg"></i></button>
                                            </div>
                                            <div class="d-flex gap-1 mt-1">
                                                <a href="/admin/orden/{{ orden.id }}" class="btn btn-outline-primary btn-sm flex-fill" title="Cobros y Notas"><i class="bi bi-cash-coin"></i> Cobros</a>
                                                <a href="https://wa.me/504{{ orden.telefono }}?text=Hola%20*{{ orden.cliente }}*,%20le%20escribimos%20de%20*Tecnomás*%20para%20informarle%20que%20su%20equipo%20(*{{ orden.equipo }}*)%20se%20encuentra%20en%20estado:%20*{{ orden.estado }}*.%20Total%20a%20pagar:%20L.%20{{ '%.2f'|format(orden.total) }}." target="_blank" class="btn btn-success btn-sm" title="Enviar WhatsApp"><i class="bi bi-whatsapp"></i></a>
                                                <a href="/admin/orden/{{ orden.id }}/ticket" target="_blank" class="btn btn-outline-secondary btn-sm" title="Imprimir Ticket"><i class="bi bi-printer"></i></a>
                                            </div>
                                        </form>
                                    </td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="5" class="text-center text-muted py-4">No se encontraron órdenes registradas.</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

TEMPLATE_DETALLE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Orden #{{ orden.id }} - Presupuesto</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
</head>
<body class="bg-light py-4">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card shadow-sm border-0 mb-4">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <h3 class="fw-bold text-primary m-0">Orden #{{ orden.id }} - Presupuesto y Notas</h3>
                            <a href="/admin" class="btn btn-outline-secondary btn-sm"><i class="bi bi-arrow-left"></i> Volver al Panel</a>
                        </div>

                        <div class="row mb-3">
                            <div class="col-md-6">
                                <p class="mb-1"><strong>Cliente:</strong> {{ orden.cliente }}</p>
                                <p class="mb-1"><strong>Teléfono:</strong> {{ orden.telefono }}</p>
                            </div>
                            <div class="col-md-6">
                                <p class="mb-1"><strong>Equipo:</strong> {{ orden.equipo }}</p>
                                <p class="mb-1"><strong>Fecha de Ingreso:</strong> {{ orden.fecha.strftime('%d/%m/%Y %H:%M') }}</p>
                            </div>
                        </div>

                        <div class="mb-3">
                            <label class="form-label fw-semibold text-danger">Falla Reportada Inicial:</label>
                            <div class="p-3 bg-light rounded border">{{ orden.falla }}</div>
                        </div>

                        <form method="POST" action="/admin/orden/{{ orden.id }}">
                            <div class="row">
                                <div class="col-md-4 mb-3">
                                    <label class="form-label fw-semibold">Costo Repuestos (L.)</label>
                                    <input type="number" step="0.01" class="form-control" name="costo_repuestos" value="{{ orden.costo_repuestos }}">
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label class="form-label fw-semibold">Mano de Obra (L.)</label>
                                    <input type="number" step="0.01" class="form-control" name="mano_obra" value="{{ orden.mano_obra }}">
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label class="form-label fw-semibold">Estado de Pago</label>
                                    <select name="estado_pago" class="form-select">
                                        <option value="Pendiente" {% if orden.estado_pago == 'Pendiente' %}selected{% endif %}>Pendiente</option>
                                        <option value="Pagado" {% if orden.estado_pago == 'Pagado' %}selected{% endif %}>Pagado</option>
                                    </select>
                                </div>
                            </div>

                            <div class="mb-3">
                                <label class="form-label fw-semibold">Notas Técnicas / Repuestos Utilizados:</label>
                                <textarea class="form-control" name="notas" rows="4" placeholder="Detalles de la reparación...">{{ orden.notas }}</textarea>
                            </div>

                            <div class="d-flex justify-content-end gap-2">
                                <button type="submit" class="btn btn-primary fw-bold px-4"><i class="bi bi-save"></i> Guardar Presupuesto y Notas</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

TEMPLATE_TICKET = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Comprobante de Recepción - Tecnomás #{{ orden.id }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #fff; color: #000; font-family: monospace; font-size: 14px; }
        .ticket-container { max-width: 400px; margin: 20px auto; padding: 20px; border: 1px dashed #000; }
        @media print {
            .no-print { display: none !important; }
            .ticket-container { border: none; margin: 0; padding: 0; width: 100%; }
        }
    </style>
</head>
<body onload="window.print()">
    <div class="ticket-container">
        <div class="text-center mb-3">
            <h3 class="fw-bold m-0">TECNOMÁS</h3>
            <small>Servicio Técnico en Electrónica y Computación</small><br>
            <small>Copal Abajo, Choluteca, Honduras</small>
            <hr>
            <h5 class="fw-bold m-0">ORDEN DE SERVICIO #{{ orden.id }}</h5>
            <small>{{ orden.fecha.strftime('%d/%m/%Y %H:%M') }}</small>
        </div>

        <div class="mb-2">
            <strong>Cliente:</strong> {{ orden.cliente }}<br>
            <strong>Teléfono:</strong> {{ orden.telefono }}<br>
            <strong>Equipo:</strong> {{ orden.equipo }}
        </div>

        <div class="mb-2">
            <strong>Falla Reportada:</strong>
            <div class="p-1 border bg-light">{{ orden.falla }}</div>
        </div>

        <div class="mb-2">
            <strong>Estado Actual:</strong> {{ orden.estado }}
        </div>

        <div class="border-top border-bottom py-2 my-2">
            <div class="d-flex justify-content-between"><span>Repuestos:</span> <span>L. {{ "%.2f"|format(orden.costo_repuestos) }}</span></div>
            <div class="d-flex justify-content-between"><span>Mano de Obra:</span> <span>L. {{ "%.2f"|format(orden.mano_obra) }}</span></div>
            <div class="d-flex justify-content-between fw-bold mt-1"><span>TOTAL A PAGAR:</span> <span>L. {{ "%.2f"|format(orden.total) }}</span></div>
            <div class="text-center mt-1"><small><strong>Pago:</strong> {{ orden.estado_pago }}</small></div>
        </div>

        <div class="text-center pt-2" style="font-size: 11px;">
            <p class="mb-1"><strong>Políticas de Garantía:</strong></p>
            <p class="mb-1">1. No nos hacemos responsables por equipos sin retirar después de 30 días.<br>
            2. Presentar este ticket para retirar su equipo.<br>
            3. Garantía válida solo en la reparación indicada.</p>
            <br>
            <p class="m-0">¡Gracias por confiar en Tecnomás!</p>
        </div>
    </div>
    <div class="text-center mt-3 no-print">
        <button onclick="window.print()" class="btn btn-dark btn-sm">Imprimir Nuevamente</button>
        <a href="/admin" class="btn btn-outline-secondary btn-sm">Regresar al Panel</a>
    </div>
</body>
</html>
"""

# RUTAS DE LA APLICACIÓN Y SEGURIDAD

@app.route('/')
def portal_cliente():
    telefono_buscado = request.args.get('telefono', '').strip()
    ordenes = []
    if telefono_buscado:
        ordenes = Orden.query.filter_by(telefono=telefono_buscado).all()
    
    return render_template_string(TEMPLATE_CLIENTE, ordenes=ordenes, telefono_buscado=telefono_buscado)

# NUEVA RUTA: Recibe los datos cuando el cliente registra su equipo
@app.route('/registrar_cliente', methods=['POST'])
def registrar_cliente():
    cliente = request.form.get('cliente', '').strip()
    telefono = request.form.get('telefono', '').strip()
    equipo = request.form.get('equipo', '').strip()
    falla = request.form.get('falla', '').strip()
    
    if cliente and telefono and equipo and falla:
        nueva_orden = Orden(
            cliente=cliente,
            telefono=telefono,
            equipo=equipo,
            falla=falla,
            estado='Pendiente',
            costo_repuestos=0.0,
            mano_obra=0.0,
            total=0.0,
            estado_pago='Pendiente'
        )
        db.session.add(nueva_orden)
        db.session.commit()
        # Redirige de nuevo a la pantalla principal mostrando su orden recién creada
        return redirect(url_for('portal_cliente', telefono=telefono))
        
    return redirect(url_for('portal_cliente'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        if usuario == ADMIN_USER and password == ADMIN_PASS:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = "Usuario o contraseña incorrectos."
    return render_template_string(TEMPLATE_LOGIN, error=error)

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    busqueda = request.args.get('q', '')
    filtro = request.args.get('filtro', '')

    query = Orden.query
    if busqueda:
        query = query.filter(
            (Orden.cliente.contains(busqueda)) | 
            (Orden.equipo.contains(busqueda)) |
            (Orden.telefono.contains(busqueda))
        )
    if filtro:
        query = query.filter(Orden.estado == filtro)
    
    ordenes = query.order_by(Orden.id.desc()).all()
    
    total_ordenes = Orden.query.count()
    en_proceso = Orden.query.filter(Orden.estado.in_(['En diagnóstico', 'Esperando repuesto', 'En reparación'])).count()
    listos = Orden.query.filter(Orden.estado == 'Listo para entregar').count()
    
    ordenes_pagadas = Orden.query.filter_by(estado_pago='Pagado').all()
    ingresos_totales = sum(o.total for o in ordenes_pagadas)

    return render_template_string(
        TEMPLATE_ADMIN, 
        ordenes=ordenes, 
        estados=ESTADOS_PERMITIDOS, 
        busqueda=busqueda, 
        filtro=filtro,
        total_ordenes=total_ordenes,
        en_proceso=en_proceso,
        listos=listos,
        ingresos_totales=ingresos_totales
    )

@app.route('/admin/agregar', methods=['POST'])
def agregar():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    nueva_orden = Orden(
        cliente=request.form['cliente'],
        telefono=request.form['telefono'],
        equipo=request.form['equipo'],
        falla=request.form['falla'],
        estado='Pendiente',
        costo_repuestos=0.0,
        mano_obra=0.0,
        total=0.0,
        estado_pago='Pendiente'
    )
    db.session.add(nueva_orden)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/actualizar/<int:id>', methods=['POST'])
def actualizar(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    orden = Orden.query.get_or_404(id)
    nuevo_estado = request.form.get('estado')
    if nuevo_estado in ESTADOS_PERMITIDOS:
        orden.estado = nuevo_estado
        db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/orden/<int:id>', methods=['GET', 'POST'])
def detalle_orden(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    orden = Orden.query.get_or_404(id)
    if request.method == 'POST':
        try:
            repuestos = float(request.form.get('costo_repuestos', 0))
        except ValueError:
            repuestos = 0.0
            
        try:
            mano = float(request.form.get('mano_obra', 0))
        except ValueError:
            mano = 0.0

        orden.costo_repuestos = repuestos
        orden.mano_obra = mano
        orden.total = repuestos + mano
        orden.estado_pago = request.form.get('estado_pago', 'Pendiente')
        orden.notas = request.form.get('notas', '')
        db.session.commit()
        return redirect(url_for('detalle_orden', id=orden.id))
    return render_template_string(TEMPLATE_DETALLE, orden=orden)

@app.route('/admin/orden/<int:id>/ticket')
def ver_ticket(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    orden = Orden.query.get_or_404(id)
    return render_template_string(TEMPLATE_TICKET, orden=orden)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)