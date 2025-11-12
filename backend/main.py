import os
import secrets
import shutil
import uuid

from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from dotenv import load_dotenv
import json
import calendar
import traceback
from datetime import date
from datetime import timedelta
from werkzeug.utils import secure_filename
from sqlalchemy import func
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm.attributes import flag_modified





# Carga las variables de entorno desde un archivo .env para mayor seguridad
load_dotenv()

app = Flask(__name__)

# Configuración de CORS para permitir peticiones desde tu frontend (Vite en puerto 5173 por defecto)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:5173"}})

# Configuración segura usando variables de entorno
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'una-clave-secreta-para-desarrollo')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:admin@localhost/control_vehicular1')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de Flask-Mail para enviar correos con Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_APP_PASS')
app.config['MAIL_DEFAULT_SENDER'] = ("Sistema Placas", os.getenv('MAIL_USER'))


# Inicialización de las extensiones de Flask
db = SQLAlchemy(app)
mail = Mail(app)

# --- 2. DEFINICIÓN DEL MODELO DE LA BASE DE DATOS (ORM) ---
# Esta clase debe coincidir con la estructura de tu tabla 'Usuarios' ya existente
class Usuarios(db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(255), nullable=False)
    correo = db.Column(db.String(255), unique=True, nullable=False)
    rol = db.Column(db.String(50), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_ultimo_login = db.Column(db.DateTime, nullable=True)
    estado = db.Column(db.Enum('activo','inactivo'), default='activo')
    token_recuperacion = db.Column(db.String(255), nullable=True)

    id_chofer = db.Column(db.Integer, db.ForeignKey('choferes.id_chofer'), nullable=True)

    def to_dict(self):
        return {
            "id_usuario": self.id_usuario,
            "nombre": self.nombre,
            "usuario": self.usuario,
            "correo": self.correo,
            "rol": self.rol,
            "estado": self.estado,
            "fecha_registro": str(self.fecha_registro),
            "id_chofer": self.id_chofer,
            "nombre_chofer": self.chofer.nombre if self.chofer else None
        }

class Choferes(db.Model):
    __tablename__ = 'choferes'
    id_chofer = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    curp = db.Column(db.String(18), unique=True, nullable=False)
    calle = db.Column(db.String(255))
    colonia_localidad = db.Column(db.String(255))
    codpos = db.Column(db.String(10))
    municipio = db.Column(db.String(100))
    licencia_folio = db.Column(db.String(50))
    licencia_tipo = db.Column(db.String(50))
    licencia_vigencia = db.Column(db.Date)

    usuarios = db.relationship('Usuarios', backref='chofer', lazy=True)  # relación inversa
    
    def to_dict(self):
        return {
            "id_chofer": self.id_chofer,
            "nombre": self.nombre,
            "curp": self.curp,
            "licencia_tipo": self.licencia_tipo,
            "licencia_vigencia": str(self.licencia_vigencia) if self.licencia_vigencia else None
        }

    
class Unidades(db.Model):
    __tablename__ = "Unidades"
    id_unidad = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(100))
    vehiculo = db.Column(db.String(100))
    modelo = db.Column(db.Integer)
    clase_tipo = db.Column(db.String(50))
    niv = db.Column(db.String(50), unique=True)
    motor = db.Column(db.String(50))
    transmision = db.Column(db.String(50))
    combustible = db.Column(db.String(50))
    color = db.Column(db.String(50))
    telefono_gps = db.Column(db.String(20))
    sim_gps = db.Column(db.String(20))
    uid = db.Column(db.String(50))
    propietario = db.Column(db.String(255))
    sucursal = db.Column(db.String(100))
    compra_arrendado = db.Column(db.String(20))
    fecha_adquisicion = db.Column(db.Date)
    kilometraje_actual = db.Column(db.Integer)  # <-- esta línea es crucial

    placa = db.relationship('Placas', uselist=False, backref='unidad')  # one-to-one

    def to_dict(self):
        return {
            'id_unidad': self.id_unidad,
            'marca': self.marca,
            'vehiculo': self.vehiculo,
            'modelo': self.modelo,
            'clase_tipo': self.clase_tipo,
            'niv': self.niv,
            'motor': self.motor,
            'transmision': self.transmision,
            'combustible': self.combustible,
            'color': self.color,
            'telefono_gps': self.telefono_gps,
            'sim_gps': self.sim_gps,
            'uid': self.uid,
            'propietario': self.propietario,
            'sucursal': self.sucursal,
            'compra_arrendado': self.compra_arrendado,
            'fecha_adquisicion': str(self.fecha_adquisicion) if self.fecha_adquisicion else None,
            'kilometraje_actual': self.kilometraje_actual,  # <-- agregado
            'placa': self.placa.to_dict() if self.placa else None
        }



class Placas(db.Model):
    __tablename__ = "Placas"
    id_placa = db.Column(db.Integer, primary_key=True)
    id_unidad = db.Column(db.Integer, db.ForeignKey('Unidades.id_unidad'), nullable=False)
    folio = db.Column(db.String(50))
    placa = db.Column(db.String(10), unique=True, nullable=False)
    fecha_expedicion = db.Column(db.Date)
    fecha_vigencia = db.Column(db.Date)
    url_placa_frontal = db.Column(db.String(255))
    url_placa_trasera = db.Column(db.String(255))
    requiere_renovacion = db.Column(db.Boolean, default=False)
    def to_dict(self):
        return {
            'id_placa': self.id_placa,
            'id_unidad': self.id_unidad,
            'folio': self.folio,
            'placa': self.placa,
            'fecha_expedicion': str(self.fecha_expedicion) if self.fecha_expedicion else None,
            'fecha_vigencia': str(self.fecha_vigencia) if self.fecha_vigencia else None,
            'url_placa_frontal': self.url_placa_frontal,
            'url_placa_trasera': self.url_placa_trasera,
            'requiere_renovacion': self.requiere_renovacion
        }

class Garantias(db.Model):
    __tablename__ = "Garantias"
    
    id_garantia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_unidad = db.Column(db.Integer, db.ForeignKey("Unidades.id_unidad", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    aseguradora = db.Column(db.String(255))
    tipo_garantia = db.Column(db.String(100))
    no_poliza = db.Column(db.String(50), unique=True)
    url_poliza = db.Column(db.String(500))
    suma_asegurada = db.Column(db.Numeric(15,2))
    inicio_vigencia = db.Column(db.Date)
    vigencia = db.Column(db.Date)
    prima = db.Column(db.Numeric(15,2))

    unidad = db.relationship("Unidades", backref="garantias")

class HistorialGarantias(db.Model):
    __tablename__ = "HistorialGarantias"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_garantia = db.Column(db.Integer)
    id_unidad = db.Column(db.Integer)
    fecha_cambio = db.Column(db.DateTime, default=datetime.now)
    aseguradora = db.Column(db.String(255))
    tipo_garantia = db.Column(db.String(100))
    no_poliza = db.Column(db.String(50))
    url_poliza = db.Column(db.String(500))
    suma_asegurada = db.Column(db.Numeric(15,2))
    inicio_vigencia = db.Column(db.Date)
    vigencia = db.Column(db.Date)
    prima = db.Column(db.Numeric(15,2))
    usuario = db.Column(db.String(50))


class HistorialPlaca(db.Model):
    __tablename__ = "HistorialPlacas"
    id_historial = db.Column(db.Integer, primary_key=True)
    id_placa = db.Column(db.Integer, db.ForeignKey('Placas.id_placa'), nullable=False)
    id_unidad = db.Column(db.Integer, nullable=False)
    fecha_cambio = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    folio = db.Column(db.String(50))
    placa = db.Column(db.String(10))
    fecha_expedicion = db.Column(db.Date)
    fecha_vigencia = db.Column(db.Date)
    url_placa_frontal = db.Column(db.String(255))
    url_placa_trasera = db.Column(db.String(255))
    usuario = db.Column(db.String(100))


class VerificacionVehicular(db.Model):
    __tablename__ = 'verificacionvehicular'
    id_verificacion = db.Column(db.Integer, primary_key=True)
    id_unidad = db.Column(db.Integer, db.ForeignKey('Unidades.id_unidad'))
    ultima_verificacion = db.Column(db.Date)
    periodo_1 = db.Column(db.Date)
    periodo_1_real = db.Column(db.Date)
    url_verificacion_1 = db.Column(db.String(255))
    periodo_2 = db.Column(db.Date, nullable=True)
    periodo_2_real = db.Column(db.Date, nullable=True)
    url_verificacion_2 = db.Column(db.String(255), nullable=True)
    holograma = db.Column(db.String(50))
    folio_verificacion = db.Column(db.String(50))
    engomado = db.Column(db.String(50))

    unidad = db.relationship("Unidades", backref="verificaciones")


class HistorialVerificacionVehicular(db.Model):
    __tablename__ = 'HistorialVerificacionVehicular'

    id_historial = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_verificacion = db.Column(db.Integer, db.ForeignKey('verificacionvehicular.id_verificacion'), nullable=False)
    fecha_cambio = db.Column(db.DateTime, default=datetime.now)
    id_unidad = db.Column(db.Integer, db.ForeignKey('Unidades.id_unidad'), nullable=False)
    ultima_verificacion = db.Column(db.Date)
    periodo_1 = db.Column(db.Date)
    periodo_1_real = db.Column(db.Date)
    url_verificacion_1 = db.Column(db.String(255))
    periodo_2 = db.Column(db.Date)
    periodo_2_real = db.Column(db.Date)
    url_verificacion_2 = db.Column(db.String(255))
    holograma = db.Column(db.String(10))
    folio_verificacion = db.Column(db.String(100))
    engomado = db.Column(db.String(20))
    usuario = db.Column(db.String(100))

    def __repr__(self):
        return f"<HistorialVerificacionVehicular id={self.id_historial} id_verif={self.id_verificacion}>"


# Modelo para lugares de reparación
class LugarReparacion(db.Model):
    __tablename__ = "lugaresreparacion"
    id_lugar = db.Column(db.Integer, primary_key=True)
    nombre_lugar = db.Column(db.String(150), unique=True, nullable=False)
    tipo_lugar = db.Column(db.String(50))  # taller, empresa, mecánico particular
    direccion = db.Column(db.Text)
    contacto = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    precio = db.Column(db.Numeric(10,2))
    tipo_pago = db.Column(db.String(50))
    
# Modelo para Solicitud de Falla (chofer)
class SolicitudFalla(db.Model):
    __tablename__ = "solicitudesfallas"
    id_solicitud = db.Column(db.Integer, primary_key=True)
    id_unidad = db.Column(db.Integer, db.ForeignKey("Unidades.id_unidad"), nullable=False)
    id_pieza = db.Column(db.Integer, db.ForeignKey("piezas.id_pieza"), nullable=False)
    id_marca = db.Column(db.Integer, db.ForeignKey("marcaspiezas.id_marca"))
    tipo_servicio = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    id_chofer = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), default="pendiente")  # pendiente/aprobada/rechazada
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)

# Modelo para Falla Mecánica
class FallaMecanica(db.Model):
    __tablename__ = "fallasmecanicas"
    id_falla = db.Column(db.Integer, primary_key=True)
    id_unidad = db.Column(db.Integer, db.ForeignKey("Unidades.id_unidad"), nullable=False)
    fecha_falla = db.Column(db.DateTime, default=datetime.now, nullable=False)
    id_pieza = db.Column(db.Integer, db.ForeignKey("piezas.id_pieza"), nullable=False)
    id_marca = db.Column(db.Integer, db.ForeignKey("marcaspiezas.id_marca"))
    tipo_servicio = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    id_lugar = db.Column(db.Integer, db.ForeignKey("lugaresreparacion.id_lugar"))
    proveedor = db.Column(db.String(255))
    tipo_pago = db.Column(db.String(50))
    costo = db.Column(db.Numeric(15,2))
    tiempo_uso_pieza = db.Column(db.Integer)
    aplica_poliza = db.Column(db.Boolean, default=False)
    observaciones = db.Column(db.Text)
    url_comprobante = db.Column(db.String(500))

class Piezas(db.Model):
    __tablename__ = "piezas"
    id_pieza = db.Column(db.Integer, primary_key=True)
    nombre_pieza = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.Text)

class MarcasPiezas(db.Model):
    __tablename__ = "marcaspiezas"
    id_marca = db.Column(db.Integer, primary_key=True)
    nombre_marca = db.Column(db.String(100), nullable=False, unique=True)
    pais_origen = db.Column(db.String(100))
    observaciones = db.Column(db.Text)


class Refrendo_Tenencia(db.Model):
    __tablename__ = 'Refrendo_Tenencia'
    id_pago = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_unidad = db.Column(db.Integer, db.ForeignKey('Unidades.id_unidad'), nullable=False)
    tipo_pago = db.Column(db.Enum('REFRENDO','TENENCIA','AMBOS'), nullable=False, default='REFRENDO')
    monto = db.Column(db.Numeric(10,2), nullable=False, default=0)
    monto_refrendo = db.Column(db.Numeric(10,2), nullable=False, default=0)
    monto_tenencia = db.Column(db.Numeric(10,2), nullable=False, default=0)
    fecha_pago = db.Column(db.Date, nullable=False)
    limite_pago = db.Column(db.Date, nullable=False)
    url_factura_refrendo = db.Column(db.String(255))
    url_factura_tenencia = db.Column(db.String(255))
    observaciones = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación ORM
    unidad = db.relationship("Unidades", backref=db.backref("pagos", lazy=True))


class Historial_Refrendo_Tenencia(db.Model):
    __tablename__ = 'Historial_Refrendo_Tenencia'
    id_historial = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_pago = db.Column(db.Integer, db.ForeignKey('Refrendo_Tenencia.id_pago'), nullable=False)
    id_unidad = db.Column(db.Integer, db.ForeignKey('Unidades.id_unidad'), nullable=False)
    tipo_pago = db.Column(db.Enum('REFRENDO','TENENCIA','AMBOS'), nullable=False)
    monto = db.Column(db.Numeric(10,2), default=0)
    monto_refrendo = db.Column(db.Numeric(10,2), default=0)
    monto_tenencia = db.Column(db.Numeric(10,2), default=0)
    fecha_pago = db.Column(db.Date)
    url_factura_refrendo = db.Column(db.String(255))
    url_factura_tenencia = db.Column(db.String(255))
    observaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    tipo_movimiento = db.Column(db.Enum('REGISTRO','ACTUALIZACION','ELIMINACION'), nullable=False)
    usuario_registro = db.Column(db.String(100))
    observaciones_adicional = db.Column(db.Text)

    # Relaciones ORM
    pago = db.relationship("Refrendo_Tenencia", backref=db.backref("historiales", lazy=True))
    unidad = db.relationship("Unidades", backref=db.backref("historiales", lazy=True))

# ---------------------
# MODELOS (mapear tablas existentes)
# ---------------------
class TiposMantenimiento(db.Model):
    __tablename__ = 'tiposmantenimiento'
    id_tipo_mantenimiento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_tipo = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.Text)

class FrecuenciasPorMarca(db.Model):
    __tablename__ = 'frecuenciaspormarca'
    id_frecuencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    marca = db.Column(db.String(100), nullable=False)
    id_tipo_mantenimiento = db.Column(db.Integer, db.ForeignKey('tiposmantenimiento.id_tipo_mantenimiento'), nullable=False)
    frecuencia_tiempo = db.Column(db.Integer, nullable=False)        # días
    frecuencia_kilometraje = db.Column(db.Integer, nullable=False)   # km

class MantenimientosProgramados(db.Model):
    __tablename__ = 'mantenimientosprogramados'
    id_mantenimiento_programado = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_unidad = db.Column(db.Integer, nullable=False)
    id_tipo_mantenimiento = db.Column(db.Integer, db.ForeignKey('tiposmantenimiento.id_tipo_mantenimiento'), nullable=False)
    fecha_ultimo_mantenimiento = db.Column(db.Date)
    kilometraje_ultimo = db.Column(db.Integer)
    proximo_mantenimiento = db.Column(db.Date)
    proximo_kilometraje = db.Column(db.Integer)

class Mantenimientos(db.Model):
    __tablename__ = 'mantenimientos'
    id_mantenimiento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_mantenimiento_programado = db.Column(db.Integer, db.ForeignKey('mantenimientosprogramados.id_mantenimiento_programado'))
    id_unidad = db.Column(db.Integer, nullable=False)
    tipo_mantenimiento = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_realizacion = db.Column(db.Date, nullable=False)
    kilometraje = db.Column(db.Integer)
    realizado_por = db.Column(db.String(255))
    empresa_garantia = db.Column(db.String(255))
    cobertura_garantia = db.Column(db.String(255))
    costo = db.Column(db.Numeric(15,2))
    observaciones = db.Column(db.Text)
    url_comprobante = db.Column(db.String(500))



class Asignaciones(db.Model):
    __tablename__ = "Asignaciones"
    id_asignacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_chofer = db.Column(db.Integer, db.ForeignKey('choferes.id_chofer'), nullable=False)
    id_unidad = db.Column(db.Integer, db.ForeignKey('Unidades.id_unidad'), nullable=False)
    fecha_asignacion = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=True)
    __table_args__ = (db.UniqueConstraint('id_chofer','id_unidad','fecha_asignacion', name='unique_asignacion'),)

class HistorialAsignaciones(db.Model):
    __tablename__ = "HistorialAsignaciones"
    id_historial = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_asignacion = db.Column(db.Integer, db.ForeignKey('Asignaciones.id_asignacion', ondelete='CASCADE'), nullable=False)
    fecha_cambio = db.Column(db.DateTime, default=datetime.now)
    id_chofer = db.Column(db.Integer)
    fecha_asignacion = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    usuario = db.Column(db.String(100))

#==============================================================================================================================

def get_db_connection():
    # Devuelve la conexión cruda para ejecutar SQL directo
    return db.engine.raw_connection()

# --- 3. RUTAS DE LA API ---

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    app.logger.info(f"Intento de inicio de sesión para el usuario: {username}")

    if not username or not password:
        app.logger.warning("No se proporcionó usuario o contraseña.")
        return jsonify({"error": "Usuario y contraseña son requeridos"}), 400

    user = Usuarios.query.filter_by(usuario=username, estado='activo').first()

    if user:
        app.logger.info(f"Usuario encontrado: {user.usuario}, contraseña almacenada: {user.contraseña}")
        if check_password_hash(user.contraseña, password):
            session['user_id'] = user.id_usuario
            session['username'] = user.usuario
            session['rol'] = user.rol
            user.fecha_ultimo_login = datetime.utcnow()
            db.session.commit()
            return jsonify({
                "message": "Inicio de sesión exitoso",
                "user": {"id": user.id_usuario, "username": user.usuario, "nombre": user.nombre, "rol": user.rol}
            }), 200
        else:
            app.logger.warning("Contraseña inválida proporcionada.")
    else:
        app.logger.info("Usuario no encontrado o inactivo.")

    return jsonify({"error": "Credenciales inválidas o usuario inactivo"}), 401



# =======================
#USUARIOS - CREACION
# ======================= 
#@app.route('/api/usuarios', methods=['POST'])
#def crear_usuario():
 #   data = request.json
  #  try:
   #     nuevo_usuario = Usuarios(
    #        nombre=data.get('nombre'),
     #       usuario=data.get('usuario'),
      #      contraseña=generate_password_hash(data.get('contraseña')),
       #     correo=data.get('correo'),
       #     rol=data.get('rol')
        #)
        #db.session.add(nuevo_usuario)
        #db.session.commit()
        #return jsonify({"mensaje": "Usuario creado correctamente"}), 201
    #except Exception as e:
     #   db.session.rollback()
      #  return jsonify({"error": str(e)}), 500


@app.route('/api/usuarios', methods=['POST'])
def crear_usuario():
    data = request.json
    try:
        # --- Datos del usuario ---
        nombre = data.get('nombre')
        usuario = data.get('usuario')
        contraseña = data.get('contraseña')
        correo = data.get('correo')
        rol = data.get('rol', 'usuario')
        id_chofer = data.get('id_chofer')  # opcional para chofer existente

        # --- Datos del chofer si se va a crear uno nuevo ---
        crear_chofer = data.get('crear_chofer', False)
        chofer_data = data.get('chofer_data', {})

        # --- Validación básica ---
        if not (nombre and usuario and contraseña and correo):
            return jsonify({'error': 'Faltan datos obligatorios'}), 400

        # --- Transacción ---
        if crear_chofer:
            # Crear chofer primero
            nuevo_chofer = Choferes(
                nombre=chofer_data.get('nombre'),
                curp=chofer_data.get('curp'),
                calle=chofer_data.get('calle'),
                colonia_localidad=chofer_data.get('colonia_localidad'),
                codpos=chofer_data.get('codpos'),
                municipio=chofer_data.get('municipio'),
                licencia_folio=chofer_data.get('licencia_folio'),
                licencia_tipo=chofer_data.get('licencia_tipo'),
                licencia_vigencia=chofer_data.get('licencia_vigencia')
            )
            db.session.add(nuevo_chofer)
            db.session.flush()  # Para obtener el id antes del commit
            id_chofer = nuevo_chofer.id_chofer
            rol = 'chofer'  # forzar rol chofer

        # Crear usuario
        nuevo_usuario = Usuarios(
            nombre=nombre,
            usuario=usuario,
            contraseña=generate_password_hash(contraseña),
            correo=correo,
            rol=rol,
            id_chofer=id_chofer
        )
        db.session.add(nuevo_usuario)
        db.session.commit()

        return jsonify({"mensaje": "Usuario creado correctamente"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/usuarios', methods=['GET'])
def obtener_usuarios():
    usuarios = Usuarios.query.all()
    resultado = []
    for u in usuarios:
        resultado.append({
            'id_usuario': u.id_usuario,
            'nombre': u.nombre,
            'usuario': u.usuario,
            'correo': u.correo,
            'rol': u.rol,
            'fecha_registro': u.fecha_registro,
            'fecha_ultimo_login': u.fecha_ultimo_login,
            'estado': u.estado,
            'id_chofer': u.id_chofer,
            'chofer': {
                'id_chofer': u.chofer.id_chofer,
                'nombre': u.chofer.nombre,
                'curp': u.chofer.curp,
                'calle': u.chofer.calle,
                'colonia_localidad': u.chofer.colonia_localidad,
                'codpos': u.chofer.codpos,
                'municipio': u.chofer.municipio,
                'licencia_folio': u.chofer.licencia_folio,
                'licencia_tipo': u.chofer.licencia_tipo,
                'licencia_vigencia': u.chofer.licencia_vigencia
            } if u.chofer else None
        })
    return jsonify(resultado), 200

@app.route('/api/usuarios/<int:id_usuario>', methods=['PUT'])
def actualizar_usuario(id_usuario):
    data = request.json
    try:
        usuario = Usuarios.query.get_or_404(id_usuario)

        # Campos básicos
        usuario.nombre = data.get('nombre', usuario.nombre)
        usuario.usuario = data.get('usuario', usuario.usuario)
        usuario.correo = data.get('correo', usuario.correo)
        usuario.rol = data.get('rol', usuario.rol)
        usuario.estado = data.get('estado', usuario.estado)

        # Actualizar contraseña solo si se proporciona
        if 'contraseña' in data and data['contraseña']:
            usuario.contraseña = generate_password_hash(data['contraseña'])

        # Asignar chofer
        id_chofer = data.get('id_chofer')
        if id_chofer is not None:
            # Validar que el chofer no tenga usuario ya asignado (excepto este usuario)
            chofer_existente = Usuarios.query.filter_by(id_chofer=id_chofer).first()
            if chofer_existente and chofer_existente.id_usuario != id_usuario:
                return jsonify({'error': 'El chofer ya tiene un usuario asignado'}), 400
            usuario.id_chofer = id_chofer
        else:
            usuario.id_chofer = None

        db.session.commit()
        return jsonify({"mensaje": "Usuario actualizado correctamente"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/choferes', methods=['GET'])
def obtener_choferes():
    try:
        # solo choferes que no tengan un usuario asignado
        choferes = Choferes.query.filter(~Choferes.usuarios.any()).all()
        resultado = []
        for c in choferes:
            resultado.append({
                'id_chofer': c.id_chofer,
                'nombre': c.nombre,
                'curp': c.curp,
                'calle': c.calle,
                'colonia_localidad': c.colonia_localidad,
                'codpos': c.codpos,
                'municipio': c.municipio,
                'licencia_folio': c.licencia_folio,
                'licencia_tipo': c.licencia_tipo,
                'licencia_vigencia': c.licencia_vigencia.isoformat() if c.licencia_vigencia else None
            })
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



#` =======================
# RECUPERACION DE CONTRASEÑA
# =======================`
@app.route('/request-reset', methods=['POST'])
def request_password_reset():
    """Maneja la solicitud de recuperación de contraseña."""
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Correo electrónico requerido"}), 400

    user = Usuarios.query.filter_by(correo=email).first()
    if user:
        # Generar el token de recuperación
        token = secrets.token_urlsafe(32)
        user.token_recuperacion = token
        user.token_expiracion = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        try:
            # Crear el enlace de restablecimiento
            #reset_link = f"{os.getenv('FRONTEND_URL', 'http://192.168.254.158:5173')}/reset-password/{token}"
            frontend_url = "http://192.168.254.158:5173"
            reset_link = f"{frontend_url}/reset-password/{token}"

            msg = Message(
                'Restablecimiento de Contraseña',
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )

            msg.html = f"""
            <div style="font-family: 'Arial', sans-serif; max-width: 600px; margin: auto; padding: 30px; background-color: #000000; color: #ffffff; border-radius: 10px; text-align: center;">
                
                <h1 style="font-size: 24px; margin-bottom: 20px;">Restablece tu contraseña</h1>
                
                <p style="font-size: 16px; margin-bottom: 30px; color: #e0e0e0;">
                    Hola,<br>
                    Has solicitado restablecer tu contraseña. Haz clic en el botón a continuación.
                </p>
                
                <a href="{reset_link}" style="
                    display: inline-block;
                    padding: 12px 28px;
                    font-size: 16px;
                    font-weight: 600;
                    color: #ffffff;
                    background-color: #ff1f3c;
                    text-decoration: none;
                    border-radius: 6px;
                ">
                    Restablecer Contraseña
                </a>
                
                <p style="font-size: 14px; color: #bbbbbb; margin-top: 25px;">
                    Si no solicitaste este cambio, ignora este correo.
                </p>
                
                <p style="font-size: 12px; color: #888888;">
                    Este enlace expira en 1 hora.
                </p>
            </div>
            """
            print("Enlace de recuperación:", reset_link)


            mail.send(msg)


        except Exception as e:
            app.logger.error(f"Error al enviar correo de recuperación: {e}")
            return jsonify({"error": "Error al enviar el correo de recuperación."}), 500

    return jsonify({"message": "Si tu correo está registrado, recibirás un enlace."}), 200


@app.route('/reset-password/<string:token>', methods=['POST'])
def reset_password(token):
    """Maneja el cambio de contraseña a través del token."""
    data = request.get_json()
    password = data.get('password')

    if not password:    
        return jsonify({"error": "La nueva contraseña es requerida"}), 400

    user = Usuarios.query.filter_by(token_recuperacion=token).filter(Usuarios.token_expiracion > datetime.utcnow()).first()

    if not user:
        return jsonify({"error": "El token es inválido o ha expirado."}), 400

    user.contraseña = generate_password_hash(password)
    user.token_recuperacion = None
    user.token_expiracion = None
    db.session.commit()

    return jsonify({"message": "Contraseña actualizada con éxito"}), 200

# =======================
#UNIDADES - OBTENER DATOS
# =======================
@app.route('/api/unidades', methods=['GET'])
def get_unidades_data():
    conn = db.engine.raw_connection()
    try:
        cursor = conn.cursor()
        query = """
        SELECT
        U.id_unidad,
        U.marca,
        U.vehiculo,
        U.modelo,
        U.niv,
        P.placa,
        U.fecha_adquisicion,
        P.fecha_vigencia AS fecha_vencimiento_tarjeta,
        CASE WHEN P.fecha_vigencia < CURDATE() THEN 'Vencida' ELSE 'Activa' END AS estado_tarjeta,
        V.engomado,
        C.nombre AS chofer_asignado,
        JSON_OBJECT(
            'color', U.color,
            'clase_tipo', U.clase_tipo,
            'motor', U.motor,
            'transmision', U.transmision,
            'combustible', U.combustible,
            'sucursal', U.sucursal,
            'compra_arrendado', U.compra_arrendado,
            'propietario', U.propietario,
            'uid', U.uid,
            'telefono_gps', U.telefono_gps,
            'sim_gps', U.sim_gps,
            'no_poliza', G.no_poliza,
            'folio_verificacion', V.folio_verificacion
        ) AS mas_datos
    FROM Unidades U
    LEFT JOIN (
        SELECT * FROM Placas P1
        WHERE P1.id_placa = (SELECT P2.id_placa FROM Placas P2 WHERE P2.id_unidad = P1.id_unidad ORDER BY P2.fecha_vigencia DESC LIMIT 1)
    ) P ON U.id_unidad = P.id_unidad
    LEFT JOIN (
        SELECT * FROM Garantias G1
        WHERE G1.id_garantia = (SELECT G2.id_garantia FROM Garantias G2 WHERE G2.id_unidad = G1.id_unidad ORDER BY G2.vigencia DESC LIMIT 1)
    ) G ON U.id_unidad = G.id_unidad
    LEFT JOIN (
        SELECT * FROM VerificacionVehicular V1
        WHERE V1.id_verificacion = (SELECT V2.id_verificacion FROM VerificacionVehicular V2 WHERE V2.id_unidad = V1.id_unidad ORDER BY V2.ultima_verificacion DESC LIMIT 1)
    ) V ON U.id_unidad = V.id_unidad
    LEFT JOIN Asignaciones A ON U.id_unidad = A.id_unidad AND A.fecha_fin IS NULL
    LEFT JOIN Choferes C ON A.id_chofer = C.id_chofer
    ORDER BY U.id_unidad;

        """
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Formatear fechas
        for unidad in results:
            if unidad['fecha_adquisicion']:
                unidad['fecha_adquisicion'] = unidad['fecha_adquisicion'].strftime('%Y-%m-%d')
            if unidad['fecha_vencimiento_tarjeta']:
                unidad['fecha_vencimiento_tarjeta'] = unidad['fecha_vencimiento_tarjeta'].strftime('%Y-%m-%d')
            if unidad['mas_datos']:
                unidad['mas_datos'] = json.loads(unidad['mas_datos'])  # Convertir JSON string a dict

        return jsonify(results), 200
    except Exception as e:
        print(f"Error al ejecutar la consulta: {e}")
        return jsonify({"error": "Error al obtener los datos de unidades"}), 500
    finally:
        cursor.close()
        conn.close()
# =======================
# PUT - Actualizar unidad
# =======================
@app.route('/api/unidades/<int:id_unidad>', methods=['PUT'])
def update_unidad(id_unidad):
    data = request.json
    conn = db.engine.raw_connection()
    try:
        cursor = conn.cursor()
        query = """
        UPDATE Unidades
        SET marca = %s,
            vehiculo = %s,
            modelo = %s,
            niv = %s,
            fecha_adquisicion = %s,
            color = %s,
            clase_tipo = %s,
            motor = %s,
            transmision = %s,
            combustible = %s,
            sucursal = %s,
            compra_arrendado = %s,
            propietario = %s,
            uid = %s,
            telefono_gps = %s,
            sim_gps = %s
        WHERE id_unidad = %s
        """
        cursor.execute(query, (
            data.get("marca"),
            data.get("vehiculo"),
            data.get("modelo"),
            data.get("niv"),
            data.get("fecha_adquisicion"),
            data.get("color"),
            data.get("clase_tipo"),
            data.get("motor"),
            data.get("transmision"),
            data.get("combustible"),
            data.get("sucursal"),
            data.get("compra_arrendado"),
            data.get("propietario"),
            data.get("uid"),
            data.get("telefono_gps"),
            data.get("sim_gps"),
            id_unidad
        ))
        conn.commit()
        return jsonify({"message": "Unidad actualizada correctamente"}), 200
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return jsonify({"error": "Error al actualizar la unidad"}), 500
    finally:
        cursor.close()
        conn.close()

#ELIMINACION DE UNIDADES
@app.route('/api/unidades/<int:id_unidad>', methods=['DELETE'])
def delete_unidad(id_unidad):
    conn = db.engine.raw_connection()
    try:
        cursor = conn.cursor()
        # Eliminación directa de la unidad; los registros relacionados se borrarán en cascada
        query = "DELETE FROM Unidades WHERE id_unidad = %s"
        cursor.execute(query, (id_unidad,))
        conn.commit()
        return jsonify({"message": "Unidad eliminada correctamente"}), 200
    except Exception as e:
        print(f"❌ Error al eliminar unidad: {e}")
        return jsonify({"error": "Error al eliminar la unidad"}), 500
    finally:
        cursor.close()
        conn.close()



ALLOWED_EXTENSIONS = {'pdf'}



@app.route('/api/unidades', methods=['POST'])
def agregar_unidad():
    try:
        UPLOAD_FOLDER = 'uploads/placas_pdf'
        # Datos del formulario
        data = request.form

        nueva_unidad = Unidades(
            marca=data.get("marca"),
            vehiculo=data.get("vehiculo"),
            modelo=data.get("modelo"),
            clase_tipo=data.get("clase_tipo"),
            niv=data.get("niv"),
            motor=data.get("motor"),
            transmision=data.get("transmision"),
            combustible=data.get("combustible"),
            color=data.get("color"),
            telefono_gps=data.get("telefono_gps"),
            sim_gps=data.get("sim_gps"),
            uid=data.get("uid"),
            propietario=data.get("propietario"),
            sucursal=data.get("sucursal"),
            compra_arrendado=data.get("compra_arrendado"),
            fecha_adquisicion=data.get("fecha_adquisicion")
        )

        # Guardar archivos PDF
        pdf_frontal = request.files.get("pdf_frontal")
        pdf_trasero = request.files.get("pdf_trasero")
        url_frontal = None
        url_trasero = None

        if pdf_frontal:
            filename = secure_filename(pdf_frontal.filename)
            pdf_frontal.save(f"uploads/placas/{filename}")
            url_frontal = f"uploads/placas/{filename}"

        if pdf_trasero:
            filename = secure_filename(pdf_trasero.filename)
            pdf_trasero.save(f"uploads/placas/{filename}")
            url_trasero = f"uploads/placas/{filename}"

        # Crear placa
        nueva_placa = Placas(
            folio=data.get("folio"),
            placa=data.get("placa"),
            fecha_expedicion=data.get("fecha_expedicion"),
            fecha_vigencia=data.get("fecha_vigencia"),
            url_placa_frontal=url_frontal,
            url_placa_trasera=url_trasero
        )

        nueva_unidad.placa = nueva_placa

        db.session.add(nueva_unidad)
        db.session.commit()

        return jsonify({"mensaje": "Unidad y placa registradas exitosamente.", "unidad": nueva_unidad.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

 #============================================================================
 #Asignaciones
 #===========================================================================

@app.route('/asignaciones', methods=['POST'])
def crear_asignacion():
    data = request.get_json()
    id_chofer = data.get('id_chofer')
    id_unidad = data.get('id_unidad')
    usuario = data.get('usuario', 'sistema')

    # Validaciones
    if not id_chofer or not id_unidad:
        return jsonify({"error":"id_chofer y id_unidad son requeridos"}), 400

    # Evitar duplicados activos
    asignacion_existente = Asignaciones.query.filter_by(id_chofer=id_chofer, id_unidad=id_unidad, fecha_fin=None).first()
    if asignacion_existente:
        return jsonify({"error":"El chofer ya está asignado a esta unidad"}), 400

    nueva = Asignaciones(
        id_chofer=id_chofer,
        id_unidad=id_unidad,
        fecha_asignacion=date.today()
    )
    db.session.add(nueva)
    db.session.flush()  # para obtener id_asignacion

    # Registrar en historial
    historial = HistorialAsignaciones(
        id_asignacion=nueva.id_asignacion,
        id_chofer=id_chofer,
        fecha_asignacion=date.today(),
        fecha_fin=None,
        usuario=usuario
    )
    db.session.add(historial)
    db.session.commit()

    return jsonify({"message":"Asignación creada", "id_asignacion": nueva.id_asignacion}), 201

@app.route('/asignaciones/<int:id_asignacion>/finalizar', methods=['PUT'])
def finalizar_asignacion(id_asignacion):
    usuario = request.json.get('usuario', 'sistema')
    asignacion = Asignaciones.query.get(id_asignacion)
    if not asignacion or asignacion.fecha_fin is not None:
        return jsonify({"error":"Asignación no encontrada o ya finalizada"}), 404

    asignacion.fecha_fin = date.today()
    db.session.add(asignacion)

    # Registrar en historial
    historial = HistorialAsignaciones(
        id_asignacion=id_asignacion,
        id_chofer=asignacion.id_chofer,
        fecha_asignacion=asignacion.fecha_asignacion,
        fecha_fin=date.today(),
        usuario=usuario
    )
    db.session.add(historial)
    db.session.commit()

    return jsonify({"message":"Asignación finalizada"}), 200

@app.route('/historial_asignaciones', methods=['GET'])
def historial():
    historial = HistorialAsignaciones.query.order_by(HistorialAsignaciones.fecha_cambio.desc()).all()
    salida = []
    for h in historial:
        salida.append({
            "id_historial": h.id_historial,
            "id_asignacion": h.id_asignacion,
            "id_chofer": h.id_chofer,
            "fecha_asignacion": h.fecha_asignacion.isoformat() if h.fecha_asignacion else None,
            "fecha_fin": h.fecha_fin.isoformat() if h.fecha_fin else None,
            "usuario": h.usuario,
            "fecha_cambio": h.fecha_cambio.isoformat()
        })
    return jsonify(salida)

@app.route('/asignaciones', methods=['GET'])
def listar_asignaciones():
    asignaciones = Asignaciones.query.order_by(Asignaciones.fecha_asignacion.desc()).all()
    salida = []
    for a in asignaciones:
        salida.append({
            "id_asignacion": a.id_asignacion,
            "id_chofer": a.id_chofer,
            "id_unidad": a.id_unidad,
            "fecha_asignacion": a.fecha_asignacion.isoformat(),
            "fecha_fin": a.fecha_fin.isoformat() if a.fecha_fin else None,
        })
    return jsonify(salida)

@app.route('/choferes', methods=['GET'])
def listar_choferes():
    choferes = Choferes.query.all()
    return jsonify([
        {
            "id_chofer": c.id_chofer,
            "nombre": c.nombre,
            "curp": c.curp
        } for c in choferes
    ])

@app.route('/unidades', methods=['GET'])
def listar_unidad():
    unidades = Unidades.query.all()
    salida = []
    for u in unidades:
        # si quieres incluir la placa principal
        placa_obj = Placas.query.filter_by(id_unidad=u.id_unidad).first()
        salida.append({
            "id_unidad": u.id_unidad,
            "vehiculo": u.vehiculo,
            "marca": u.marca,
            "modelo": u.modelo,
            "placa": placa_obj.placa if placa_obj else None
        })
    return jsonify(salida)

@app.route('/unidades/libres', methods=['GET'])
def listar_unidades_libres():
    # Obtener todas las unidades
    todas_unidades = Unidades.query.all()
    # Obtener IDs de unidades que ya están asignadas activamente
    asignadas = [a.id_unidad for a in Asignaciones.query.filter_by(fecha_fin=None).all()]
    
    unidades_libres = [
        {
            "id_unidad": u.id_unidad,
            "nombre": u.vehiculo
        }
        for u in todas_unidades if u.id_unidad not in asignadas
    ]
    return jsonify(unidades_libres)

@app.route('/unidades/chofer/<int:id_usuario>', methods=['GET'])
def obtener_unidad_por_chofer(id_usuario):
    try:
        # Obtener el chofer vinculado al usuario
        usuario = db.session.get(Usuarios, id_usuario)
        if not usuario or not usuario.id_chofer:
            return jsonify({'error': 'El usuario no está vinculado a un chofer'}), 404

        id_chofer = usuario.id_chofer

        # Buscar asignación activa (sin fecha_fin o aún vigente)
        asignacion = (
            Asignaciones.query
            .filter_by(id_chofer=id_chofer)
            .filter((Asignaciones.fecha_fin == None) | (Asignaciones.fecha_fin >= date.today()))
            .order_by(Asignaciones.fecha_asignacion.desc())
            .first()
        )

        if not asignacion:
            return jsonify({'error': 'No tiene unidad asignada'}), 404

        # Buscar datos de la unidad asignada
        unidad = db.session.get(Unidades, asignacion.id_unidad)
        if not unidad:
            return jsonify({'error': 'Unidad no encontrada'}), 404

        # Obtener placa asociada
        placa_obj = Placas.query.filter_by(id_unidad=unidad.id_unidad).first()
        placa = placa_obj.placa if placa_obj else None

        return jsonify({
            'id_unidad': unidad.id_unidad,
            'vehiculo': unidad.vehiculo,
            'marca': unidad.marca,
            'modelo': unidad.modelo,
            'placa': placa,
            'id_chofer': id_chofer,
            'id_usuario': id_usuario
        })

    except Exception as e:
        print("Error en obtener_unidad_por_chofer:", e)
        return jsonify({'error': 'Error interno del servidor'}), 500

# =======================
#GARANTIAS - OBTENER DATOS
# =======================
@app.route('/api/garantias', methods=['GET'])
def obtener_garantias():
    conn = db.engine.raw_connection()
    cursor = None
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                g.id_garantia,
                COALESCE(C.nombre, 'Sin chofer asignado') AS chofer_asignado,
                g.id_unidad,
                u.marca,
                u.vehiculo,
                g.aseguradora,
                g.tipo_garantia,
                g.no_poliza,
                g.url_poliza,
                g.suma_asegurada,
                g.inicio_vigencia,
                g.vigencia,
                g.prima
            FROM Garantias g
            JOIN Unidades u ON g.id_unidad = u.id_unidad
            LEFT JOIN (
                SELECT id_unidad, id_chofer
                FROM Asignaciones
                WHERE fecha_fin IS NULL
            ) A ON u.id_unidad = A.id_unidad
            LEFT JOIN Choferes C ON A.id_chofer = C.id_chofer
            ORDER BY u.id_unidad, g.id_garantia;
        """

        cursor.execute(query)
        garantias = cursor.fetchall()
        columnas = [desc[0] for desc in cursor.description]
        resultados = []

        for fila in garantias:
            fila_dict = dict(zip(columnas, fila))
            # Convertir fechas a formato YYYY-MM-DD para inputs tipo date
            for campo in ['inicio_vigencia', 'vigencia']:
                if fila_dict[campo]:
                    fila_dict[campo] = fila_dict[campo].strftime('%Y-%m-%d')
                else:
                    fila_dict[campo] = None
            resultados.append(fila_dict)

        return jsonify(resultados), 200

    except Exception as e:
        print(f"Error al obtener garantías: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/garantias', methods=['POST'])
def crear_garantia():
    UPLOAD_FOLDER = 'uploads/garantias'
    HISTORIAL_FOLDER = 'uploads/historial_garantias'

    ruta_upload_abs = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    ruta_historial_abs = os.path.join(current_app.root_path, HISTORIAL_FOLDER)
    os.makedirs(ruta_upload_abs, exist_ok=True)
    os.makedirs(ruta_historial_abs, exist_ok=True)

    data = request.form
    archivo = request.files.get('archivo')

    if not archivo or archivo.filename == '':
        return jsonify({"error": "Debe subir un archivo PDF"}), 400
    if not allowed_file(archivo.filename):
        return jsonify({"error": "Solo se permiten archivos PDF"}), 400

    id_unidad = data.get('id_unidad')
    if not id_unidad:
        return jsonify({"error": "Debe especificar una unidad"}), 400

    garantia = Garantias.query.filter_by(id_unidad=id_unidad).first()

    filename = secure_filename(f"{id_unidad}_{date.today()}.pdf")
    ruta_guardado_abs = os.path.join(ruta_upload_abs, filename)
    archivo.save(ruta_guardado_abs)
    ruta_pdf = os.path.join(UPLOAD_FOLDER, filename).replace("\\", "/")

    try:
        def mover_a_historial(ruta_relativa):
            if not ruta_relativa:
                return None
            ruta_abs = os.path.join(current_app.root_path, ruta_relativa.lstrip("/").replace("/", os.sep))
            if os.path.exists(ruta_abs):
                nombre = os.path.basename(ruta_abs)
                nueva_ruta_abs = os.path.join(ruta_historial_abs, nombre)
                shutil.move(ruta_abs, nueva_ruta_abs)
                return os.path.join(HISTORIAL_FOLDER, nombre).replace("\\", "/")
            return ruta_relativa

        hoy = date.today()
        puede_renovar = False

        if garantia and garantia.vigencia:
            fecha_pre_renovacion = garantia.vigencia - timedelta(days=30)
            # Puede renovar si ya venció o estamos dentro del mes previo
            puede_renovar = hoy >= fecha_pre_renovacion

        # Caso: garantía existente y permite renovación
        if garantia and puede_renovar:
            url_historial = mover_a_historial(garantia.url_poliza)

            historial = HistorialGarantias(
                id_garantia=garantia.id_garantia,
                id_unidad=garantia.id_unidad,
                fecha_cambio=datetime.now(),
                aseguradora=garantia.aseguradora,
                tipo_garantia=garantia.tipo_garantia,
                no_poliza=garantia.no_poliza,
                url_poliza=url_historial,
                suma_asegurada=garantia.suma_asegurada,
                inicio_vigencia=garantia.inicio_vigencia,
                vigencia=garantia.vigencia,
                prima=garantia.prima,
                usuario=data.get('usuario', 'sistema')
            )
            db.session.add(historial)

            # Actualizar con nuevos datos
            garantia.aseguradora = data.get('aseguradora')
            garantia.tipo_garantia = data.get('tipo_garantia')
            garantia.no_poliza = data.get('no_poliza')
            garantia.url_poliza = ruta_pdf
            garantia.suma_asegurada = data.get('suma_asegurada')
            garantia.inicio_vigencia = data.get('inicio_vigencia')
            garantia.vigencia = data.get('vigencia')
            garantia.prima = data.get('prima')
            print("Garantía actualizada y enviada a historial (vencida o pre-renovación)")

        # Caso: no hay garantía previa → crear nueva
        elif not garantia:
            nueva = Garantias(
                id_unidad=id_unidad,
                aseguradora=data.get('aseguradora'),
                tipo_garantia=data.get('tipo_garantia'),
                no_poliza=data.get('no_poliza'),
                url_poliza=ruta_pdf,
                suma_asegurada=data.get('suma_asegurada'),
                inicio_vigencia=data.get('inicio_vigencia'),
                vigencia=data.get('vigencia'),
                prima=data.get('prima')
            )
            db.session.add(nueva)
            print("Nueva garantía creada")

        # Caso: aún vigente y fuera del mes previo
        else:
            return jsonify({"error": "La garantía aún está vigente y no puede registrarse una nueva."}), 400

        db.session.commit()
        return jsonify({"message": "Garantía registrada correctamente."}), 201

    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/garantias/<int:id_garantia>', methods=['PUT'])
def actualizar_garantia(id_garantia):
    print(f"\n=== ACTUALIZAR GARANTÍA: {id_garantia} ===")
    print("Headers recibidos:", dict(request.headers))
    print("Form data recibida:", request.form)
    print("Archivos recibidos:", request.files)

    UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads', 'garantias')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    ALLOWED_EXTENSIONS = {'pdf'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    data = request.form
    archivo = request.files.get('archivo')

    conn = db.engine.raw_connection()
    cursor = conn.cursor()

    try:
        # Validar existencia de la garantía
        cursor.execute(
            "SELECT id_garantia, url_poliza FROM Garantias WHERE id_garantia = %s",
            (id_garantia,)
        )
        garantia_existente = cursor.fetchone()
        if not garantia_existente:
            print(f"⚠️ Garantía {id_garantia} no encontrada")
            return jsonify({"error": "La garantía no existe"}), 404
        print(f"✅ Garantía encontrada: {garantia_existente}")

        # Validar unidad
        id_unidad = data.get('id_unidad')
        cursor.execute("SELECT id_unidad FROM Unidades WHERE id_unidad = %s", (id_unidad,))
        if not cursor.fetchone():
            print(f"⚠️ Unidad {id_unidad} no encontrada")
            return jsonify({"error": "La unidad indicada no existe"}), 400
        print(f"✅ Unidad válida: {id_unidad}")

        # URL actual del archivo
        url_poliza = garantia_existente[1]
        print(f"Archivo actual: {url_poliza}")

        # Guardar archivo nuevo si se envió
        if archivo and allowed_file(archivo.filename):
            if url_poliza:
                ruta_antigua = os.path.join(app.root_path, url_poliza.lstrip("/").replace("/", os.sep))
                if os.path.exists(ruta_antigua):
                    os.remove(ruta_antigua)
                    print(f"🗑 Archivo antiguo eliminado: {ruta_antigua}")

            ext = archivo.filename.rsplit('.', 1)[1].lower()
            filename = f"{data.get('no_poliza')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            archivo.save(filepath)
            url_poliza = f"/uploads/garantias/{filename}"
            print(f"📁 Archivo nuevo guardado: {url_poliza}")

        # Conversión segura de campos numéricos
        suma_asegurada = float(data.get('suma_asegurada') or 0)
        prima = float(data.get('prima') or 0)

        # Actualización
        query = """
            UPDATE Garantias SET
                id_unidad = %s,
                aseguradora = %s,
                tipo_garantia = %s,
                no_poliza = %s,
                suma_asegurada = %s,
                inicio_vigencia = %s,
                vigencia = %s,
                prima = %s,
                url_poliza = %s
            WHERE id_garantia = %s
        """
        params = (
            id_unidad,
            data.get('aseguradora'),
            data.get('tipo_garantia'),
            data.get('no_poliza'),
            suma_asegurada,
            data.get('inicio_vigencia'),
            data.get('vigencia'),
            prima,
            url_poliza,
            id_garantia
        )
        cursor.execute(query, params)
        conn.commit()

        print(f"✅ Garantía {id_garantia} actualizada correctamente")
        return jsonify({"message": "Garantía actualizada correctamente", "url_poliza": url_poliza}), 200

    except Exception as e:
        conn.rollback()
        import traceback; traceback.print_exc()
        error_message = f"❌ Error al actualizar la garantía: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/garantias/verificar/<int:id_unidad>', methods=['GET'])
def verificar_garantia(id_unidad):
    garantia = Garantias.query.filter_by(id_unidad=id_unidad).first()
    hoy = date.today()
    puede_renovar = False
    datos = None

    if garantia:
        vigencia = garantia.vigencia
        if vigencia:
            # Renovación permitida 1 mes antes o después del vencimiento
            fecha_limite = vigencia - timedelta(days=30)
            if hoy >= fecha_limite:
                puede_renovar = True
        datos = {
            "aseguradora": garantia.aseguradora,
            "tipo_garantia": garantia.tipo_garantia,
            "no_poliza": garantia.no_poliza,
            "suma_asegurada": garantia.suma_asegurada,
            "inicio_vigencia": garantia.inicio_vigencia.isoformat() if garantia.inicio_vigencia else None,
            "vigencia": garantia.vigencia.isoformat() if garantia.vigencia else None,
            "prima": garantia.prima
        }

    return jsonify({
        "existe": bool(garantia),
        "vigente": garantia.vigencia >= hoy if garantia else False,
        "puede_renovar": puede_renovar,
        "datos": datos
    })

@app.route('/api/garantias/<int:id_garantia>', methods=['DELETE'])
def eliminar_garantia(id_garantia):
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    try:
        # Primero obtener la URL del PDF para eliminarlo del servidor
        cursor.execute("SELECT url_poliza FROM Garantias WHERE id_garantia = %s", (id_garantia,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Garantía no encontrada"}), 404

        url_poliza = row[0]
        filepath = os.path.join(app.root_path, url_poliza.lstrip("/"))
        if os.path.exists(filepath):
            os.remove(filepath)

        # Eliminar la garantía
        cursor.execute("DELETE FROM Garantias WHERE id_garantia = %s", (id_garantia,))
        conn.commit()

        return jsonify({"message": "Garantía eliminada correctamente"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar garantía: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# Servir archivos (opcional para ver en navegador)
@app.route('/uploads/garantias/<filename>')
def uploaded_files(filename):
    print(f"Sirviendo archivo: {filename}")
    return send_from_directory('uploads/garantias', filename)

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads', 'garantias')

@app.route('/api/garantias/descargar/<filename>')
def descargar_garantia(filename):
    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
        as_attachment=True  # <-- Esto fuerza que el navegador pregunte dónde guardar
    )

@app.route('/api/descargar/<path:filename>', methods=['GET'])
def descargar_archivo(filename):
    # Carpeta base de uploads
    UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')

    # Construir ruta absoluta del archivo
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Validar que el archivo exista
    if not os.path.isfile(file_path):
        return abort(404, description="Archivo no encontrado")

    # Devolver el archivo para descarga
    # 'as_attachment=True' fuerza la descarga en lugar de abrirlo en el navegador
    return send_from_directory(
        directory=UPLOAD_FOLDER,
        path=filename,
        as_attachment=True
    )





#verificacionwes
# =======================
# VERIFICACIONES - OBTENER DATOS
# =======================
# Configuración de uploads

MESES_ENGOMADO = {
    "primer_semestre": {
        "amarillo": [1, 2],
        "rosa": [2, 3],
        "rojo": [3, 4],
        "verde": [4, 5],
        "azul": [5, 6]
    },
    "segundo_semestre": {
        "amarillo": [7, 8],
        "rosa": [8, 9],
        "rojo": [9, 10],
        "verde": [10, 11],
        "azul": [11, 12]
    }
}


@app.route('/api/unidad/<int:id_unidad>', methods=['GET'])
def obtener_unidad_por_id(id_unidad):
    unidad = Unidades.query.filter_by(id_unidad=id_unidad).first()
    if not unidad:
        return jsonify({"error": "Unidad no encontrada"}), 404

    placa_obj = Placas.query.filter_by(id_unidad=id_unidad).first()
    placa = placa_obj.placa if placa_obj else ""
    
    # Calcular engomado automáticamente
    def calcular_color_por_placa(placa):
        if not placa:
            return ""
        ultimo_digito = placa[-1]
        colores = {"1": "verde", "2": "verde", "3": "rojo", "4": "rojo",
                   "5": "amarillo", "6": "amarillo", "7": "rosa", "8": "rosa",
                   "9": "azul", "0": "azul"}
        return colores.get(ultimo_digito, "")

    engomado = calcular_color_por_placa(placa)

    return jsonify({
        "id_unidad": unidad.id_unidad,
        "marca": unidad.marca,
        "vehiculo": unidad.vehiculo,
        "modelo": unidad.modelo,
        "placa": placa,
        "engomado": engomado
    })

# Helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def calcular_color_por_placa(placa_str):
    """Determinar color de engomado según último dígito de placa."""
    if not placa_str:
        return ""
    ultimo_digito = placa_str[-1]
    colores = {
        "1": "verde", "2": "verde",
        "3": "rojo", "4": "rojo",
        "5": "amarillo", "6": "amarillo",
        "7": "rosa", "8": "rosa",
        "9": "azul", "0": "azul"
    }
    return colores.get(ultimo_digito, "")

# -------------------------------------------------------------------------
# FUNCIÓN: mover vencidos al historial (solo guarda, no resetea)
# -------------------------------------------------------------------------
def mover_y_resetear_verificaciones_vencidas():
    hoy = date.today()
    limite_reset = hoy + timedelta(days=60)

    verificaciones = VerificacionVehicular.query.all()

    for v in verificaciones:
        fecha_siguiente = calcular_siguiente_verificacion(
            v.ultima_verificacion, v.holograma, v.engomado
        )

        # Solo guarda en historial si está dentro del rango, pero no limpia
        if fecha_siguiente and fecha_siguiente <= limite_reset:
            historial = HistorialVerificacionVehicular(
                id_verificacion=v.id_verificacion,
                fecha_cambio=datetime.now(),
                ultima_verificacion=v.ultima_verificacion,
                periodo_1=v.periodo_1,
                periodo_1_real=v.periodo_1_real,
                url_verificacion_1=v.url_verificacion_1,
                periodo_2=v.periodo_2,
                periodo_2_real=v.periodo_2_real,
                url_verificacion_2=v.url_verificacion_2,
                holograma=v.holograma,
                folio_verificacion=v.folio_verificacion,
                engomado=v.engomado,
                usuario="sistema_automatico"
            )
            db.session.add(historial)

    db.session.commit()
    
from flask import current_app, send_from_directory

# Servir archivos desde /uploads
@app.route('/uploads/<path:filename>')
def serve_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/api/verificaciones', methods=['POST'])
def crear_verificacion():
    UPLOAD_FOLDER = 'uploads/verificaciones'
    HISTORIAL_FOLDER = 'uploads/historial_verificaciones'

    ruta_upload_abs = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    ruta_historial_abs = os.path.join(current_app.root_path, HISTORIAL_FOLDER)
    os.makedirs(ruta_upload_abs, exist_ok=True)
    os.makedirs(ruta_historial_abs, exist_ok=True)

    data = request.form
    archivo = request.files.get('archivo')

    print("=== DATA recibida ===")
    print(data)
    print("Archivo recibido:", archivo.filename if archivo else "No hay archivo")

    if not archivo or archivo.filename == '':
        return jsonify({"error": "Debe subir un archivo PDF"}), 400
    if not allowed_file(archivo.filename):
        return jsonify({"error": "Solo se permiten archivos PDF"}), 400

    unidad = Unidades.query.filter_by(id_unidad=data['id_unidad']).first()
    if not unidad:
        return jsonify({"error": "La unidad indicada no existe"}), 400
    print("Unidad encontrada:", unidad)

    placa_str = unidad.placa.placa if unidad.placa else ""
    engomado = calcular_color_por_placa(placa_str)
    holograma = data.get('holograma', '')

    if 'periodo_1_real' in data:
        periodo = '1'
    elif 'periodo_2_real' in data:
        periodo = '2'
    else:
        return jsonify({"error": "No se encontró periodo válido."}), 400

    fecha_sugerida = datetime.strptime(data[f'periodo_{periodo}'], "%Y-%m-%d").date()
    fecha_real = datetime.strptime(data[f'periodo_{periodo}_real'], "%Y-%m-%d").date()
    print(f"Periodo: {periodo}, Fecha sugerida: {fecha_sugerida}, Fecha real: {fecha_real}")

    filename = secure_filename(f"{data['id_unidad']}_{periodo}_{date.today()}.pdf")
    ruta_guardado_abs = os.path.join(ruta_upload_abs, filename)
    archivo.save(ruta_guardado_abs)
    ruta_pdf = os.path.join(UPLOAD_FOLDER, filename).replace("\\", "/")
    print(f"Archivo guardado en: {ruta_guardado_abs}")
    print(f"Ruta relativa para DB/frontend: {ruta_pdf}")

    existing = VerificacionVehicular.query.filter_by(id_unidad=data['id_unidad']).first()
    print("Verificación existente:", existing)

    try:
        def mover_a_historial(ruta_relativa):
            if not ruta_relativa or ruta_relativa == ruta_pdf:
                print(f"No se mueve (nuevo o vacío): {ruta_relativa}")
                return ruta_relativa
            ruta_abs = os.path.join(current_app.root_path, ruta_relativa.lstrip("/").replace("/", os.sep))
            if os.path.exists(ruta_abs):
                nombre = os.path.basename(ruta_abs)
                nueva_ruta_abs = os.path.join(ruta_historial_abs, nombre)
                shutil.move(ruta_abs, nueva_ruta_abs)
                print(f"Archivo movido a historial: {nueva_ruta_abs}")
                return os.path.join(HISTORIAL_FOLDER, nombre).replace("\\", "/")
            print(f"Archivo no encontrado para mover: {ruta_abs}")
            return ruta_relativa

        if existing and existing.ultima_verificacion:
            anio_existente = existing.ultima_verificacion.year
            anio_nuevo = fecha_real.year
            print(f"Año existente: {anio_existente}, Año nuevo: {anio_nuevo}")

            if anio_nuevo > anio_existente:
                url_v1 = mover_a_historial(existing.url_verificacion_1)
                url_v2 = mover_a_historial(existing.url_verificacion_2)

                historial = HistorialVerificacionVehicular(
                    id_verificacion=existing.id_verificacion,
                    id_unidad=existing.id_unidad,
                    fecha_cambio=datetime.now(),
                    ultima_verificacion=existing.ultima_verificacion,
                    periodo_1=existing.periodo_1,
                    periodo_1_real=existing.periodo_1_real,
                    url_verificacion_1=url_v1,
                    periodo_2=existing.periodo_2,
                    periodo_2_real=existing.periodo_2_real,
                    url_verificacion_2=url_v2,
                    holograma=existing.holograma,
                    folio_verificacion=existing.folio_verificacion,
                    engomado=existing.engomado,
                    usuario=data.get('usuario', 'sistema')
                )
                db.session.add(historial)
                print("Historial agregado a la sesión")

                # Resetear campos antiguos
                existing.periodo_1 = None
                existing.periodo_1_real = None
                existing.url_verificacion_1 = None
                existing.periodo_2 = None
                existing.periodo_2_real = None
                existing.url_verificacion_2 = None
                existing.ultima_verificacion = None
                existing.holograma = None
                existing.folio_verificacion = None
                existing.engomado = None
                print("Campos antiguos reseteados")

        if existing:
            if periodo == '1':
                existing.periodo_1 = fecha_sugerida
                existing.periodo_1_real = fecha_real
                existing.url_verificacion_1 = ruta_pdf
            else:
                existing.periodo_2 = fecha_sugerida
                existing.periodo_2_real = fecha_real
                existing.url_verificacion_2 = ruta_pdf

            existing.ultima_verificacion = fecha_real
            existing.holograma = holograma
            existing.folio_verificacion = data.get('folio_verificacion', '')
            existing.engomado = engomado
            print("Verificación existente actualizada con nuevo PDF")
        else:
            nueva = VerificacionVehicular(
                id_unidad=data['id_unidad'],
                ultima_verificacion=fecha_real,
                periodo_1=fecha_sugerida if periodo == '1' else None,
                periodo_1_real=fecha_real if periodo == '1' else None,
                periodo_2=fecha_sugerida if periodo == '2' else None,
                periodo_2_real=fecha_real if periodo == '2' else None,
                url_verificacion_1=ruta_pdf if periodo == '1' else None,
                url_verificacion_2=ruta_pdf if periodo == '2' else None,
                holograma=holograma,
                folio_verificacion=data.get('folio_verificacion', ''),
                engomado=engomado
            )
            db.session.add(nueva)
            print("Nueva verificación agregada a la sesión")

        db.session.commit()
        print("Commit realizado correctamente")
        return jsonify({"message": f"Verificación del periodo {periodo} registrada correctamente."}), 201

    except Exception as e:
        db.session.rollback()
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/calendario', methods=['GET'])
def obtener_calendario():
    calendario_dict = {}
    for semestre, colores_dict in MESES_ENGOMADO.items():
        for color, meses in colores_dict.items():
            for mes in meses:
                calendario_dict.setdefault(mes, []).append(color)
    
    # Convertir a lista de objetos
    calendario = [{"mes": mes, "color": colores} for mes, colores in calendario_dict.items()]
    return jsonify(calendario)

@app.route('/api/calendario', methods=['POST'])
def actualizar_calendario():
    data = request.json  # [{"mes":3,"color":["verde"]}, ...]
    # Aquí actualizarías tu DB o estructura interna
    for item in data:
        mes = item["mes"]
        colores = item["color"]
        # Actualizar MESES_ENGOMADO o DB según tu lógica
    return jsonify({"status": "ok"})


#--------------------------------------------------------------------------------------------

#calculo de verificaciones

def calcular_siguiente_verificacion(fecha_real, holograma, engomado):
    if not fecha_real:
        return None

    # Holograma "00" → 2 años después
    if holograma == "00":
        return fecha_real.replace(year=fecha_real.year + 2)

    # Holograma "0" → 6 meses después
    if holograma == "0":
        mes_siguiente = fecha_real.month + 6
        año = fecha_real.year
        if mes_siguiente > 12:
            mes_siguiente -= 12
            año += 1
        ultimo_dia = calendar.monthrange(año, mes_siguiente)[1]
        return fecha_real.replace(year=año, month=mes_siguiente, day=ultimo_dia)

    # Hologramas normales según engomado y semestre
    MESES_ENGOMADO = {
        "primer_semestre": {"amarillo":[1,2],"rosa":[2,3],"rojo":[3,4],"verde":[4,5],"azul":[5,6]},
        "segundo_semestre": {"amarillo":[7,8],"rosa":[8,9],"rojo":[9,10],"verde":[10,11],"azul":[11,12]}
    }

    mes_actual = fecha_real.month
    semestre = "primer_semestre" if mes_actual <= 6 else "segundo_semestre"
    meses_posibles = MESES_ENGOMADO[semestre].get(engomado.lower(), [])

    if not meses_posibles:
        # fallback: 6 meses después
        nueva_fecha = fecha_real + timedelta(days=182)
        return nueva_fecha

    # Tomar primer mes >= mes_actual
    for m in meses_posibles:
        if m >= mes_actual:
            mes_siguiente = m
            break
    else:
        # Si ya pasaron todos los meses del semestre → primer mes del semestre siguiente
        semestre_siguiente = "segundo_semestre" if semestre == "primer_semestre" else "primer_semestre"
        mes_siguiente = MESES_ENGOMADO[semestre_siguiente].get(engomado.lower(), [mes_actual + 6])[0]

    # Ajustar año si se pasa de diciembre
    año = fecha_real.year + (1 if mes_siguiente < mes_actual else 0)
    ultimo_dia = calendar.monthrange(año, mes_siguiente)[1]

    return fecha_real.replace(year=año, month=mes_siguiente, day=ultimo_dia)


# Endpoint: obtener verificación por placa
@app.route('/api/verificacion-placa/<string:placa>', methods=['GET'])
def obtener_verificacion_placa(placa):
    placa_obj = Placas.query.filter_by(placa=placa).first()
    if not placa_obj:
        return jsonify({"error": "Placa no encontrada"}), 404

    unidad = placa_obj.unidad
    verificacion = VerificacionVehicular.query.filter_by(id_unidad=unidad.id_unidad).first()
    if not verificacion:
        return jsonify({"error": "No hay verificaciones registradas"}), 404

    # Determinar la fecha base para cálculo de próxima
    fecha_base = verificacion.periodo_2_real or verificacion.periodo_1_real

    proxima = None
    if fecha_base:
        proxima = calcular_siguiente_verificacion(fecha_base, verificacion.holograma, verificacion.engomado)

    return jsonify({
        "unidad": f"{unidad.marca} {unidad.vehiculo}",
        "placa": placa_obj.placa,
        "holograma": verificacion.holograma,
        "engomado": verificacion.engomado,
        "vigente": verificacion.periodo_1_real,
        "proxima": proxima,
        "anterior": verificacion.periodo_1_real,
        "url_verificacion_1": verificacion.url_verificacion_1,
        "url_verificacion_2": verificacion.url_verificacion_2
    })

@app.route('/api/verificaciones', methods=['GET'])
def obtener_verificaciones():
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT 
                V.id_verificacion,
                V.id_unidad,
                U.marca,
                U.vehiculo,
                U.modelo,
                P.placa,
                V.ultima_verificacion,
                V.periodo_1,
                V.periodo_1_real,
                V.url_verificacion_1,
                V.periodo_2,
                V.periodo_2_real,
                V.url_verificacion_2,
                V.holograma,
                V.folio_verificacion,
                V.engomado
            FROM verificacionvehicular V
            JOIN Unidades U ON V.id_unidad = U.id_unidad
            LEFT JOIN Placas P ON P.id_unidad = U.id_unidad
            ORDER BY V.id_verificacion DESC;
        """
        cursor.execute(query)
        filas = cursor.fetchall()
        columnas = [desc[0] for desc in cursor.description]

        resultados = []

        for fila in filas:
            fila_dict = dict(zip(columnas, fila))

            # Convertir fechas a string
            for campo in ['ultima_verificacion','periodo_1','periodo_1_real','periodo_2','periodo_2_real']:
                if fila_dict[campo]:
                    fila_dict[campo] = fila_dict[campo].strftime('%Y-%m-%d')

            # Calcular próxima verificación según engomado y periodo real
            fecha_base_str = fila_dict.get('periodo_2_real') or fila_dict.get('periodo_1_real')
            if fecha_base_str:
                fecha_base = datetime.strptime(fecha_base_str, "%Y-%m-%d").date()
                engomado = fila_dict.get('engomado', '')
                fila_dict['proxima_verificacion'] = calcular_siguiente_verificacion(fecha_base, fila_dict.get('holograma', ''), fila_dict.get('engomado', '')).strftime("%Y-%m-%d")
            else:
                fila_dict['proxima_verificacion'] = None

            resultados.append(fila_dict)

        return jsonify(resultados), 200

    except Exception as e:
        import traceback
        print("Error al obtener verificaciones:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==============================================================
# ENDPOINT: Obtener historial de verificaciones vehiculares
# ==============================================================

@app.route('/api/historial_verificaciones', methods=['GET'])
def obtener_historial_verificaciones():
    try:
        # Trae historial con unidad y placa relacionada
        historial = (
            db.session.query(HistorialVerificacionVehicular, Unidades, Placas)
            .join(Unidades, HistorialVerificacionVehicular.id_unidad == Unidades.id_unidad)
            .outerjoin(Placas, Placas.id_unidad == Unidades.id_unidad)
            .order_by(HistorialVerificacionVehicular.fecha_cambio.desc())
            .all()
        )

        resultado = []
        for registro, unidad, placa in historial:
            # Debug: imprime para verificar los datos
            print(f"Registro: {registro}, Unidad: {unidad}, Placa: {placa}")

            nombre_unidad = f"{unidad.marca} {unidad.vehiculo} {unidad.modelo}"

            resultado.append({
                "id_historial": registro.id_historial,
                "id_verificacion": registro.id_verificacion,
                "id_unidad": registro.id_unidad,
                "fecha_cambio": registro.fecha_cambio.strftime("%Y-%m-%d %H:%M:%S"),
                "ultima_verificacion": registro.ultima_verificacion.strftime("%Y-%m-%d") if registro.ultima_verificacion else None,
                "periodo_1": registro.periodo_1.strftime("%Y-%m-%d") if registro.periodo_1 else None,
                "periodo_1_real": registro.periodo_1_real.strftime("%Y-%m-%d") if registro.periodo_1_real else None,
                "url_verificacion_1": registro.url_verificacion_1,
                "periodo_2": registro.periodo_2.strftime("%Y-%m-%d") if registro.periodo_2 else None,
                "periodo_2_real": registro.periodo_2_real.strftime("%Y-%m-%d") if registro.periodo_2_real else None,
                "url_verificacion_2": registro.url_verificacion_2,
                "holograma": registro.holograma,
                "folio_verificacion": registro.folio_verificacion,
                "engomado": registro.engomado,
                "usuario": registro.usuario or "sistema",
                "unidad": {
                    "id_unidad": unidad.id_unidad,
                    "nombre": nombre_unidad,
                    "placa": placa.placa if placa else None
                }
            })

        return jsonify(resultado), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Error al obtener el historial de verificaciones.",
            "detalles": str(e)
        }), 500



# =======================

@app.route('/solicitudes/chofer/<int:id_chofer>', methods=['GET'])
def solicitudes_chofer(id_chofer):
    # Trae todas las solicitudes del chofer
    solicitudes = SolicitudFalla.query.filter_by(id_chofer=id_chofer).all()
    resultado = []
    for s in solicitudes:
        # Verifica si ya hay falla asociada
        falla_existente = FallaMecanica.query.filter_by(
            id_unidad=s.id_unidad,
            id_pieza=s.id_pieza,
            tipo_servicio=s.tipo_servicio
        ).first()
        resultado.append({
            "id_solicitud": s.id_solicitud,
            "unidad": s.id_unidad,
            "pieza": s.id_pieza,
            "marca": s.id_marca,
            "tipo_servicio": s.tipo_servicio,
            "descripcion": s.descripcion,
            "estado": s.estado,
            "completada": True if falla_existente else False
        })
    return jsonify(resultado)


# -------------------------------
# Crear solicitud de falla (CHOFER)
# -------------------------------
@app.route('/solicitudes', methods=['POST'])
def crear_solicitud():
    data = request.json
    nueva = SolicitudFalla(
        id_unidad = data['id_unidad'],
        id_pieza = data['id_pieza'],
        id_marca = data.get('id_marca'),
        tipo_servicio = data['tipo_servicio'],
        descripcion = data.get('descripcion', ''),
        id_chofer = data['id_chofer']
    )
    db.session.add(nueva)
    db.session.commit()
    return jsonify({"msg":"Solicitud creada", "id_solicitud": nueva.id_solicitud}), 201

# -------------------------------
# Listar solicitudes pendientes (ADMIN)

# -------------------------------
@app.route('/solicitudes', methods=['GET'])
def listar_todas_solicitudes():
    # Trae todas las solicitudes, ordenadas de más recientes a más antiguas
    solicitudes = SolicitudFalla.query.order_by(SolicitudFalla.fecha_solicitud.desc()).all()
    resultado = []
    for s in solicitudes:
        resultado.append({
            "id_solicitud": s.id_solicitud,
            "unidad": s.id_unidad,
            "pieza": s.id_pieza,
            "marca": s.id_marca,
            "tipo_servicio": s.tipo_servicio,
            "descripcion": s.descripcion,
            "estado": s.estado,  # añade estado para que se vea aprobado/pendiente/rechazado
            "id_chofer": s.id_chofer,
            "fecha_solicitud": s.fecha_solicitud.isoformat()
        })
    return jsonify(resultado)

# -------------------------------
# Aprobar o rechazar solicitud (ADMIN)
# -------------------------------
@app.route('/solicitudes/<int:id_solicitud>/aprobar', methods=['POST'])
def aprobar_solicitud(id_solicitud):
    data = request.json
    solicitud = SolicitudFalla.query.get_or_404(id_solicitud)

    # Cambiar estado
    solicitud.estado = 'aprobada' if data.get('aprobar') else 'rechazada'
    db.session.commit()

    return jsonify({"msg": f"Solicitud {'aprobada' if solicitud.estado=='aprobada' else 'rechazada'}"})

# -------------------------------
# Registrar falla (ADMIN)
# -------------------------------    

# Carpeta para los comprobantes de fallas
UPLOAD_FOLDER_FALLA = 'uploads/comprobantes_falla'
os.makedirs(UPLOAD_FOLDER_FALLA, exist_ok=True)
ALLOWED_EXTENSIONS_FALLA = {'pdf'}
app.config['UPLOAD_FOLDER_FALLA'] = UPLOAD_FOLDER_FALLA

def allowed_file_falla(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_FALLA

@app.route('/fallas', methods=['POST'])
def crear_falla():
    data = request.form
    archivo = request.files.get('comprobante')  # nombre del archivo en FormData

    id_solicitud = data.get('id_solicitud')
    if not id_solicitud:
        return jsonify({"error": "Falta id_solicitud"}), 400

    solicitud = SolicitudFalla.query.get_or_404(id_solicitud)
    if solicitud.estado != 'aprobada':
        return jsonify({"error": "La solicitud no ha sido aprobada"}), 400

    url_comprobante = None
    if archivo:
        if archivo.filename.lower().endswith('.pdf'):
            filename = f"falla_{solicitud.id_solicitud}.pdf"
            carpeta = os.path.join(app.root_path, 'uploads', 'fallasmecanicas')
            os.makedirs(carpeta, exist_ok=True)
            filepath = os.path.join(carpeta, filename)
            archivo.save(filepath)
            url_comprobante = f"uploads/fallasmecanicas/{filename}"
        else:
            return jsonify({"error": "Solo se permiten archivos PDF"}), 400

    # Aquí imprimimos para depuración
    print("URL del comprobante:", url_comprobante)

    aplica_poliza_str = data.get('aplica_poliza', 'false')
    aplica_poliza = aplica_poliza_str.lower() in ['true', '1', 'on']

    falla = FallaMecanica(
        id_unidad=solicitud.id_unidad,
        id_pieza=solicitud.id_pieza,
        fecha_falla=solicitud.fecha_solicitud,
        id_marca=solicitud.id_marca,
        tipo_servicio=solicitud.tipo_servicio,
        descripcion=solicitud.descripcion,
        id_lugar=data.get('id_lugar'),
        proveedor=data.get('proveedor'),
        tipo_pago=data.get('tipo_pago'),
        costo=data.get('costo'),
        tiempo_uso_pieza=data.get('tiempo_uso_pieza'),
        aplica_poliza=aplica_poliza,
        observaciones=data.get('observaciones'),
        url_comprobante=url_comprobante
    )

    db.session.add(falla)
    db.session.commit()

    # También podemos devolverlo en la respuesta para confirmar
    return jsonify({
        "msg": "Falla registrada con éxito",
        "id_falla": falla.id_falla,
        "url_comprobante": falla.url_comprobante
    })



@app.route('/falla_admin', methods=['POST'])
def registrar_falla_admin():
    try:
        data = request.form
        # Obtener datos del formulario
        id_unidad = int(data.get('id_unidad'))
        id_pieza = int(data.get('id_pieza'))
        id_marca = int(data.get('id_marca')) if data.get('id_marca') else None
        id_lugar = int(data.get('id_lugar')) if data.get('id_lugar') else None
        proveedor = data.get('proveedor')
        tipo_pago = data.get('tipo_pago')
        costo = float(data.get('costo', 0))
        tiempo_uso_pieza = int(data.get('tiempo_uso_pieza', 0)) if data.get('tiempo_uso_pieza') else None
        observaciones = data.get('observaciones')
        aplica_poliza = data.get('aplica_poliza') == 'true'
        descripcion = data.get('descripcion')
        tipo_servicio = data.get('tipo_servicio')
        comprobante = request.files.get('comprobante')

        # Guardar archivo si existe
        filename = None
        if comprobante:
            filename = secure_filename(comprobante.filename)
            path = os.path.join('static/comprobantes_fallas', filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            comprobante.save(path)

        # Crear registro usando SQLAlchemy
        nueva_falla = FallaMecanica(
            id_unidad=id_unidad,
            id_pieza=id_pieza,
            id_marca=id_marca,
            tipo_servicio=tipo_servicio,
            descripcion=descripcion,
            id_lugar=id_lugar,
            proveedor=proveedor,
            tipo_pago=tipo_pago,
            costo=costo,
            tiempo_uso_pieza=tiempo_uso_pieza,
            observaciones=observaciones,
            aplica_poliza=aplica_poliza,
            url_comprobante=f'static/comprobantes_fallas/{filename}' if filename else None
        )

        db.session.add(nueva_falla)
        db.session.commit()

        return jsonify({"message": "Falla registrada por administrador correctamente", "falla": {
            "id_falla": nueva_falla.id_falla,
            "id_unidad": nueva_falla.id_unidad,
            "id_pieza": nueva_falla.id_pieza,
            "id_marca": nueva_falla.id_marca,
            "tipo_servicio": nueva_falla.tipo_servicio,
            "descripcion": nueva_falla.descripcion,
            "id_lugar": nueva_falla.id_lugar,
            "proveedor": nueva_falla.proveedor,
            "tipo_pago": nueva_falla.tipo_pago,
            "costo": float(nueva_falla.costo or 0),
            "tiempo_uso_pieza": nueva_falla.tiempo_uso_pieza,
            "aplica_poliza": nueva_falla.aplica_poliza,
            "observaciones": nueva_falla.observaciones,
            "url_comprobante": nueva_falla.url_comprobante
        }}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400




@app.route('/fallas/<int:id_falla>', methods=['PUT'])
def actualizar_falla(id_falla):
    falla = FallaMecanica.query.get_or_404(id_falla)
    data = request.form
    archivo = request.files.get('comprobante')

    # Actualizar todos los campos excepto la fecha
    falla.descripcion = data.get('descripcion', falla.descripcion)
    falla.tipo_servicio = data.get('tipo_servicio', falla.tipo_servicio)
    falla.id_unidad = int(data.get('id_unidad', falla.id_unidad))
    falla.id_pieza = int(data.get('id_pieza', falla.id_pieza))
    falla.id_marca = int(data.get('id_marca', falla.id_marca))
    falla.id_lugar = int(data.get('id_lugar', falla.id_lugar))
    falla.proveedor = data.get('proveedor', falla.proveedor)
    falla.tipo_pago = data.get('tipo_pago', falla.tipo_pago)
    falla.costo = data.get('costo', falla.costo)
    falla.tiempo_uso_pieza = data.get('tiempo_uso_pieza', falla.tiempo_uso_pieza)
    falla.observaciones = data.get('observaciones', falla.observaciones)

    aplica_poliza_str = data.get('aplica_poliza')
    if aplica_poliza_str is not None:
        falla.aplica_poliza = aplica_poliza_str.lower() in ['true', '1', 'on']

    # Guardar archivo PDF si existe
    if archivo:
        if archivo.filename.lower().endswith('.pdf'):
            filename = f"falla_{falla.id_falla}.pdf"
            carpeta = os.path.join(app.root_path, 'uploads', 'fallasmecanicas')
            os.makedirs(carpeta, exist_ok=True)
            archivo.save(os.path.join(carpeta, filename))
            falla.url_comprobante = f"uploads/fallasmecanicas/{filename}"
        else:
            return jsonify({"error": "Solo se permiten archivos PDF"}), 400

    try:
        db.session.commit()

        # Obtener nombres descriptivos
        unidad = Unidades.query.get(falla.id_unidad)
        pieza = Piezas.query.get(falla.id_pieza)
        marca = MarcasPiezas.query.get(falla.id_marca)
        lugar = LugarReparacion.query.get(falla.id_lugar)

        return jsonify({
            "msg": "Falla actualizada con éxito",
            "falla": {
                "id_falla": falla.id_falla,
                "descripcion": falla.descripcion,
                "tipo_servicio": falla.tipo_servicio,
                "unidad": unidad.vehiculo if unidad else "No especificada",
                "pieza": pieza.nombre_pieza if pieza else "No especificada",
                "marca": marca.nombre_marca if marca else "No especificada",
                "id_lugar": falla.id_lugar,
                "lugar_reparacion": lugar.nombre_lugar if lugar else "No especificado",
                "proveedor": falla.proveedor,
                "tipo_pago": falla.tipo_pago,
                "costo": str(falla.costo),
                "tiempo_uso_pieza": falla.tiempo_uso_pieza,
                "aplica_poliza": falla.aplica_poliza,
                "observaciones": falla.observaciones,
                "fecha_falla": falla.fecha_falla.isoformat() if falla.fecha_falla else None,
                "url_comprobante": falla.url_comprobante
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# -------------------------------
# Obtener detalle de una falla
# -------------------------------
@app.route('/fallas/<int:id_falla>', methods=['GET'])
def detalle_falla(id_falla):
    falla = FallaMecanica.query.get_or_404(id_falla)
    return jsonify({
        "id_falla": falla.id_falla,
        "unidad": falla.id_unidad,
        "pieza": falla.id_pieza,
        "marca": falla.id_marca,
        "tipo_servicio": falla.tipo_servicio,
        "descripcion": falla.descripcion,
        "id_lugar": falla.id_lugar,
        "proveedor": falla.proveedor,
        "tipo_pago": falla.tipo_pago,
        "costo": str(falla.costo),
        "tiempo_uso_pieza": falla.tiempo_uso_pieza,
        "aplica_poliza": falla.aplica_poliza,
        "observaciones": falla.observaciones,
        "url_comprobante": falla.url_comprobante
    })

# Listar unidades
@app.route('/unidades', methods=['GET'])
def listar_unidades():
    unidades = Unidades.query.all()
    return jsonify([
        {"id_unidad": u.id_unidad, "vehiculo": u.vehiculo, "marca": u.marca, "modelo": u.modelo}
        for u in unidades
    ])

# Obtener unidad por ID
@app.route('/unidades/<int:id_unidad>', methods=['GET'])
def obtener_unidad(id_unidad):
    unidad = Unidades.query.get(id_unidad)
    if not unidad:
        return jsonify({"error": "Unidad no encontrada"}), 404
    return jsonify({
        "id_unidad": unidad.id_unidad,
        "vehiculo": unidad.vehiculo,
        "marca": unidad.marca,
        "modelo": unidad.modelo
    })

# Listar piezas
@app.route('/piezas', methods=['GET'])
def listar_piezas():
    piezas = Piezas.query.all()
    return jsonify([
        {"id_pieza": p.id_pieza, "nombre_pieza": p.nombre_pieza} for p in piezas
    ])

# Listar marcas
@app.route('/marcas', methods=['GET'])
def listar_marcas():
    marcas = MarcasPiezas.query.all()
    return jsonify([
        {"id_marca": m.id_marca, "nombre_marca": m.nombre_marca} for m in marcas
    ])

# Listar lugares de reparación
@app.route('/lugares', methods=['GET'])
def listar_lugares():
    lugares = LugarReparacion.query.all()
    return jsonify([
        {"id_lugar": l.id_lugar, "nombre_lugar": l.nombre_lugar} for l in lugares
    ])

# -------------------------------
# Listar fallas mecánicas (con nombres descriptivos)
# -------------------------------
@app.route('/fallas', methods=['GET'])
def listar_fallas():
    fallas = FallaMecanica.query.all()
    resultado = []

    for f in fallas:
        unidad = Unidades.query.get(f.id_unidad)
        pieza = Piezas.query.get(f.id_pieza)
        marca = MarcasPiezas.query.get(f.id_marca)
        lugar = LugarReparacion.query.get(f.id_lugar)

        resultado.append({
            "id_falla": f.id_falla,
            # IDs para selects
            "id_unidad": f.id_unidad,
            "id_pieza": f.id_pieza,
            "id_marca": f.id_marca,
            "id_lugar": f.id_lugar,

            # Nombres descriptivos
            "unidad": unidad.vehiculo if unidad else "No especificada",
            "pieza": pieza.nombre_pieza if pieza else "No especificada",
            "marca": marca.nombre_marca if marca else "No especificada",
            "lugar_reparacion": lugar.nombre_lugar if lugar else "No especificado",

            # Datos de la falla
            "tipo_servicio": f.tipo_servicio,
            "descripcion": f.descripcion,
            "proveedor": f.proveedor,
            "tipo_pago": f.tipo_pago,
            "costo": str(f.costo) if f.costo else "0.00",
            "tiempo_uso_pieza": f.tiempo_uso_pieza,
            "aplica_poliza": f.aplica_poliza,
            "observaciones": f.observaciones,
            "url_comprobante": f.url_comprobante,
            "fecha_falla": f.fecha_falla.isoformat() if f.fecha_falla else None
        })

    return jsonify(resultado)




@app.route('/fallas/<int:id_falla>', methods=['DELETE'])
def eliminar_falla(id_falla):
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    try:
        # Primero obtener la URL del comprobante para eliminarlo del servidor
        cursor.execute("SELECT url_comprobante FROM fallasmecanicas WHERE id_falla = %s", (id_falla,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Falla no encontrada"}), 404

        url_comprobante = row[0]
        if url_comprobante:
            filepath = os.path.join(app.root_path, url_comprobante.lstrip("/"))
            if os.path.exists(filepath):
                os.remove(filepath)

        # Eliminar el registro de la falla
        cursor.execute("DELETE FROM fallasmecanicas WHERE id_falla = %s", (id_falla,))
        conn.commit()

        return jsonify({"message": "Falla y comprobante eliminados correctamente"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar falla: {e}")  # <- Esto mostrará el detalle en consola

        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()



@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    # Carpeta 'uploads' absoluta
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')  # Ajusta si tu carpeta está en otro lugar

    # filename puede ser 'fallasmecanicas/falla_24.pdf'
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)


#========================================================================================================
#Placas
#========================================================================================================

@app.route('/placas', methods=['GET'])
def get_placas():
    try:
        id_unidad = request.args.get('id_unidad', None, type=int)

        # Si se está consultando por unidad (verificación)
        if id_unidad:
            placas = Placas.query.filter_by(id_unidad=id_unidad).all()
            return jsonify({
                'placas': [p.to_dict() for p in placas]
            })

        # Si no se pasa id_unidad, aplicar paginación normal (vista general)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        placas_query = Placas.query.paginate(page=page, per_page=per_page)

        placas = [p.to_dict() for p in placas_query.items]

        return jsonify({
            'total': placas_query.total,
            'page': page,
            'per_page': per_page,
            'placas': placas,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ---------------------------
# Endpoint para probar envío de correo manual
# ---------------------------
@app.route("/test-email", methods=["GET"])
def test_email():
    # Cambia este correo por el que quieras usar para la prueba
    correo_destino = "imanolcruz588@gmail.com"

    try:
        msg = Message(
            subject="✅ Prueba de alerta - Sistema Placas",
            recipients=[correo_destino],
            body="Este es un correo de prueba desde el sistema de placas. Si lo recibes, el envío está funcionando correctamente."
        )
        mail.send(msg)
        return jsonify({"status": "ok", "message": f"Correo enviado a {correo_destino}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/reseteo_manual", methods=["POST"])
def reseteo_manual():
    try:
        reseteo_y_alertas()
        return jsonify({"message": "Reseteo ejecutado correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ---------------------------
# Función para enviar alertas semanales
# ---------------------------

def enviar_alertas_semanales():
    placas_alerta = Placas.query.filter_by(requiere_renovacion=True).all()
    if not placas_alerta:
        return

    for p in placas_alerta:
        # Correo de prueba
        correo_prueba = "imanolcruz588@gmail.com"

        msg = Message(
            subject=f"Placa próxima a vencer: {p.placa or 'Sin placa'}",
            recipients=[correo_prueba],
            body=f"La placa de la unidad {p.id_unidad} vence el {p.fecha_vigencia}. Favor de renovarla."
        )
        mail.send(msg)

        mail.send(msg)


def guardar_archivo_unico(file, carpeta='placas'):
    """Guarda un archivo con nombre único en la carpeta especificada y devuelve la ruta relativa"""
    UPLOAD_DIR = f'uploads/{carpeta}/'
    ext = os.path.splitext(file.filename)[1]  # mantiene la extensión
    nombre_unico = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, nombre_unico)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file.save(path)
    # Retornar ruta con barras normales
    return path.replace("\\", "/")


@app.route("/placas/registrar", methods=["POST"])
def registrar_o_actualizar_placa():
    UPLOAD_DIR = 'uploads/placas/'
    HISTORIAL_DIR = 'uploads/historial_placas/'
    USUARIO_SISTEMA = "sistema"
    data = request.form
    id_unidad = data.get("id_unidad")
    nueva_placa = data.get("placa")
    folio = data.get("folio")
    fecha_expedicion = data.get("fecha_expedicion")
    fecha_vigencia = data.get("fecha_vigencia")

    if not id_unidad or not nueva_placa or not fecha_vigencia:
        return jsonify({"error": "Unidad, placa y fecha de vigencia son obligatorios"}), 400

    hoy = date.today()
    placa_activa = Placas.query.filter_by(id_unidad=id_unidad).first()

    if placa_activa:
        # Revisar días restantes
        dias_restantes = (placa_activa.fecha_vigencia - hoy).days if placa_activa.fecha_vigencia else 0
        if dias_restantes > 180:
            return jsonify({
                "error": f"No se puede registrar nueva placa. Vigencia actual hasta {placa_activa.fecha_vigencia}"
            }), 400

        # Mover archivos al historial
        for field_name in ["url_placa_frontal", "url_placa_trasera"]:
            old_path = getattr(placa_activa, field_name)
            if old_path and os.path.exists(old_path):
                os.makedirs(HISTORIAL_DIR, exist_ok=True)
                ext = old_path.rsplit('.', 1)[1].lower()
                nuevo_nombre = f"{uuid.uuid4()}.{ext}"
                dst = os.path.join(HISTORIAL_DIR, nuevo_nombre)
                shutil.move(old_path, dst)
                # Guardar ruta en historial
                setattr(placa_activa, field_name, dst.replace("\\", "/"))

        # Guardar historial
        historial = HistorialPlaca(
            id_placa=placa_activa.id_placa,
            id_unidad=placa_activa.id_unidad,
            folio=placa_activa.folio,
            placa=placa_activa.placa,
            fecha_expedicion=placa_activa.fecha_expedicion,
            fecha_vigencia=placa_activa.fecha_vigencia,
            url_placa_frontal=placa_activa.url_placa_frontal,
            url_placa_trasera=placa_activa.url_placa_trasera,
            usuario=USUARIO_SISTEMA
        )
        db.session.add(historial)

        # Actualizar la misma fila con nueva info
        placa_activa.placa = nueva_placa
        placa_activa.folio = folio
        placa_activa.fecha_expedicion = fecha_expedicion
        placa_activa.fecha_vigencia = fecha_vigencia

        # Archivos PDF con nombre único
        if 'url_placa_frontal' in request.files:
            archivo = request.files['url_placa_frontal']
            placa_activa.url_placa_frontal = guardar_archivo_unico(archivo, 'placas')
        if 'url_placa_trasera' in request.files:
            archivo = request.files['url_placa_trasera']
            placa_activa.url_placa_trasera = guardar_archivo_unico(archivo, 'placas')

        placa_activa.requiere_renovacion = False
        db.session.commit()
        return jsonify({"message": "Placa actualizada correctamente"}), 200

    # Si no existe, crear nuevo registro
    nueva = Placas(
        id_unidad=id_unidad,
        placa=nueva_placa,
        folio=folio,
        fecha_expedicion=fecha_expedicion,
        fecha_vigencia=fecha_vigencia,
        requiere_renovacion=False
    )

    # Archivos PDF con nombre único
    if 'url_placa_frontal' in request.files:
        archivo = request.files['url_placa_frontal']
        nueva.url_placa_frontal = guardar_archivo_unico(archivo, 'placas')
    if 'url_placa_trasera' in request.files:
        archivo = request.files['url_placa_trasera']
        nueva.url_placa_trasera = guardar_archivo_unico(archivo, 'placas')

    db.session.add(nueva)
    db.session.commit()
    return jsonify({"message": "Placa registrada correctamente"}), 200

# ---------------------------
# Función de reseteo y marcación
# ---------------------------
def reseteo_y_alertas():
    UPLOAD_DIR = 'uploads/placas/'
    HISTORIAL_DIR = 'uploads/historial_placas/'
    hoy = date.today()
    fecha_preaviso = hoy + timedelta(days=180)
    usuario = "sistema"

    # 1️⃣ Marcar placas próximas a vencer
    placas_preaviso = Placas.query.filter(
        Placas.fecha_vigencia <= fecha_preaviso,
        Placas.requiere_renovacion == False
    ).all()

    for p in placas_preaviso:
        p.requiere_renovacion = True

    db.session.commit()

    # 2️⃣ Reseteo físico de placas vencidas
    placas_vencidas = Placas.query.filter(
        Placas.fecha_vigencia <= hoy,
        Placas.requiere_renovacion == True
    ).all()

    for p in placas_vencidas:
        # Mover archivos a historial
        for url in [p.url_placa_frontal, p.url_placa_trasera]:
            if url:
                nombre = os.path.basename(url)
                src = os.path.join(UPLOAD_DIR, nombre)
                dst = os.path.join(HISTORIAL_DIR, nombre)
                if os.path.exists(src):
                    shutil.move(src, dst)

        # Guardar historial
        historial = HistorialPlaca(
            id_placa=p.id_placa,
            id_unidad=p.id_unidad,
            folio=p.folio,
            placa=p.placa,
            fecha_expedicion=p.fecha_expedicion,
            fecha_vigencia=p.fecha_vigencia,
            url_placa_frontal=p.url_placa_frontal.replace(UPLOAD_DIR,HISTORIAL_DIR) if p.url_placa_frontal else None,
            url_placa_trasera=p.url_placa_trasera.replace(UPLOAD_DIR,HISTORIAL_DIR) if p.url_placa_trasera else None,
            usuario=usuario
        )
        db.session.add(historial)

        # Limpiar registro activo
        p.placa = None
        p.fecha_expedicion = None
        p.url_placa_frontal = None
        p.url_placa_trasera = None
        # Mantener requiere_renovacion=True para alertas semanales

    db.session.commit()

    # 3️⃣ Enviar alertas semanales
    enviar_alertas_semanales()

    placas_reseteadas = [p.id_placa for p in placas_vencidas]
    return placas_reseteadas

# ---------------------------
# Scheduler diario
# ---------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: app.app_context().push() or reseteo_y_alertas(), 'interval', days=7)
scheduler.start()

# ---------------------------
# Endpoint para consultar alertas
# ---------------------------
@app.route("/alertas_placas", methods=["GET"])
def alertas_placas_endpoint():
    placas_alerta = Placas.query.filter_by(requiere_renovacion=True).all()
    return jsonify([{
        "id_placa": p.id_placa,
        "id_unidad": p.id_unidad,
        "fecha_vigencia": p.fecha_vigencia.isoformat() if p.fecha_vigencia else None
    } for p in placas_alerta])



ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/placas/<int:id_placa>", methods=["PUT"])
def update_placa(id_placa):
    UPLOAD_FOLDER = "uploads/placas"
    placa = Placas.query.get(id_placa)

    if not placa:
        return jsonify({"error": "Placa no encontrada"}), 404

    # Validar id_unidad
    id_unidad = request.form.get("id_unidad", placa.id_unidad)
    try:
        id_unidad = int(id_unidad)
    except (TypeError, ValueError):
        return jsonify({"error": "id_unidad inválido"}), 400
    placa.id_unidad = id_unidad

    # Actualizar campos básicos
    placa.folio = request.form.get("folio", placa.folio)
    placa.placa = request.form.get("placa", placa.placa)

    # Fechas
    fecha_expedicion = request.form.get("fecha_expedicion")
    if fecha_expedicion:
        try:
            placa.fecha_expedicion = datetime.strptime(fecha_expedicion, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Formato de fecha de expedición inválido"}), 400

    fecha_vigencia = request.form.get("fecha_vigencia")
    if fecha_vigencia:
        try:
            placa.fecha_vigencia = datetime.strptime(fecha_vigencia, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Formato de fecha de vigencia inválido"}), 400

    # requiere_renovacion
    requiere_renovacion = request.form.get("requiere_renovacion", placa.requiere_renovacion)
    if isinstance(requiere_renovacion, str):
        requiere_renovacion = requiere_renovacion.lower() in ["true", "1", "yes"]
    placa.requiere_renovacion = bool(requiere_renovacion)

    # Archivos PDF con nombre único
    for field_name in ["url_placa_frontal", "url_placa_trasera"]:
        if field_name in request.files:
            file = request.files[field_name]
            if file and allowed_file(file.filename):
                # Eliminar archivo viejo si existe
                old_path = getattr(placa, field_name)
                if old_path and os.path.exists(old_path):
                    os.remove(old_path)

                # Crear nombre único
                ext = os.path.splitext(file.filename)[1]  # conservar extensión
                new_filename = f"{uuid.uuid4()}{ext}"
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file_path = os.path.join(UPLOAD_FOLDER, new_filename)
                file.save(file_path)
                setattr(placa, field_name, file_path)
    try:
        db.session.commit()
        return jsonify({"message": "Placa actualizada correctamente", "placa": placa.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ---------------------------
# Endpoint para obtener historial de placas 

@app.route("/placas/historial", methods=["GET"])
def get_historial_placas():
    historial = HistorialPlaca.query.order_by(HistorialPlaca.fecha_vigencia.desc()).all()
    historial_list = [
        {
            "id_historial": h.id_historial,
            "id_placa": h.id_placa,
            "id_unidad": h.id_unidad,
            "folio": h.folio,
            "placa": h.placa,
            "fecha_expedicion": h.fecha_expedicion.strftime("%Y-%m-%d") if h.fecha_expedicion else None,
            "fecha_vigencia": h.fecha_vigencia.strftime("%Y-%m-%d") if h.fecha_vigencia else None,
            "url_placa_frontal": h.url_placa_frontal,
            "url_placa_trasera": h.url_placa_trasera,
            "usuario": h.usuario
        }
        for h in historial
    ]
    return jsonify({"historial": historial_list})


# Ruta para servir archivos de placas
@app.route('/uploads/placas/<filename>')
def uploaded_file(filename):
    print(f"Sirviendo archivo: {filename}")
    return send_from_directory('uploads/placas', filename)

@app.route("/uploads/historial_placas/<filename>")
def historial_file(filename):
    return send_from_directory("uploads/historial_placas", filename)






#==============================================================================
#refrendo y tenencia
#==============================================================================



@app.route("/refrendo_tenencia/check/<int:id_unidad>", methods=["GET"])
def check_unidad(id_unidad):
    hoy = date.today()
    year = hoy.year

    # Buscar si ya hay registro de este año
    pago = Refrendo_Tenencia.query.filter(
        Refrendo_Tenencia.id_unidad == id_unidad,
        db.extract("year", Refrendo_Tenencia.fecha_pago) == year
    ).first()

    if pago:
        return jsonify({
            "ok": False,
            "mensaje": "Ya existe un pago registrado para este año",
            "refrendo": pago.tipo_pago in ["REFRENDO","AMBOS"],
            "tenencia": pago.tipo_pago in ["TENENCIA","AMBOS"]
        })

    # Si no existe, se puede registrar
    return jsonify({
        "ok": True,
        "mensaje": "Unidad disponible para registrar pago",
        "refrendo": False,
        "tenencia": False
    })

# ----------------------------
# Funciones auxiliares
# ----------------------------
ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file_obj, tipo, id_unidad, fecha_pago):
    if not file_obj or file_obj.filename == "":
        return None
    if not allowed_file(file_obj.filename):
        return None

    subfolder = "refrendo" if tipo == "REFRENDO" else "tenencia"
    folder = os.path.join(app.root_path, "uploads", subfolder)
    os.makedirs(folder, exist_ok=True)

    ext = os.path.splitext(file_obj.filename)[1].lower()
    filename = f"{tipo.lower()}_{id_unidad}_{fecha_pago.isoformat()}_{uuid.uuid4().hex}{ext}"
    safe = secure_filename(filename)
    filepath = os.path.join(folder, safe)
    file_obj.save(filepath)

    return os.path.join("uploads", subfolder, safe).replace("\\", "/")

def move_file_to_historial(url, tipo):
    if not url:
        return None
    src = os.path.join(app.root_path, url)
    subfolder = "historial_refrendo" if tipo == "REFRENDO" else "historial_tenencia"
    folder = os.path.join(app.root_path, "uploads", subfolder)
    os.makedirs(folder, exist_ok=True)
    nombre = os.path.basename(url)
    dst = os.path.join(folder, nombre)
    if os.path.exists(src):
        shutil.move(src, dst)
    return os.path.join("uploads", subfolder, nombre).replace("\\", "/")

# ----------------------------
# Endpoint principal
# ----------------------------
# ----------------------------
@app.route('/refrendo_tenencia', methods=['POST'])
def registrar_pago():
    data = request.form
    try:
        id_unidad = int(data.get('id_unidad'))
        fecha_pago = datetime.strptime(data.get('fecha_pago'), '%Y-%m-%d').date()
        monto_general = float(data.get('monto') or 0)
        monto_refrendo = float(data.get('monto_refrendo') or 0)
        monto_tenencia = float(data.get('monto_tenencia') or 0)
        usuario = data.get('usuario', 'Sistema')
    except Exception:
        return jsonify({"error": "Datos inválidos"}), 400

    unidad = Unidades.query.get(id_unidad)
    if not unidad:
        return jsonify({"error": "Unidad no encontrada"}), 404

    limite_pago = date(fecha_pago.year, 3, 31)
    reset_realizado = False
    nuevo_registro = False

    # ------------------------------------------------------------------
    # 1️⃣ Verificar si ya existe registro del mismo año
    # ------------------------------------------------------------------
    existe_refrendo = Refrendo_Tenencia.query.filter(
        Refrendo_Tenencia.id_unidad == id_unidad,
        db.extract('year', Refrendo_Tenencia.fecha_pago) == fecha_pago.year
    ).first()

    if existe_refrendo:
        return jsonify({"error": "Ya existe un pago registrado para este año"}), 400

    # ------------------------------------------------------------------
    # 2️⃣ Buscar registro previo (año anterior)
    # ------------------------------------------------------------------
    registro = Refrendo_Tenencia.query.filter_by(id_unidad=id_unidad).first()

    if registro and registro.fecha_pago and registro.fecha_pago.year < fecha_pago.year:
        historial = Historial_Refrendo_Tenencia(
            id_pago=registro.id_pago,
            id_unidad=registro.id_unidad,
            tipo_pago=registro.tipo_pago,
            monto=registro.monto,
            monto_refrendo=registro.monto_refrendo,
            monto_tenencia=registro.monto_tenencia,
            fecha_pago=registro.fecha_pago,
            url_factura_refrendo=move_file_to_historial(registro.url_factura_refrendo, "REFRENDO"),
            url_factura_tenencia=move_file_to_historial(registro.url_factura_tenencia, "TENENCIA"),
            observaciones=registro.observaciones,
            tipo_movimiento="REGISTRO",
            usuario_registro=usuario
        )
        db.session.add(historial)

        registro.monto = 0
        registro.monto_refrendo = 0
        registro.monto_tenencia = 0
        registro.fecha_pago = None
        registro.tipo_pago = 'PENDIENTE'
        registro.observaciones = None
        registro.url_factura_refrendo = None
        registro.url_factura_tenencia = None
        db.session.commit()
        reset_realizado = True

    # ------------------------------------------------------------------
    # 3️⃣ Crear nuevo registro si no existe activo
    # ------------------------------------------------------------------
    if not registro or reset_realizado:
        registro = Refrendo_Tenencia(
            id_unidad=id_unidad,
            fecha_pago=fecha_pago,
            limite_pago=limite_pago,
            tipo_pago='REFRENDO' if fecha_pago <= limite_pago else 'AMBOS',
            monto_refrendo=monto_refrendo or monto_general,
            monto_tenencia=monto_tenencia or monto_general,
            monto=(monto_refrendo or monto_general) + (monto_tenencia or monto_general),
            observaciones=data.get('observaciones')
        )
        db.session.add(registro)
        db.session.commit()
        nuevo_registro = True

    # ------------------------------------------------------------------
    # 4️⃣ Guardar PDFs
    # ------------------------------------------------------------------
    file_refrendo = request.files.get('url_factura_refrendo')
    file_tenencia = request.files.get('url_factura_tenencia')

    registro.url_factura_refrendo = save_uploaded_file(file_refrendo, "REFRENDO", id_unidad, fecha_pago)
    registro.url_factura_tenencia = save_uploaded_file(file_tenencia, "TENENCIA", id_unidad, fecha_pago)

    db.session.commit()

    return jsonify({
        "message": f"Pago {registro.tipo_pago} registrado correctamente",
        "id_pago": registro.id_pago
    }), 200


@app.route('/refrendo_tenencia', methods=['GET'])
def listar_pagos_refrendo_tenencia():
    try:
        pagos = Refrendo_Tenencia.query.join(Unidades).all()
        data = []

        for pago in pagos:
            data.append({
                "id_pago": pago.id_pago,
                "id_unidad": pago.id_unidad,
                "vehiculo": pago.unidad.vehiculo,
                "marca": pago.unidad.marca,
                "modelo": pago.unidad.modelo,
                "fecha_pago": pago.fecha_pago.strftime('%Y-%m-%d') if pago.fecha_pago else "",
                "tipo_pago": pago.tipo_pago,
                "monto_refrendo": float(pago.monto_refrendo or 0),
                "monto_tenencia": float(pago.monto_tenencia or 0),
                "monto_total": float(pago.monto or 0),
                "usuario": getattr(pago, "usuario", ""),  # si luego agregas campo usuario
                "observaciones": pago.observaciones or "",
                "url_factura_refrendo": pago.url_factura_refrendo,
                "url_factura_tenencia": pago.url_factura_tenencia,
                "limite_pago": pago.limite_pago.strftime('%Y-%m-%d') if pago.limite_pago else "",
                "fecha_creacion": pago.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if pago.fecha_creacion else ""
            })
        return jsonify(data), 200

    except Exception as e:
        print("ERROR listar_pagos_refrendo_tenencia:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/refrendo_tenencia/<int:id_pago>', methods=['PUT'])
def actualizar_pago(id_pago):
    data = request.form

    # Ahora obtenemos el usuario desde FormData
    user_id = data.get("usuario")
    if not user_id:
        return jsonify({"error": "Usuario no proporcionado"}), 401

    registro = Refrendo_Tenencia.query.get(id_pago)
    if not registro:
        return jsonify({"error": "Registro no encontrado"}), 404

    try:
        if 'fecha_pago' in data:
            registro.fecha_pago = datetime.strptime(data['fecha_pago'], '%Y-%m-%d').date()
            registro.limite_pago = date(registro.fecha_pago.year, 3, 31)

        if 'monto_refrendo' in data:
            registro.monto_refrendo = float(data['monto_refrendo'])
        if 'monto_tenencia' in data:
            registro.monto_tenencia = float(data['monto_tenencia'])
        if 'observaciones' in data:
            registro.observaciones = data['observaciones']

        # Archivos
        file_refrendo = request.files.get('url_factura_refrendo')
        file_tenencia = request.files.get('url_factura_tenencia')
        if file_refrendo:
            registro.url_factura_refrendo = save_uploaded_file(file_refrendo, "REFRENDO", registro.id_unidad, registro.fecha_pago)
        if file_tenencia:
            registro.url_factura_tenencia = save_uploaded_file(file_tenencia, "TENENCIA", registro.id_unidad, registro.fecha_pago)

        registro.usuario = user_id  # 👈 Usuario desde frontend

        db.session.commit()
        return jsonify({"message": "Pago actualizado correctamente"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/historiales', methods=['GET'])
def get_historiales():
    try:
        historiales = (
            db.session.query(Historial_Refrendo_Tenencia, Unidades)
            .join(Unidades, Historial_Refrendo_Tenencia.id_unidad == Unidades.id_unidad)
            .order_by(Historial_Refrendo_Tenencia.fecha_registro.desc())
            .all()
        )

        data = []
        for h, u in historiales:
            data.append({
                "id_historial": h.id_historial,
                "id_unidad": h.id_unidad,
                "vehiculo_modelo": f"{u.vehiculo} {u.modelo}",
                "id_pago": h.id_pago,
                "tipo_pago": h.tipo_pago,
                "monto": float(h.monto) if h.monto else 0,
                "monto_refrendo": float(h.monto_refrendo) if h.monto_refrendo else 0,
                "monto_tenencia": float(h.monto_tenencia) if h.monto_tenencia else 0,
                "fecha_pago": h.fecha_pago.strftime("%Y-%m-%d") if h.fecha_pago else None,
                "url_factura_refrendo": h.url_factura_refrendo,
                "url_factura_tenencia": h.url_factura_tenencia,
                "observaciones": h.observaciones,
                "fecha_registro": h.fecha_registro.strftime("%Y-%m-%d %H:%M:%S") if h.fecha_registro else None,
                "tipo_movimiento": h.tipo_movimiento,
                "usuario_registro": h.usuario_registro,
                "observaciones_adicional": h.observaciones_adicional
            })

        return jsonify(data), 200

    except Exception as e:
        print("ERROR get_historiales:", e)
        return jsonify({"error": str(e)}), 500
        
def enviar_alertas_refrendo_tenencia():
    hoy = date.today()
    año_actual = hoy.year
    inicio_periodo = date(año_actual, 1, 1)
    fin_periodo = date(año_actual, 3, 31)

    unidades = Unidades.query.all()
    if not unidades:
        return []

    alertas_por_correo = {}
    for u in unidades:
        pago = Refrendo_Tenencia.query.filter(
            Refrendo_Tenencia.id_unidad == u.id_unidad,
            db.extract("year", Refrendo_Tenencia.fecha_pago) == año_actual
        ).first()

        if not pago:
            correo = getattr(u, "correo", None) or "imanolcruz588@gmail.com"
            if correo not in alertas_por_correo:
                alertas_por_correo[correo] = []

            mensaje = (
                f"Pague refrendo antes del 31 de marzo"
                if hoy <= fin_periodo
                else "Debe pagar refrendo y tenencia. Se aplicarán recargos."
            )
            alertas_por_correo[correo].append({
                "id_unidad": u.id_unidad,
                "vehiculo": u.vehiculo,
                "modelo": u.modelo,
                "mensaje": mensaje
            })

    resultado = []
    for correo, vehiculos in alertas_por_correo.items():
        cuerpo = "Unidades con pagos pendientes:\n\n"
        for v in vehiculos:
            cuerpo += f"- {v['vehiculo']} {v['modelo']} (ID {v['id_unidad']}): {v['mensaje']}\n"
            resultado.append({
                "correo": correo,
                "id_unidad": v['id_unidad'],
                "vehiculo": v['vehiculo'],
                "modelo": v['modelo'],
                "mensaje": v['mensaje']
            })

        msg = Message(
            subject=f"Aviso de pagos pendientes ({año_actual})",
            recipients=[correo],
            body=cuerpo
        )
        mail.send(msg)
        print(f"[INFO] Correo enviado a {correo} con {len(vehiculos)} vehículos.")

    print(f"[INFO] Total alertas enviadas: {len(resultado)}")
    return resultado

# --------------------------------------------
# Programador semanal automático
# --------------------------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: app.app_context().push() or enviar_alertas_refrendo_tenencia(), 'interval', days=7)
scheduler.start()

# --------------------------------------------
# Endpoint manual para pruebas
# --------------------------------------------
@app.route('/refrendo_tenencia/test_alertas', methods=['GET'])
def test_alertas():
    alertas = enviar_alertas_refrendo_tenencia()
    return jsonify({"alertas": alertas, "total": len(alertas)}), 200





#===================================================
#Mantenimientod programados
#====================================================


# ------------------------------------------------------
# UTIL: obtener frecuencia por marca y tipo
# -----------------------------------------------------
def obtener_frecuencia_por_marca(marca, id_tipo):
    return FrecuenciasPorMarca.query.filter_by(marca=marca, id_tipo_mantenimiento=id_tipo).first()

# ---------------------
# RUTAS: Tipos de mantenimiento
# ---------------------
@app.route('/tipos_mantenimiento', methods=['GET'])
def get_tipos():
    tipos = TiposMantenimiento.query.order_by(TiposMantenimiento.id_tipo_mantenimiento).all()
    return jsonify([{
        "id_tipo_mantenimiento": t.id_tipo_mantenimiento,
        "nombre_tipo": t.nombre_tipo,
        "descripcion": t.descripcion
    } for t in tipos])

@app.route('/tipos_mantenimiento', methods=['POST'])
def post_tipo():
    data = request.get_json()
    nombre = data.get('nombre_tipo')
    descripcion = data.get('descripcion')
    if not nombre:
        return jsonify({"error":"nombre_tipo requerido"}), 400
    nuevo = TiposMantenimiento(nombre_tipo=nombre, descripcion=descripcion)
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"message":"Tipo creado","id": nuevo.id_tipo_mantenimiento}), 201

# ------------------------------------------------------------
# RUTAS: Frecuencias por marca
# ------------------------------------------------------------
@app.route('/frecuencias_pormarca', methods=['GET'])
def get_frecuencias():
    filas = FrecuenciasPorMarca.query.all()
    return jsonify([{
        "id_frecuencia": f.id_frecuencia,
        "marca": f.marca,
        "id_tipo_mantenimiento": f.id_tipo_mantenimiento,
        "frecuencia_tiempo": f.frecuencia_tiempo,
        "frecuencia_kilometraje": f.frecuencia_kilometraje
    } for f in filas])

@app.route('/frecuencias_pormarca', methods=['POST'])
def post_frecuencia():
    data = request.get_json()
    if not all(k in data for k in ("marca","id_tipo_mantenimiento","frecuencia_tiempo","frecuencia_kilometraje")):
        return jsonify({"error":"campos faltantes"}), 400
    f = FrecuenciasPorMarca(
        marca = data['marca'],
        id_tipo_mantenimiento = data['id_tipo_mantenimiento'],
        frecuencia_tiempo = data['frecuencia_tiempo'],
        frecuencia_kilometraje = data['frecuencia_kilometraje']
    )
    db.session.add(f)
    db.session.commit()
    return jsonify({"message":"Frecuencia creada","id": f.id_frecuencia}), 201

# ---------------------
# RUTA: programar mantenimientos iniciales para una unidad (al crear unidad)
# ---------------------
@app.route('/programar_mantenimientos/<int:id_unidad>', methods=['POST'])
def programar_por_marca(id_unidad):
    unidad = Unidades.query.get(id_unidad)
    if not unidad:
        return jsonify({"error":"Unidad no encontrada"}), 404

    # Busca frecuencias para la marca
    frecuencias = FrecuenciasPorMarca.query.filter_by(marca=unidad.marca).all()
    if not frecuencias:
        return jsonify({"error":"No hay frecuencias definidas para esta marca"}), 400

    created = []
    for f in frecuencias:
        # si ya existe programado para (unidad, tipo) no duplicar
        existe = MantenimientosProgramados.query.filter_by(id_unidad=id_unidad, id_tipo_mantenimiento=f.id_tipo_mantenimiento).first()
        if existe:
            continue
        proximo_fecha = date.today() + timedelta(days=f.frecuencia_tiempo)
        proximo_km = (unidad.kilometraje_actual or 0) + f.frecuencia_kilometraje
        mp = MantenimientosProgramados(
            id_unidad = id_unidad,
            id_tipo_mantenimiento = f.id_tipo_mantenimiento,
            fecha_ultimo_mantenimiento = None,
            kilometraje_ultimo = None,
            proximo_mantenimiento = proximo_fecha,
            proximo_kilometraje = proximo_km
        )
        db.session.add(mp)
        db.session.flush()  # para obtener id si es necesario
        created.append(mp.id_mantenimiento_programado)
    db.session.commit()
    return jsonify({"message":"Programados creados","created": created}), 201

# ---------------------
# RUTAS: Listar programados
# ---------------------
@app.route('/mantenimientos_programados', methods=['GET'])
def listar_programados():
    # Subconsulta para obtener la placa más reciente por unidad
    sub_placa = db.session.query(
        Placas.id_unidad,
        Placas.placa.label("placa")
    ).distinct(Placas.id_unidad).subquery()

    # Consulta principal
    q = db.session.query(
        MantenimientosProgramados.id_mantenimiento_programado,
        MantenimientosProgramados.id_unidad,
        sub_placa.c.placa,
        Unidades.marca,
        Unidades.kilometraje_actual,
        TiposMantenimiento.nombre_tipo,
        MantenimientosProgramados.fecha_ultimo_mantenimiento,
        MantenimientosProgramados.kilometraje_ultimo,
        MantenimientosProgramados.proximo_mantenimiento,
        MantenimientosProgramados.proximo_kilometraje
    ).join(
        TiposMantenimiento,
        MantenimientosProgramados.id_tipo_mantenimiento == TiposMantenimiento.id_tipo_mantenimiento
    ).join(
        Unidades,
        MantenimientosProgramados.id_unidad == Unidades.id_unidad
    ).outerjoin(
        sub_placa,
        MantenimientosProgramados.id_unidad == sub_placa.c.id_unidad
    )

    resultado = []
    for row in q:
        resultado.append({
            "id_mantenimiento_programado": row.id_mantenimiento_programado,
            "id_unidad": row.id_unidad,
            "placa": row.placa,
            "marca": row.marca,
            "tipo": row.nombre_tipo,
            "fecha_ultimo_mantenimiento": row.fecha_ultimo_mantenimiento.isoformat() if row.fecha_ultimo_mantenimiento else None,
            "kilometraje_ultimo": row.kilometraje_ultimo,
            "proximo_mantenimiento": row.proximo_mantenimiento.isoformat() if row.proximo_mantenimiento else None,
            "proximo_kilometraje": row.proximo_kilometraje
        })
    
    return jsonify(resultado)

# ---------------------
# RUTA: registrar mantenimiento realizado (y reprogramar)
# ---------------------
@app.route('/mantenimientos', methods=['POST'])
def registrar_mantenimiento():
    data = request.get_json()
    # campos esperados: id_unidad, tipo_mantenimiento (nombre), kilometraje, descripcion, id_mantenimiento_programado (opcional)
    id_unidad = data.get('id_unidad')
    tipo_nombre = data.get('tipo_mantenimiento')
    kilometraje = data.get('kilometraje')
    descripcion = data.get('descripcion')
    id_mp = data.get('id_mantenimiento_programado')

    if not id_unidad or not tipo_nombre or kilometraje is None:
        return jsonify({"error":"id_unidad, tipo_mantenimiento y kilometraje son requeridos"}), 400

    unidad = Unidades.query.get(id_unidad)
    if not unidad:
        return jsonify({"error":"Unidad no encontrada"}), 404

    # Buscar tipo (Menor/Mayor)
    tipo = TiposMantenimiento.query.filter_by(nombre_tipo=tipo_nombre).first()
    if not tipo:
        return jsonify({"error":"Tipo de mantenimiento no válido"}), 400

    # Buscar el programado correspondiente si no se proporcionó
    if not id_mp:
        mp = MantenimientosProgramados.query.filter_by(id_unidad=id_unidad, id_tipo_mantenimiento=tipo.id_tipo_mantenimiento).first()
    else:
        mp = MantenimientosProgramados.query.get(id_mp)

    # Crear historial mantenimiento (registro)
    fecha_real = date.today()
    nuevo = Mantenimientos(
        id_mantenimiento_programado = mp.id_mantenimiento_programado if mp else None,
        id_unidad = id_unidad,
        tipo_mantenimiento = tipo_nombre,
        descripcion = descripcion,
        fecha_realizacion = fecha_real,
        kilometraje = kilometraje,
        realizado_por = data.get('realizado_por'),
        empresa_garantia = data.get('empresa_garantia'),
        cobertura_garantia = data.get('cobertura_garantia'),
        costo = data.get('costo'),
        observaciones = data.get('observaciones'),
        url_comprobante = data.get('url_comprobante')
    )
    db.session.add(nuevo)

    # Actualizar o crear registro programado:
    # Si existe, actualizamos fecha_ultimo y kilometraje_ultimo y recalculamos proximo
    frecuencia = FrecuenciasPorMarca.query.filter_by(marca=unidad.marca, id_tipo_mantenimiento=tipo.id_tipo_mantenimiento).first()
    if mp:
        mp.fecha_ultimo_mantenimiento = fecha_real
        mp.kilometraje_ultimo = kilometraje
        if frecuencia:
            # calcular próximo por tiempo y por km
            mp.proximo_mantenimiento = fecha_real + timedelta(days=frecuencia.frecuencia_tiempo)
            mp.proximo_kilometraje = (kilometraje or 0) + frecuencia.frecuencia_kilometraje
        db.session.add(mp)
    else:
        # si no existía programado, crear uno nuevo basado en frecuencia
        if frecuencia:
            proximo_fecha = fecha_real + timedelta(days=frecuencia.frecuencia_tiempo)
            proximo_km = (kilometraje or 0) + frecuencia.frecuencia_kilometraje
        else:
            proximo_fecha = None
            proximo_km = None
        nuevo_mp = MantenimientosProgramados(
            id_unidad = id_unidad,
            id_tipo_mantenimiento = tipo.id_tipo_mantenimiento,
            fecha_ultimo_mantenimiento = fecha_real,
            kilometraje_ultimo = kilometraje,
            proximo_mantenimiento = proximo_fecha,
            proximo_kilometraje = proximo_km
        )
        db.session.add(nuevo_mp)

    # Opcional: actualizar kilometraje_actual en Unidades si existe campo
    try:
        if unidad.kilometraje_actual is None or (kilometraje and kilometraje > (unidad.kilometraje_actual or 0)):
            unidad.kilometraje_actual = kilometraje
            db.session.add(unidad)
    except Exception:
        pass

    db.session.commit()
    return jsonify({"message":"Mantenimiento registrado y programado actualizado."}), 201

# ---------------------
# RUTA: historial de mantenimientos
# ---------------------
@app.route('/mantenimientos', methods=['GET'])
def listar_mantenimientos():
    mantenimientos = Mantenimientos.query.order_by(Mantenimientos.fecha_realizacion.desc()).all()
    salida = []
    for m in mantenimientos:
        salida.append({
            "id_mantenimiento": m.id_mantenimiento,
            "id_unidad": m.id_unidad,
            "tipo_mantenimiento": m.tipo_mantenimiento,
            "fecha_realizacion": m.fecha_realizacion.isoformat(),
            "kilometraje": m.kilometraje,
            "descripcion": m.descripcion,
            "realizado_por": m.realizado_por,
            "costo": str(m.costo) if m.costo is not None else None
        })
    return jsonify(salida)

#===================================================================================
#filteraciones
#===============================================================================

@app.route('/api/stats/costos_mantenimiento_por_mes', methods=['GET'])
def get_costos_mantenimiento_por_mes():
    try:
        # --- 1. Obtener Filtros Opcionales de la URL ---
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sucursal = request.args.get('sucursal')

        print("Filtros recibidos:", start_date, end_date, sucursal)  # Depuración

        # --- 2. Seleccionar la Función de Fecha ---
        mes_grupo = db.func.date_trunc('month', Mantenimientos.fecha_realizacion).label('mes')

        # --- 3. Construir la Consulta ---
        query = db.session.query(
            mes_grupo,
            db.func.sum(Mantenimientos.costo).label('total_costo')
        )

        # Unir con Unidades si hay filtro de sucursal
        if sucursal:
            query = query.join(Unidades, Mantenimientos.id_unidad == Unidades.id_unidad)

        # --- 4. Aplicar Filtros ---
        if start_date:
            query = query.filter(Mantenimientos.fecha_realizacion >= start_date)
        if end_date:
            query = query.filter(Mantenimientos.fecha_realizacion <= end_date)
        if sucursal:
            # Hacemos insensible a mayúsculas y espacios
            query = query.filter(func.lower(Unidades.sucursal) == sucursal.strip().lower())

        # --- 5. Agrupar y Ordenar ---
        query = query.group_by(mes_grupo).order_by(mes_grupo.asc())

        # --- 6. Ejecutar y revisar resultados ---
        resultados = query.all()
        print("Resultados de la query:", resultados)  # Depuración

        datos_grafica = [
            {
                "mes": r.mes.strftime('%Y-%m-%d'),
                "total_costo": float(r.total_costo) if r.total_costo else 0
            }
            for r in resultados
        ]

        return jsonify(datos_grafica)

    except Exception as e:
        print("Error interno:", e)  # Depuración
        return jsonify({"error": str(e)}), 500


@app.route("/api/sucursales", methods=["GET"])
def get_sucursales():
    try:
        # Extraemos sucursales distintas de la tabla Unidades
        sucursales = db.session.query(Unidades.sucursal).distinct().all()
        print("Sucursales raw:", sucursales)

        # Limpiamos valores vacíos o None
        lista_sucursales = [s[0].strip() for s in sucursales if s[0] and s[0].strip() != ""]
        print("Sucursales limpias:", lista_sucursales)

        # Ordenamos alfabéticamente
        lista_sucursales.sort()

        # Valor por defecto si no hay sucursales
        if not lista_sucursales:
            lista_sucursales = ["Sin sucursales"]

        return jsonify(lista_sucursales)
    except Exception as e:
        print("Error en /api/sucursales:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/choferes", methods=["GET"])
def choferlistas():
    choferes = Choferes.query.order_by(Choferes.nombre).all()
    return jsonify([c.to_dict() for c in choferes])




@app.route('/api/stats/fallas_por_pieza', methods=['GET'])
def get_fallas_por_pieza():
    try:
        # --- Obtener filtros opcionales ---
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sucursal = request.args.get('sucursal')
        # Límite opcional; si no viene o es 0, se traen todas las fallas
        limit = request.args.get('limit', default=0, type=int)

        # --- Construir la consulta ---
        query = db.session.query(
            Piezas.nombre_pieza,
            db.func.count(FallaMecanica.id_falla).label('total_fallas')
        ).join(Piezas, FallaMecanica.id_pieza == Piezas.id_pieza)

        if sucursal:
            query = query.join(Unidades, FallaMecanica.id_unidad == Unidades.id_unidad)

        # --- Aplicar filtros ---
        if start_date:
            query = query.filter(FallaMecanica.fecha_falla >= start_date)
        if end_date:
            query = query.filter(FallaMecanica.fecha_falla <= end_date)
        if sucursal:
            query = query.filter(Unidades.sucursal == sucursal)

        # --- Agrupar y ordenar ---
        query = query.group_by(Piezas.nombre_pieza) \
                     .order_by(db.func.count(FallaMecanica.id_falla).desc())

        # --- Aplicar límite solo si es mayor a 0 ---
        if limit > 0:
            query = query.limit(limit)

        # --- Ejecutar y convertir a JSON ---
        resultados = query.all()
        datos_grafica = [
            {"pieza": r.nombre_pieza, "total_fallas": r.total_fallas}
            for r in resultados
        ]

        return jsonify(datos_grafica)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



from datetime import date
from flask import jsonify, request

@app.route('/api/verificaciones', methods=['GET'])
def get_verificaciones():
    """
    Endpoint para obtener todas las verificaciones vehiculares,
    mostrando si cada unidad tiene verificación vigente o no.
    """
    try:
        verificaciones = VerificacionVehicular.query.join(Unidades).all()
        hoy = date.today()

        resultado = []
        for v in verificaciones:
            # Calculamos vigencia según periodo_1_real y periodo_2_real
            vigente = False
            if v.periodo_1_real and v.periodo_1_real >= hoy:
                vigente = True
            if v.periodo_2_real and v.periodo_2_real >= hoy:
                vigente = True

            resultado.append({
                "id_verificacion": v.id_verificacion,
                "unidad": v.unidad.placa if v.unidad else None,
                "ultima_verificacion": v.ultima_verificacion.isoformat() if v.ultima_verificacion else None,
                "periodo_1_real": v.periodo_1_real.isoformat() if v.periodo_1_real else None,
                "periodo_2_real": v.periodo_2_real.isoformat() if v.periodo_2_real else None,
                "holograma": v.holograma,
                "folio_verificacion": v.folio_verificacion,
                "engomado": v.engomado,
                "vigente": vigente
            })

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000, debug=True)