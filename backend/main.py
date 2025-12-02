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
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "http://localhost:5173"}})
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:admin@localhost/control_vehicular_unificada')
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
    token_expiracion = db.Column(db.DateTime, nullable=True)  # <-- Agrega esta línea

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
    niv = db.Column(db.String(50))
    motor = db.Column(db.String(50))
    transmision = db.Column(db.String(50))
    combustible = db.Column(db.String(50))
    color = db.Column(db.String(50))
    telefono_gps = db.Column(db.String(20))
    sim_gps = db.Column(db.String(20))
    uid = db.Column(db.String(50))
    propietario = db.Column(db.String(255))
    id_empresa = db.Column(db.Integer, db.ForeignKey("empresa.id_empresa"), nullable=False)  # <-- empresa
    sucursal = db.Column(db.Integer, db.ForeignKey("sucursales.id_sucursal"))  # <-- sucursal
    compra_arrendado = db.Column(db.String(20))
    fecha_adquisicion = db.Column(db.Date)
    valor_factura = db.Column(db.Numeric(12,2))
    url_factura = db.Column(db.String(255))
    kilometraje_actual = db.Column(db.Integer)
    url_foto = db.Column(db.String(255))  # <-- campo agregado

    placa = db.relationship('Placas', uselist=False, backref='unidad')
    empresa = db.relationship("Empresa", backref="unidades")
    sucursal_rel = db.relationship("Sucursal", backref="unidades")

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
            'id_empresa': self.id_empresa,
            'sucursal': self.sucursal,
            'compra_arrendado': self.compra_arrendado,
            'fecha_adquisicion': str(self.fecha_adquisicion) if self.fecha_adquisicion else None,
            'valor_factura': float(self.valor_factura) if self.valor_factura else None,
            'url_factura': self.url_factura,
            'kilometraje_actual': self.kilometraje_actual,
            'url_foto': self.url_foto,
            'placa': self.placa.to_dict() if self.placa else None,
            'empresa_nombre': self.empresa.nombre_comercial if self.empresa else None,
            'sucursal_nombre': self.sucursal_rel.nombre if self.sucursal_rel else None
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
    monto_pago = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    url_comprobante_pago = db.Column(db.String(255))
    url_tarjeta_circulacion = db.Column(db.String(255))

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
            'requiere_renovacion': self.requiere_renovacion,
            'monto_pago': float(self.monto_pago) if self.monto_pago else 0,
            'url_comprobante_pago': self.url_comprobante_pago,
            'url_tarjeta_circulacion': self.url_tarjeta_circulacion
        }


# Modelo principal de Garantias
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
    telefono_fijo = db.Column(db.String(20))    # NUEVO
    telefono_celular = db.Column(db.String(20)) # NUEVO

    unidad = db.relationship("Unidades", backref="garantias")


# Modelo de historial de Garantías
class HistorialGarantias(db.Model):
    __tablename__ = "HistorialGarantias"

    id_historial = db.Column(db.Integer, primary_key=True, autoincrement=True)
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
    telefono_fijo = db.Column(db.String(20))    # NUEVO
    telefono_celular = db.Column(db.String(20)) # NUEVO
    usuario = db.Column(db.String(50))



class HistorialPlaca(db.Model):
    __tablename__ = "HistorialPlacas"
    id_historial = db.Column(db.Integer, primary_key=True)
    
    # Relaciones y referencias
    id_placa = db.Column(db.Integer, db.ForeignKey('Placas.id_placa'), nullable=False)
    id_unidad = db.Column(db.Integer, nullable=False)
    
    # Fechas y auditoría
    fecha_cambio = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    
    # Datos de la placa
    folio = db.Column(db.String(50))
    placa = db.Column(db.String(10))
    fecha_expedicion = db.Column(db.Date)
    fecha_vigencia = db.Column(db.Date)
    
    # Archivos asociados
    url_placa_frontal = db.Column(db.String(255))
    url_placa_trasera = db.Column(db.String(255))
    url_comprobante_pago = db.Column(db.String(255))
    url_tarjeta_circulacion = db.Column(db.String(255))
    
    # Otros campos
    monto_pago = db.Column(db.Float)
    requiere_renovacion = db.Column(db.Boolean, default=False)
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

    # Relaciones
    marca_rel = db.relationship("MarcasPiezas", backref="fallas")
    pieza_rel = db.relationship("Piezas", backref="fallas")  # <-- agregada
    lugar_rel = db.relationship("LugarReparacion", backref="fallas")  # opcional

    def to_dict(self):
        return {
            "id_falla": self.id_falla,
            "id_unidad": self.id_unidad,
            "pieza": self.pieza_rel.nombre_pieza if self.pieza_rel else None,  # usa la relación
            "marca": self.marca_rel.nombre_marca if self.marca_rel else None,
            "lugar_reparacion": self.lugar_rel.nombre_lugar if self.lugar_rel else None,
            "tipo_servicio": self.tipo_servicio,
            "descripcion": self.descripcion,
            "proveedor": self.proveedor,
            "costo": float(self.costo) if self.costo else None,
            "fecha_falla": self.fecha_falla.strftime("%Y-%m-%d") if self.fecha_falla else None
        }


class FallasMensajes(db.Model):
    __tablename__ = 'fallas_mensajes'
    id_mensaje = db.Column(db.Integer, primary_key=True)
    id_falla = db.Column(db.Integer, db.ForeignKey('fallasmecanicas.id_falla'))
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    mensaje = db.Column(db.Text, nullable=False)
    archivo_adjunto = db.Column(db.String(255))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    falla = db.relationship("FallaMecanica", backref="mensajes")  # <-- usar el nombre correcto de la clase


# -------------------------------
# Modelo para mensajes de solicitudes
# -------------------------------
class SolicitudFallaMensajes(db.Model):
    __tablename__ = "solicitudes_mensajes"
    id_mensaje = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_solicitud = db.Column(db.Integer, db.ForeignKey("solicitudesfallas.id_solicitud"))
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id_usuario"))
    mensaje = db.Column(db.Text, nullable=False)
    archivo_adjunto = db.Column(db.String(255))  # <-- esto faltaba
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    solicitud = db.relationship("SolicitudFalla", backref="mensajes")  # para acceder a la solicitud
    usuario = db.relationship("Usuarios", backref="mensajes")  # para acceder al usuario que envía




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
    tipo_pago = db.Column(db.Enum('REFRENDO','TENENCIA','AMBOS','PENDIENTE'), nullable=False, default='REFRENDO')
    monto = db.Column(db.Numeric(10,2), nullable=False, default=0)
    monto_refrendo = db.Column(db.Numeric(10,2), nullable=False, default=0)
    monto_tenencia = db.Column(db.Numeric(10,2), nullable=False, default=0)
    fecha_pago = db.Column(db.Date, nullable=False)
    limite_pago = db.Column(db.Date, nullable=False)
    url_factura = db.Column(db.String(255))  # <-- Solo un archivo
    observaciones = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación ORM
    unidad = db.relationship("Unidades", backref=db.backref("pagos", lazy=True))


class Historial_Refrendo_Tenencia(db.Model):
    __tablename__ = 'Historial_Refrendo_Tenencia'
    id_historial = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_pago = db.Column(db.Integer, db.ForeignKey('Refrendo_Tenencia.id_pago'), nullable=False)
    id_unidad = db.Column(db.Integer, db.ForeignKey('Unidades.id_unidad'), nullable=False)
    tipo_pago = db.Column(db.Enum('REFRENDO','TENENCIA','AMBOS','PENDIENTE'), nullable=False)
    monto = db.Column(db.Numeric(10,2), default=0)
    monto_refrendo = db.Column(db.Numeric(10,2), default=0)
    monto_tenencia = db.Column(db.Numeric(10,2), default=0)
    fecha_pago = db.Column(db.Date)
    url_factura = db.Column(db.String(255))  # <-- Solo un archivo
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


class Empresa(db.Model):
    __tablename__ = 'empresa'
    id_empresa = db.Column(db.Integer, primary_key=True, autoincrement=True)
    razon_social = db.Column(db.String(255))
    rfc = db.Column(db.String(20))
    regimen_fiscal = db.Column(db.String(255))
    nombre_comercial = db.Column(db.String(255))
    direccion = db.Column(db.String(255))
    inicio_operaciones = db.Column(db.Date)
    estatus = db.Column(db.String(10))
    actividad_economica = db.Column(db.String(255))
    sucursales = db.relationship("Sucursal", backref="empresa", cascade="all, delete-orphan")

    
class Sucursal(db.Model):
    __tablename__ = "sucursales"
    id_sucursal = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(255), nullable=False)
    direccion = db.Column(db.String(255))
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(100))
    horario = db.Column(db.String(100))
    id_empresa = db.Column(db.Integer, db.ForeignKey("empresa.id_empresa"), nullable=False)


class Alerta(db.Model):
    __tablename__ = "alertas"
    id_alerta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_unidad = db.Column(db.Integer, db.ForeignKey("Unidades.id_unidad", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    tipo_alerta = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_generada = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_resuelta = db.Column(db.DateTime, nullable=True)
    estado = db.Column(db.String(20), nullable=False, default="pendiente")  # pendiente / enviada / atendida
    detalle = db.Column(db.JSON, nullable=True)

    # Relación con unidad
    unidad = db.relationship("Unidades", backref=db.backref("alertas", lazy=True))

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



# Función para enviar correo en segundo plano
def enviar_correo_async(app, msg):
    with app.app_context():
        mail.send(msg)

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
        id_chofer = data.get('id_chofer')  # opcional

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
            db.session.flush()  # Para obtener el id
            id_chofer = nuevo_chofer.id_chofer
            rol = 'chofer'  # forzar rol chofer

        # Crear usuario
        nuevo_usuario = Usuarios(
            nombre=nombre,
            usuario=usuario,
            contraseña=generate_password_hash(contraseña),  # Guardamos el hash
            correo=correo,
            rol=rol,
            id_chofer=id_chofer
        )
        db.session.add(nuevo_usuario)
        db.session.commit()

        # --- Enviar correo en segundo plano ---
        msg = Message(
            subject="Tus credenciales de acceso",
            recipients=[correo],
            body=f"Hola {nombre},\n\nTu usuario ha sido creado exitosamente.\n\nUsuario: {usuario}\nContraseña: {contraseña}\n\nTe recomendamos cambiar tu contraseña después de iniciar sesión.\n\nSaludos."
        )
        threading.Thread(target=enviar_correo_async, args=(app, msg)).start()

        return jsonify({"mensaje": "Usuario creado correctamente y correo enviado"}), 201

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

        # Obtener filtros desde query string
        filtros = []
        params = []

        id_empresa = request.args.get('id_empresa')
        if id_empresa:
            filtros.append("U.id_empresa = %s")
            params.append(id_empresa)

        sucursal = request.args.get('sucursal')
        if sucursal:
            filtros.append("U.sucursal = %s")
            params.append(sucursal)

        estado_tarjeta = request.args.get('estado_tarjeta')
        if estado_tarjeta:
            filtros.append(
                "CASE WHEN P.fecha_vigencia < CURDATE() THEN 'Vencida' ELSE 'Activa' END = %s"
            )
            params.append(estado_tarjeta)

        # Construir WHERE dinámico
        where_clause = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        query = f"""
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
            U.valor_factura,
            U.url_factura,
            U.kilometraje_actual,
            U.url_foto,
            U.id_empresa,
            U.sucursal,
            JSON_OBJECT(
                'color', U.color,
                'clase_tipo', U.clase_tipo,
                'motor', U.motor,
                'transmision', U.transmision,
                'combustible', U.combustible,
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
        {where_clause}
        ORDER BY U.id_unidad;
        """

        cursor.execute(query, tuple(params))
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Formatear fechas
        for unidad in results:
            if unidad['fecha_adquisicion']:
                unidad['fecha_adquisicion'] = unidad['fecha_adquisicion'].strftime('%Y-%m-%d')
            if unidad['fecha_vencimiento_tarjeta']:
                unidad['fecha_vencimiento_tarjeta'] = unidad['fecha_vencimiento_tarjeta'].strftime('%Y-%m-%d')
            if unidad['mas_datos']:
                unidad['mas_datos'] = json.loads(unidad['mas_datos'])

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
    try:
        print("=== INICIO UPDATE UNIDAD ===")
        UPLOAD_IMG = 'uploads/unidades_imagen'
        UPLOAD_PLACAS = 'uploads/placas'
        UPLOAD_FACTURAS = 'uploads/facturas'

        # Crear carpetas si no existen
        os.makedirs(UPLOAD_IMG, exist_ok=True)
        os.makedirs(UPLOAD_PLACAS, exist_ok=True)
        os.makedirs(UPLOAD_FACTURAS, exist_ok=True)
        print("Carpetas de subida verificadas")

        # Obtener datos del formulario y archivos
        data = request.form
        files = request.files
        print("Datos recibidos:", data)
        print("Archivos recibidos:", files)
        print("ID unidad a actualizar:", id_unidad)

        # Obtener la unidad
        unidad = db.session.get(Unidades, id_unidad)
        if not unidad:
            print("Unidad no encontrada")
            return jsonify({"error": "Unidad no encontrada"}), 404
        print("Unidad encontrada:", unidad.to_dict())

        # Actualizar campos básicos
        campos = ["marca", "vehiculo", "modelo", "clase_tipo", "niv",
                  "motor", "transmision", "combustible", "color",
                  "telefono_gps", "sim_gps", "uid", "propietario",
                  "compra_arrendado", "valor_factura", "kilometraje_actual"]
        for campo in campos:
            valor = data.get(campo)
            setattr(unidad, campo, valor)
            print(f"Campo {campo} actualizado a:", valor)

        # Fecha de adquisición
        fecha_adq = data.get("fecha_adquisicion")
        unidad.fecha_adquisicion = date.fromisoformat(fecha_adq) if fecha_adq else unidad.fecha_adquisicion
        print("Fecha de adquisición:", unidad.fecha_adquisicion)

        # Empresa y sucursal
        id_empresa = data.get("empresa")
        id_sucursal = data.get("sucursal")
        unidad.id_empresa = int(id_empresa) if id_empresa else unidad.id_empresa
        unidad.sucursal = int(id_sucursal) if id_sucursal else unidad.sucursal
        print("Empresa y sucursal actualizadas:", unidad.id_empresa, unidad.sucursal)

        # Función para guardar archivos
        def guardar_archivo_sobre(file_obj, carpeta, prefijo="archivo"):
            if not file_obj:
                return None
            ext = os.path.splitext(file_obj.filename)[1]
            filename = secure_filename(f"{prefijo}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}")
            path = os.path.join(carpeta, filename)
            file_obj.save(path)
            print(f"Archivo guardado: {filename} en {carpeta}")
            return f"{carpeta}/{filename}".replace("\\", "/")

        # Foto unidad
        foto = files.get("foto_unidad")
        if foto and allowed_image(foto.filename):
            unidad.url_foto = guardar_archivo_sobre(foto, UPLOAD_IMG, prefijo=f"unidad_{id_unidad}")
            print("URL foto unidad:", unidad.url_foto)

        # Factura
        pdf_factura = files.get("pdf_factura")
        if pdf_factura and allowed_pdf(pdf_factura.filename):
            unidad.url_factura = guardar_archivo_sobre(pdf_factura, UPLOAD_FACTURAS, prefijo=f"factura_{id_unidad}")
            print("URL factura:", unidad.url_factura)

        # Placas
        pdf_frontal = files.get("pdf_frontal")
        pdf_trasero = files.get("pdf_trasero")
        if any([data.get("placa"), data.get("folio"), data.get("fecha_expedicion"), data.get("fecha_vigencia"), pdf_frontal, pdf_trasero]):
            placa = unidad.placa or Placas()
            placa.placa = data.get("placa")
            placa.folio = data.get("folio")
            fecha_exp = data.get("fecha_expedicion")
            fecha_vig = data.get("fecha_vigencia")
            placa.fecha_expedicion = date.fromisoformat(fecha_exp) if fecha_exp else placa.fecha_expedicion
            placa.fecha_vigencia = date.fromisoformat(fecha_vig) if fecha_vig else placa.fecha_vigencia
            if pdf_frontal and allowed_pdf(pdf_frontal.filename):
                placa.url_placa_frontal = guardar_archivo_sobre(pdf_frontal, UPLOAD_PLACAS, prefijo=f"frontal_{id_unidad}")
            if pdf_trasero and allowed_pdf(pdf_trasero.filename):
                placa.url_placa_trasera = guardar_archivo_sobre(pdf_trasero, UPLOAD_PLACAS, prefijo=f"trasero_{id_unidad}")
            unidad.placa = placa
            print("Placas actualizadas:", placa.placa, placa.folio)

        # Guardar cambios
        db.session.commit()
        print("Unidad actualizada correctamente en la base de datos")

        return jsonify({"message": "Unidad actualizada correctamente", "unidad": unidad.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        print("Error al actualizar unidad:", str(e))
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

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



# Extensiones permitidas
ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_PDF_EXT = {'pdf'}

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXT

def allowed_pdf(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PDF_EXT


@app.route('/api/unidades', methods=['POST'])
def agregar_unidad():
    try:
        print("\n=== INICIO DE REGISTRO DE UNIDAD ===\n")

        # ----------------------------
        # Carpetas
        # ----------------------------
        UPLOAD_IMG = 'uploads/unidades_imagen'
        UPLOAD_PLACAS = 'uploads/placas'
        UPLOAD_FACTURAS = 'uploads/facturas'
        PAGO_DIR = 'uploads/pagos/'
        TARJETA_DIR = 'uploads/tarjetas_circulacion/'

        os.makedirs(UPLOAD_IMG, exist_ok=True)
        os.makedirs(UPLOAD_PLACAS, exist_ok=True)
        os.makedirs(UPLOAD_FACTURAS, exist_ok=True)
        os.makedirs(PAGO_DIR, exist_ok=True)
        os.makedirs(TARJETA_DIR, exist_ok=True)

        data = request.form
        print("=== DATA RECIBIDA ===")
        for key, value in data.items():
            print(f"{key}: {value}")

        print("\n=== FILES RECIBIDOS ===")
        for key, file in request.files.items():
            print(f"{key}: {file.filename}")
        print("========================\n")

        # ----------------------------
        # Validar sucursal y empresa
        # ----------------------------
        id_sucursal = data.get("sucursal")
        id_empresa = data.get("empresa")
        try:
            id_sucursal = int(id_sucursal)
            id_empresa = int(id_empresa)
        except (ValueError, TypeError):
            return jsonify({"error": "ID de sucursal o empresa inválido"}), 400

        sucursal_obj = db.session.get(Sucursal, id_sucursal)
        empresa_obj = db.session.get(Empresa, id_empresa)

        if not empresa_obj:
            return jsonify({"error": f"Empresa no encontrada. ID recibido: {id_empresa}"}), 400
        if not sucursal_obj:
            return jsonify({"error": f"Sucursal no encontrada. ID recibido: {id_sucursal}"}), 400
        if sucursal_obj.id_empresa != empresa_obj.id_empresa:
            return jsonify({"error": f"La sucursal {id_sucursal} no pertenece a la empresa {id_empresa}"}), 400

        # ----------------------------
        # Crear unidad
        # ----------------------------
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
            sucursal=id_sucursal,
            id_empresa=id_empresa,
            compra_arrendado=data.get("compra_arrendado"),
            fecha_adquisicion=date.fromisoformat(data.get("fecha_adquisicion")) if data.get("fecha_adquisicion") else None,
            valor_factura=data.get("valor_factura"),
            kilometraje_actual=data.get("kilometraje_actual")
        )

        # ----------------------------
        # Guardar imagen de unidad
        # ----------------------------
        img_file = request.files.get("foto_unidad")
        if img_file and allowed_image(img_file.filename):
            ext = os.path.splitext(img_file.filename)[1]
            filename = secure_filename(f"unidad_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}")
            abs_path = os.path.join(UPLOAD_IMG, filename)
            img_file.save(abs_path)
            nueva_unidad.url_foto = f"{UPLOAD_IMG}/{filename}".replace("\\", "/")
        elif img_file:
            return jsonify({"error": "La imagen debe ser JPG, JPEG, PNG o WEBP"}), 400

        # ----------------------------
        # Guardar PDF
        # ----------------------------
        def guardar_pdf_unico(file_obj, carpeta):
            if not file_obj or not allowed_pdf(file_obj.filename):
                return None
            ext = os.path.splitext(file_obj.filename)[1]
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}")
            abs_path = os.path.join(carpeta, filename)
            file_obj.save(abs_path)
            return f"{carpeta}/{filename}".replace("\\", "/")

        pdf_factura = request.files.get("pdf_factura")
        if pdf_factura:
            if not allowed_pdf(pdf_factura.filename):
                return jsonify({"error": "La factura debe ser PDF"}), 400
            nueva_unidad.url_factura = guardar_pdf_unico(pdf_factura, UPLOAD_FACTURAS)

        # ----------------------------
        # Guardar unidad en BD primero
        # ----------------------------
        db.session.add(nueva_unidad)
        db.session.commit()  # ahora nueva_unidad.id_unidad existe

        # ----------------------------
        # Guardar placas si hay datos o archivos
        # ----------------------------
        pdf_frontal = request.files.get("pdf_frontal")
        pdf_trasero = request.files.get("pdf_trasero")
        comprobante = request.files.get("comprobante")
        tarjeta = request.files.get("tarjeta_circulacion")

        if any([data.get("placa"), data.get("folio"), data.get("fecha_expedicion"),
                data.get("fecha_vigencia"), pdf_frontal, pdf_trasero, comprobante, tarjeta]):

            nueva_placa = Placas(
                id_unidad=nueva_unidad.id_unidad,
                folio=data.get("folio"),
                placa=data.get("placa"),
                fecha_expedicion=date.fromisoformat(data.get("fecha_expedicion")) if data.get("fecha_expedicion") else None,
                fecha_vigencia=date.fromisoformat(data.get("fecha_vigencia")) if data.get("fecha_vigencia") else None,
                url_placa_frontal=guardar_pdf_unico(pdf_frontal, UPLOAD_PLACAS),
                url_placa_trasera=guardar_pdf_unico(pdf_trasero, UPLOAD_PLACAS),
                url_comprobante_pago=guardar_pdf_unico(comprobante, PAGO_DIR),
                url_tarjeta_circulacion=guardar_pdf_unico(tarjeta, TARJETA_DIR),
                monto_pago=float(data.get("monto_pago") or 0)
            )
            db.session.add(nueva_placa)
            db.session.commit()

        # ----------------------------
        # Programar mantenimientos iniciales según la marca de la unidad
        # ----------------------------
        try:
            frecuencias = FrecuenciasPorMarca.query.filter_by(marca=nueva_unidad.marca).all()
            created = []
            for f in frecuencias:
                # Evitar duplicados por unidad y tipo de mantenimiento
                existe = MantenimientosProgramados.query.filter_by(
                    id_unidad=nueva_unidad.id_unidad,
                    id_tipo_mantenimiento=f.id_tipo_mantenimiento
                ).first()
                if existe:
                    continue

                proximo_fecha = date.today() + timedelta(days=f.frecuencia_tiempo)
                proximo_km = (nueva_unidad.kilometraje_actual or 0) + f.frecuencia_kilometraje

                mp = MantenimientosProgramados(
                    id_unidad=nueva_unidad.id_unidad,
                    id_tipo_mantenimiento=f.id_tipo_mantenimiento,
                    fecha_ultimo_mantenimiento=None,
                    kilometraje_ultimo=None,
                    proximo_mantenimiento=proximo_fecha,
                    proximo_kilometraje=proximo_km
                )
                db.session.add(mp)
                db.session.flush()  # para obtener id si es necesario
                created.append(mp.id_mantenimiento_programado)
            db.session.commit()
            print(f"Mantenimientos programados para la unidad {nueva_unidad.id_unidad}: {created}")
        except Exception as e:
            db.session.rollback()
            print(f"Error al programar mantenimientos iniciales: {e}")

        # ----------------------------
        # Retorno
        # ----------------------------
        return jsonify({
            "mensaje": "Unidad registrada exitosamente.",
            "unidad": nueva_unidad.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

        
import threading
from datetime import date
from flask_mail import Message

# Función para enviar correo en segundo plano
def enviar_correo_async(app, msg):
    with app.app_context():
        mail.send(msg)

@app.route('/asignaciones', methods=['POST'])
def crear_asignacion():
    data = request.get_json()
    id_chofer = data.get('id_chofer')
    id_unidad = data.get('id_unidad')
    usuario = data.get('usuario', 'sistema')
    fecha_asignacion = date.today()

    # Validaciones básicas
    if not id_chofer or not id_unidad:
        return jsonify({"error": "id_chofer y id_unidad son requeridos"}), 400

    # Validar que la unidad tenga placas
    placa_unidad = Placas.query.filter_by(id_unidad=id_unidad).first()

    if not Unidades or not placa_unidad or not placa_unidad.placa or placa_unidad.placa.strip() == "":
        return jsonify({"error": "La unidad no tiene una placa válida registrada"}), 400

    # Evitar duplicados exactos por fecha
    asignacion_existente = Asignaciones.query.filter_by(
        id_chofer=id_chofer,
        id_unidad=id_unidad,
        fecha_asignacion=fecha_asignacion
    ).first()

    if asignacion_existente:
        return jsonify({"error": "El chofer ya tiene asignada esta unidad en esta fecha"}), 400

    # Crear asignación
    nueva = Asignaciones(
        id_chofer=id_chofer,
        id_unidad=id_unidad,
        fecha_asignacion=fecha_asignacion
    )
    db.session.add(nueva)
    db.session.flush()  # Para obtener id_asignacion antes del commit

    # Registrar historial
    historial = HistorialAsignaciones(
        id_asignacion=nueva.id_asignacion,
        id_chofer=id_chofer,
        fecha_asignacion=fecha_asignacion,
        fecha_fin=None,
        usuario=usuario
    )
    db.session.add(historial)
    db.session.commit()

    # Enviar correo al chofer
    usuario_chofer = db.session.query(Usuarios).filter_by(id_chofer=id_chofer).first()
    if usuario_chofer and usuario_chofer.correo:
        msg = Message(
            subject="Nueva asignación de unidad",
            sender="tu-correo@dominio.com",
            recipients=[usuario_chofer.correo],
            body=f"Hola {usuario_chofer.nombre},\n\nSe te ha asignado la unidad: {unidad.vehiculo}.\nFecha de asignación: {fecha_asignacion.isoformat()}.\n\nSaludos."
        )
        threading.Thread(target=enviar_correo_async, args=(app, msg)).start()

    return jsonify({
        "message": "Asignación creada y correo enviado con documento",
        "id_asignacion": nueva.id_asignacion
    }), 201

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
        asignacion = Asignaciones.query.get(h.id_asignacion)
        unidad = Unidades.query.get(asignacion.id_unidad) if asignacion else None
        chofer = Choferes.query.get(asignacion.id_chofer) if asignacion else None

        salida.append({
            "id_historial": h.id_historial,
            "id_asignacion": h.id_asignacion,
            "id_unidad": unidad.id_unidad if unidad else None,  # <-- ID del vehículo
            "nombre_unidad": f"{unidad.marca} {unidad.vehiculo} {unidad.modelo}" if unidad else None,
            "id_chofer": chofer.id_chofer if chofer else None,
            "nombre_chofer": chofer.nombre if chofer else None,
            "fecha_asignacion": h.fecha_asignacion.isoformat() if h.fecha_asignacion else None,
            "fecha_fin": h.fecha_fin.isoformat() if h.fecha_fin else None,
            "usuario": h.usuario,
            "fecha_cambio": h.fecha_cambio.isoformat()
        })

    return jsonify(salida)



@app.route('/asignaciones', methods=['GET'])
def listar_asignaciones():
    asignaciones = Asignaciones.query.filter_by(fecha_fin=None).all()  # solo activas
    salida = []
    for a in asignaciones:
        salida.append({
            "id_asignacion": a.id_asignacion,
            "id_chofer": a.id_chofer,
            "id_unidad": a.id_unidad,
            "fecha_asignacion": a.fecha_asignacion.isoformat() if a.fecha_asignacion else None,
            "fecha_fin": a.fecha_fin.isoformat() if a.fecha_fin else None
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

    # Filtrar las que no están asignadas
    unidades_libres = [
        {
            "id_unidad": u.id_unidad,
            "nombre": f"{u.marca} {u.vehiculo} {u.modelo}"
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


@app.route('/chofer/unidad/<int:id_usuario>', methods=['GET'])
def obtener_datos_chofer_unidad(id_usuario):
    try:
        # Obtener el usuario
        usuario = db.session.get(Usuarios, id_usuario)
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        # Obtener el chofer asociado
        chofer = db.session.get(Choferes, usuario.id_chofer) if usuario.id_chofer else None
        if not chofer:
            return jsonify({'error': 'Chofer no encontrado'}), 404

        # Obtener la última asignación activa de unidad
        asignacion = (
            Asignaciones.query
            .filter_by(id_chofer=chofer.id_chofer)
            .filter((Asignaciones.fecha_fin == None) | (Asignaciones.fecha_fin >= date.today()))
            .order_by(Asignaciones.fecha_asignacion.desc())
            .first()
        )

        if not asignacion:
            return jsonify({'error': 'No tiene unidad asignada'}), 404

        # Obtener la unidad
        unidad = db.session.get(Unidades, asignacion.id_unidad)
        if not unidad:
            return jsonify({'error': 'Unidad no encontrada'}), 404

        # Usar to_dict() si está disponible y asegurarse de incluir id_unidad
        unidad_data = unidad.to_dict() if hasattr(unidad, 'to_dict') else {
            'id_unidad': unidad.id_unidad,
            'marca': unidad.marca,
            'vehiculo': unidad.vehiculo,
            'modelo': unidad.modelo,
            'color': unidad.color,
            'kilometraje_actual': unidad.kilometraje_actual,
            'url_imagen': getattr(unidad, 'url_imagen', None),
            'url_foto': getattr(unidad, 'url_foto', None),
        }
        # Aseguramos que exista la clave id_unidad (por si to_dict no la incluye)
        unidad_data['id_unidad'] = unidad.id_unidad

        # Preparar la respuesta completa
        response = {
            "usuario": {
                "id_usuario": usuario.id_usuario,
                "nombre": usuario.nombre,
                "usuario": usuario.usuario,
                "correo": usuario.correo,
                "rol": usuario.rol,
                "estado": usuario.estado,
                "fecha_registro": str(usuario.fecha_registro),
                "fecha_ultimo_login": str(usuario.fecha_ultimo_login) if usuario.fecha_ultimo_login else None,
            },
            "chofer": {
                "id_chofer": chofer.id_chofer,
                "nombre": chofer.nombre,
                "curp": chofer.curp,
                "calle": chofer.calle,
                "colonia_localidad": chofer.colonia_localidad,
                "codpos": chofer.codpos,
                "municipio": chofer.municipio,
                "licencia_folio": chofer.licencia_folio,
                "licencia_tipo": chofer.licencia_tipo,
                "licencia_vigencia": str(chofer.licencia_vigencia) if chofer.licencia_vigencia else None
            },
            "unidad": unidad_data
        }

        return jsonify(response)

    except Exception as e:
        print("Error en obtener_datos_chofer_unidad:", e)
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

        # Obtener filtros desde query params
        unidad = request.args.get('unidad')
        chofer = request.args.get('chofer')
        aseguradora = request.args.get('aseguradora')
        tipo_garantia = request.args.get('tipo_garantia')

        # Base query
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
                g.prima,
                g.telefono_fijo,
                g.telefono_celular
            FROM Garantias g
            JOIN Unidades u ON g.id_unidad = u.id_unidad
            LEFT JOIN (
                SELECT id_unidad, id_chofer
                FROM Asignaciones
                WHERE fecha_fin IS NULL
            ) A ON u.id_unidad = A.id_unidad
            LEFT JOIN Choferes C ON A.id_chofer = C.id_chofer
            WHERE 1=1
        """


        # Lista de parámetros para query parametrizada
        params = []

        if unidad:
            query += " AND g.id_unidad = %s"
            params.append(unidad)
        if chofer:
            query += " AND C.nombre LIKE %s"
            params.append(f"%{chofer}%")
        if aseguradora:
            query += " AND g.aseguradora LIKE %s"
            params.append(f"%{aseguradora}%")
        if tipo_garantia:
            query += " AND g.tipo_garantia LIKE %s"
            params.append(f"%{tipo_garantia}%")

        query += " ORDER BY u.id_unidad, g.id_garantia;"

        # Ejecutar query con parámetros
        cursor.execute(query, params)
        garantias = cursor.fetchall()
        columnas = [desc[0] for desc in cursor.description]
        resultados = []

        for fila in garantias:
            fila_dict = dict(zip(columnas, fila))
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

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'webp'}

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
        return jsonify({"error": "Debe subir un archivo"}), 400
    if not allowed_file(archivo.filename):
        return jsonify({"error": "Solo se permiten archivos PDF o imágenes"}), 400

    id_unidad = data.get('id_unidad')
    if not id_unidad:
        return jsonify({"error": "Debe especificar una unidad"}), 400

    # ------------------- Recibir teléfonos -------------------
    telefono_fijo = data.get('telefono_fijo')
    telefono_celular = data.get('telefono_celular')
    # ---------------------------------------------------------

    garantia = Garantias.query.filter_by(id_unidad=id_unidad).first()

    # Generar nombre de archivo único con fecha y hora
    ahora = datetime.now()
    timestamp = ahora.strftime("%Y-%m-%d_%H-%M-%S")  # YYYY-MM-DD_HH-MM-SS
    ext = os.path.splitext(archivo.filename)[1].lower()
    filename = secure_filename(f"{id_unidad}_{timestamp}{ext}")

    ruta_guardado_abs = os.path.join(ruta_upload_abs, filename)
    archivo.save(ruta_guardado_abs)

    # Ruta relativa para DB/frontend
    ruta_archivo = "/" + os.path.join(UPLOAD_FOLDER, filename).replace("\\", "/")

    try:
        def mover_a_historial(ruta_relativa):
            if not ruta_relativa:
                return None
            ruta_abs = os.path.join(current_app.root_path, ruta_relativa.lstrip("/").replace("/", os.sep))
            if os.path.exists(ruta_abs):
                nombre = os.path.basename(ruta_abs)
                nueva_ruta_abs = os.path.join(ruta_historial_abs, nombre)
                shutil.move(ruta_abs, nueva_ruta_abs)
                return "/" + os.path.join(HISTORIAL_FOLDER, nombre).replace("\\", "/")
            return ruta_relativa

        hoy = date.today()
        puede_renovar = False

        if garantia and garantia.vigencia:
            fecha_pre_renovacion = garantia.vigencia - timedelta(days=30)
            puede_renovar = hoy >= fecha_pre_renovacion

        # ---------------- Garantía existente y puede renovarse ----------------
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
                usuario=data.get('usuario', 'sistema'),
                # ---------------- Guardar teléfonos en historial ----------------
                telefono_fijo=garantia.telefono_fijo,
                telefono_celular=garantia.telefono_celular
            )
            db.session.add(historial)

            # Actualizar con nuevos datos
            garantia.aseguradora = data.get('aseguradora')
            garantia.tipo_garantia = data.get('tipo_garantia')
            garantia.no_poliza = data.get('no_poliza')
            garantia.url_poliza = ruta_archivo
            garantia.suma_asegurada = data.get('suma_asegurada')
            garantia.inicio_vigencia = data.get('inicio_vigencia')
            garantia.vigencia = data.get('vigencia')
            garantia.prima = data.get('prima')
            # ---------------- Guardar teléfonos en la garantía actual ----------------
            garantia.telefono_fijo = telefono_fijo
            garantia.telefono_celular = telefono_celular
            print("Garantía actualizada y enviada a historial (vencida o pre-renovación)")

        # ---------------- Crear nueva garantía ----------------
        elif not garantia:
            nueva = Garantias(
                id_unidad=id_unidad,
                aseguradora=data.get('aseguradora'),
                tipo_garantia=data.get('tipo_garantia'),
                no_poliza=data.get('no_poliza'),
                url_poliza=ruta_archivo,
                suma_asegurada=data.get('suma_asegurada'),
                inicio_vigencia=data.get('inicio_vigencia'),
                vigencia=data.get('vigencia'),
                prima=data.get('prima'),
                # ---------------- Guardar teléfonos ----------------
                telefono_fijo=telefono_fijo,
                telefono_celular=telefono_celular
            )
            db.session.add(nueva)
            print("Nueva garantía creada")

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

    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'webp'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    data = request.form
    archivo = request.files.get('archivo')

    conn = db.engine.raw_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id_garantia, url_poliza FROM Garantias WHERE id_garantia = %s",
            (id_garantia,)
        )
        garantia_existente = cursor.fetchone()
        if not garantia_existente:
            return jsonify({"error": "La garantía no existe"}), 404

        id_unidad = data.get('id_unidad')
        cursor.execute("SELECT id_unidad FROM Unidades WHERE id_unidad = %s", (id_unidad,))
        if not cursor.fetchone():
            return jsonify({"error": "La unidad indicada no existe"}), 400

        url_poliza = garantia_existente[1]

        if archivo and allowed_file(archivo.filename):
            if url_poliza:
                ruta_antigua = os.path.join(app.root_path, url_poliza.lstrip("/").replace("/", os.sep))
                if os.path.exists(ruta_antigua):
                    os.remove(ruta_antigua)

            ext = archivo.filename.rsplit('.', 1)[1].lower()
            filename = f"{data.get('no_poliza')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            archivo.save(filepath)
            url_poliza = f"/uploads/garantias/{filename}"

        suma_asegurada = float(data.get('suma_asegurada') or 0)
        prima = float(data.get('prima') or 0)

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
                url_poliza = %s,
                telefono_fijo = %s,
                telefono_celular = %s
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
            data.get('telefono_fijo'),      # nuevo
            data.get('telefono_celular'),    # nuevo
            id_garantia
        )
        cursor.execute(query, params)
        conn.commit()

        return jsonify({"message": "Garantía actualizada correctamente", "url_poliza": url_poliza}), 200

    except Exception as e:
        conn.rollback()
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

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
            "prima": garantia.prima,
            "telefono_fijo": garantia.telefono_fijo,
            "telefono_celular": garantia.telefono_celular

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

#hitorial de garantias
@app.route('/api/historial_garantias', methods=['GET'])
def get_historial_garantias():
    """
    Obtiene todos los registros de la tabla HistorialGarantias
    junto con los datos de la unidad (marca, tipo) si están relacionados.
    """
    try:
        # Si tienes relación con Unidades, puedes hacer join; si no, omite el join.
        historial = HistorialGarantias.query.all()

        resultado = []
        for h in historial:
            resultado.append({
                "id_historial": h.id_historial,
                "id_garantia": h.id_garantia,
                "id_unidad": h.id_unidad,
                "fecha_cambio": h.fecha_cambio.strftime("%Y-%m-%d %H:%M:%S") if h.fecha_cambio else None,
                "aseguradora": h.aseguradora,
                "tipo_garantia": h.tipo_garantia,
                "no_poliza": h.no_poliza,
                "url_poliza": h.url_poliza,
                "telefono_fijo": h.telefono_fijo,
                "telefono_celular": h.telefono_celular,
                "suma_asegurada": str(h.suma_asegurada),
                "inicio_vigencia": h.inicio_vigencia.strftime("%Y-%m-%d") if h.inicio_vigencia else None,
                "vigencia": h.vigencia.strftime("%Y-%m-%d") if h.vigencia else None,
                "prima": str(h.prima),
                "usuario": h.usuario
            })

        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



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
        return jsonify({"error": "Debe subir un archivo"}), 400

    # Permitir PDF e imágenes
    ext = os.path.splitext(archivo.filename)[1].lower()
    permitidos = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
    if ext not in permitidos:
        return jsonify({"error": "Solo se permiten archivos PDF o imágenes"}), 400

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

    filename = secure_filename(f"{data['id_unidad']}_{periodo}_{date.today()}{ext}")
    ruta_guardado_abs = os.path.join(ruta_upload_abs, filename)
    archivo.save(ruta_guardado_abs)
    ruta_archivo = os.path.join(UPLOAD_FOLDER, filename).replace("\\", "/")
    print(f"Archivo guardado en: {ruta_guardado_abs}")
    print(f"Ruta relativa para DB/frontend: {ruta_archivo}")

    existing = VerificacionVehicular.query.filter_by(id_unidad=data['id_unidad']).first()
    print("Verificación existente:", existing)

    try:
        def mover_a_historial(ruta_relativa):
            if not ruta_relativa or ruta_relativa == ruta_archivo:
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
                existing.url_verificacion_1 = ruta_archivo
            else:
                existing.periodo_2 = fecha_sugerida
                existing.periodo_2_real = fecha_real
                existing.url_verificacion_2 = ruta_archivo

            existing.ultima_verificacion = fecha_real
            existing.holograma = holograma
            existing.folio_verificacion = data.get('folio_verificacion', '')
            existing.engomado = engomado
            print("Verificación existente actualizada con nuevo archivo")

            # --- MARCAR ALERTAS EXISTENTES COMO COMPLETADAS ---
            try:
                alertas_pendientes = Alerta.query.filter_by(
                    id_unidad=data['id_unidad'],
                    tipo_alerta='verificacion',
                    estado='pendiente'
                ).all()

                for alerta in alertas_pendientes:
                    alerta.estado = 'completada'
                    alerta.fecha_completada = datetime.now()

                if alertas_pendientes:
                    print(f"✅ {len(alertas_pendientes)} alertas de verificación existentes marcadas como completadas")
            except Exception as e:
                print("⚠️ Error al marcar alertas como completadas:", e)

        else:
            nueva = VerificacionVehicular(
                id_unidad=data['id_unidad'],
                ultima_verificacion=fecha_real,
                periodo_1=fecha_sugerida if periodo == '1' else None,
                periodo_1_real=fecha_real if periodo == '1' else None,
                periodo_2=fecha_sugerida if periodo == '2' else None,
                periodo_2_real=fecha_real if periodo == '2' else None,
                url_verificacion_1=ruta_archivo if periodo == '1' else None,
                url_verificacion_2=ruta_archivo if periodo == '2' else None,
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

@app.route('/api/verificaciones/<int:id_verificacion>', methods=['DELETE'])
def eliminar_verificacion(id_verificacion):
    UPLOAD_FOLDER = 'uploads/verificaciones'
    HISTORIAL_FOLDER = 'uploads/historial_verificaciones'

    ruta_upload_abs = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    ruta_historial_abs = os.path.join(current_app.root_path, HISTORIAL_FOLDER)
    os.makedirs(ruta_upload_abs, exist_ok=True)
    os.makedirs(ruta_historial_abs, exist_ok=True)

    verificacion = VerificacionVehicular.query.get(id_verificacion)
    if not verificacion:
        print(f"Verificación con id {id_verificacion} no encontrada")
        return jsonify({"error": "Verificación no encontrada"}), 404

    print(f"=== Eliminando verificación ID {verificacion.id_verificacion} ===")
    print(f"Unidad: {verificacion.id_unidad}, Última verificación: {verificacion.ultima_verificacion}")
    print(f"Periodo 1: {verificacion.periodo_1}, URL: {verificacion.url_verificacion_1}")
    print(f"Periodo 2: {verificacion.periodo_2}, URL: {verificacion.url_verificacion_2}")
    print(f"Holograma: {verificacion.holograma}, Folio: {verificacion.folio_verificacion}, Engomado: {verificacion.engomado}")

    # Función para mover archivos
    def mover_archivo_a_historial(url_relativa):
        if not url_relativa:
            print("No hay archivo para mover")
            return None
        ruta_abs = os.path.join(current_app.root_path, url_relativa.lstrip("/").replace("/", os.sep))
        if os.path.exists(ruta_abs):
            nombre = os.path.basename(ruta_abs)
            nueva_ruta_abs = os.path.join(ruta_historial_abs, nombre)
            shutil.move(ruta_abs, nueva_ruta_abs)
            print(f"Archivo movido a historial: {nueva_ruta_abs}")
            return os.path.join(HISTORIAL_FOLDER, nombre).replace("\\", "/")
        print(f"Archivo no encontrado para mover: {ruta_abs}")
        return url_relativa

    url_v1 = mover_archivo_a_historial(verificacion.url_verificacion_1)
    url_v2 = mover_archivo_a_historial(verificacion.url_verificacion_2)

    historial = HistorialVerificacionVehicular(
        id_verificacion=verificacion.id_verificacion,
        id_unidad=verificacion.id_unidad,
        fecha_cambio=datetime.now(),
        ultima_verificacion=verificacion.ultima_verificacion,
        periodo_1=verificacion.periodo_1,
        periodo_1_real=verificacion.periodo_1_real,
        url_verificacion_1=url_v1,
        periodo_2=verificacion.periodo_2,
        periodo_2_real=verificacion.periodo_2_real,
        url_verificacion_2=url_v2,
        holograma=verificacion.holograma,
        folio_verificacion=verificacion.folio_verificacion,
        engomado=verificacion.engomado,
        usuario="sistema"
    )

    db.session.add(historial)
    print("Registro agregado al historial")

    # Borrar verificación original
    db.session.delete(verificacion)
    db.session.commit()
    print(f"Verificación ID {id_verificacion} eliminada y commit realizado")

    return jsonify({"message": "Verificación eliminada y enviada a historial"}), 200


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


#====================================================

#calculo de verificaciones refrendo
#========================================================
import calendar
from datetime import timedelta

def calcular_siguiente_verificacion(fecha_real, holograma, engomado):
    print("----------------------------------------------------")
    print("CÁLCULO DE VERIFICACIÓN")
    print(f"Fecha real: {fecha_real}")
    print(f"Holograma: {holograma}")
    print(f"Engomado: {engomado}")
    print("----------------------------------------------------")

    if not fecha_real:
        print("SIN FECHA REAL → SE REGRESA None")
        return None

    engomado = engomado.strip().lower()
    holograma = holograma.strip()

    print(f"Engomado normalizado: {engomado}")
    print(f"Holograma normalizado: {holograma}")

    # HOLOGRAMA 00
    if holograma == "00":
        print("Regla: HOLOGRAMA 00 → +2 AÑOS")
        try:
            resultado = fecha_real.replace(year=fecha_real.year + 2)
            print(f"Resultado: {resultado}")
            return resultado
        except ValueError:
            ultimo_dia = calendar.monthrange(fecha_real.year + 2, fecha_real.month)[1]
            resultado = fecha_real.replace(year=fecha_real.year + 2, day=ultimo_dia)
            print(f"Resultado ajustado: {resultado}")
            return resultado

    # HOLOGRAMA 0
    if holograma == "0":
        print("Regla: HOLOGRAMA 0 → +6 MESES")
        mes_siguiente = fecha_real.month + 6
        año = fecha_real.year
        if mes_siguiente > 12:
            mes_siguiente -= 12
            año += 1

        ultimo_dia = calendar.monthrange(año, mes_siguiente)[1]
        dia = min(fecha_real.day, ultimo_dia)

        resultado = fecha_real.replace(year=año, month=mes_siguiente, day=dia)
        print(f"Resultado: {resultado}")
        return resultado

    # HOLOGRAMAS 1 Y 2 (NORMA POR ENGOMADO)
    print("Regla: HOLOGRAMAS 1/2 → POR ENGOMADO")

    MESES_ENGOMADO = {
        "primer_semestre": {
            "amarillo": [1, 2],
            "rosa": [2, 3],
            "rojo": [3, 4],
            "verde": [4, 5],
            "azul": [5, 6],
        },
        "segundo_semestre": {
            "amarillo": [7, 8],
            "rosa": [8, 9],
            "rojo": [9, 10],
            "verde": [10, 11],
            "azul": [11, 12],
        }
    }

    mes_actual = fecha_real.month
    semestre = "primer_semestre" if mes_actual <= 6 else "segundo_semestre"

    print(f"Mes actual: {mes_actual}")
    print(f"Semestre detectado: {semestre}")

    meses_posibles = MESES_ENGOMADO.get(semestre, {}).get(engomado, [])
    print(f"Meses posibles por engomado: {meses_posibles}")

    if not meses_posibles:
        print("NO HAY MESES POSIBLES → FALLBACK +182 días")
        resultado = fecha_real + timedelta(days=182)
        print(f"Resultado: {resultado}")
        return resultado

    # Buscar primer mes válido
    for mes in meses_posibles:
        if mes >= mes_actual:
            mes_siguiente = mes
            print(f"Primer mes válido encontrado: {mes_siguiente}")
            break
    else:
        print("No hay mes válido en este semestre → siguiente semestre")
        semestre_siguiente = (
            "segundo_semestre" if semestre == "primer_semestre" else "primer_semestre"
        )
        mes_siguiente = MESES_ENGOMADO[semestre_siguiente][engomado][0]
        print(f"Mes del siguiente semestre: {mes_siguiente}")

    año = fecha_real.year + (1 if mes_siguiente < mes_actual else 0)
    ultimo_dia = calendar.monthrange(año, mes_siguiente)[1]
    dia = min(fecha_real.day, ultimo_dia)

    resultado = fecha_real.replace(year=año, month=mes_siguiente, day=dia)

    print(f"Año asignado: {año}")
    print(f"Día ajustado: {dia}")
    print(f"Resultado final: {resultado}")
    print("----------------------------------------------------")

    return resultado

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

#================================================================
#Alertas de verificacion vehicular
#================================================================

def enviar_alertas_verificacion():
    print("📌 Iniciando envío de alertas de verificación")
    hoy = date.today()
    anticipacion = timedelta(days=60)  # 2 meses antes

    # --- 1. Traer todas las verificaciones ---
    verificaciones = VerificacionVehicular.query.all()
    print(f"Total verificaciones encontradas: {len(verificaciones)}")

    proximas_alertas = []

    for v in verificaciones:
        if not v.ultima_verificacion:
            continue

        fecha_siguiente = calcular_siguiente_verificacion(
            v.ultima_verificacion,
            v.holograma,
            v.engomado
        )

        if not fecha_siguiente:
            continue

        # Guardar fecha siguiente en la verificación (opcional)
        v.proxima_verificacion = fecha_siguiente  # Si agregas este campo en el modelo
        # db.session.commit()  # Mejor hacerlo al final

        if hoy + anticipacion >= fecha_siguiente:
            proximas_alertas.append((v, fecha_siguiente))

    print(f"Verificaciones próximas (alerta): {len(proximas_alertas)}")
    if not proximas_alertas:
        print("❌ No hay verificaciones próximas")
        return

    # --- 2. Administradores ---
    admins = Usuarios.query.filter_by(rol='admin').all()
    emails_admin = [a.correo for a in admins if a.correo]
    print(f"Administradores con correo: {emails_admin}")

    if emails_admin:
        lista_admin_html = "".join([
            f"<li>Unidad: <strong>{v.unidad.id_unidad}</strong> | "
            f"Próxima verificación: {fecha} | "
            f"Holograma: {v.holograma} | Engomado: {v.engomado}</li>"
            for v, fecha in proximas_alertas
        ])
        cuerpo_admin = f"<html><body><h2>Vehículos próximos a verificación</h2><ul>{lista_admin_html}</ul></body></html>"
        msg_admin = Message(
            subject="Listado de vehículos próximos a verificación",
            recipients=emails_admin,
            html=cuerpo_admin
        )
        mail.send(msg_admin)
        print(f"✅ Correos enviados a administradores: {emails_admin}")

        # Crear alertas en BD para admins
        for v, fecha in proximas_alertas:
            alerta = Alerta(
                id_unidad=v.id_unidad,
                tipo_alerta="verificacion",
                descripcion=f"Unidad {v.unidad.id_unidad} requiere verificación antes del {fecha}",
                estado="pendiente",
                detalle={
                    "rol": "admin",
                    "holograma": v.holograma,
                    "engomado": v.engomado
                }
            )
            db.session.add(alerta)


    # --- 3. Choferes ---
    choferes = Usuarios.query.filter_by(rol='chofer').all()
    for user in choferes:
        if not user.correo:
            continue

        # Vehículos asignados al chofer
        asignaciones_activas = Asignaciones.query.filter(
            Asignaciones.id_chofer == user.id_chofer,
            (Asignaciones.fecha_fin == None) | (Asignaciones.fecha_fin >= hoy)
        ).all()
        unidades_usuario = [a.id_unidad for a in asignaciones_activas]

        vehiculos_usuario = [(v, fecha) for v, fecha in proximas_alertas if v.id_unidad in unidades_usuario]

        if not vehiculos_usuario:
            continue

        lista_usuario_html = "".join([
            f"<li>Unidad: <strong>{v.unidad.id_unidad}</strong> | "
            f"Próxima verificación: {fecha} | "
            f"Holograma: {v.holograma} | Engomado: {v.engomado}</li>"
            for v, fecha in vehiculos_usuario
        ])
        cuerpo_usuario = f"<html><body><h2>Vehículos de sus unidades próximos a verificación</h2><ul>{lista_usuario_html}</ul></body></html>"
        msg_usuario = Message(
            subject="Próxima verificación de sus unidades",
            recipients=[user.correo],
            html=cuerpo_usuario
        )
        mail.send(msg_usuario)
        print(f"✅ Correo enviado a chofer {user.id_chofer} - {user.correo}")

        # Crear alertas en BD para chofer
        for v, fecha in vehiculos_usuario:
            alerta = Alerta(
                id_unidad=v.id_unidad,
                tipo_alerta="verificacion",
                descripcion=f"Su unidad {v.unidad.id_unidad} requiere verificación antes del {fecha}",
                estado="pendiente",
                detalle={
                    "rol": "chofer",
                    "id_chofer": user.id_chofer,
                    "holograma": v.holograma,
                    "engomado": v.engomado
                }
            )
            db.session.add(alerta)


    # Commit final para todas las alertas
    db.session.commit()
    print("✅ Envío de alertas de verificación completado")

# ---------------------------
# Scheduler diario
# ---------------------------
scheduler = BackgroundScheduler()

def job_envio_alertas_verificacion():
    with app.app_context():  # Contexto de Flask activo
        print("📌 Iniciando envío de alertas")
        try:
            enviar_alertas_verificacion()
            print("✅ Alertas enviadas correctamente")
        except Exception as e:
            print(f"❌ Error al enviar alertas: {e}")

# Ejecutar cada 100 segundos
scheduler.add_job(job_envio_alertas_verificacion, 'interval', seconds=45060)
scheduler.start()




# ===============================================================================================
# SOLICITUDES DE FALLA MECÁNICA
# ===============================================================================================

@app.route('/solicitudes/chofer/<int:id_chofer>', methods=['GET'])
def solicitudes_chofer(id_chofer):
    solicitudes = SolicitudFalla.query.filter_by(id_chofer=id_chofer).all()
    resultado = []
    for s in solicitudes:
        falla_existente = FallaMecanica.query.filter_by(
            id_unidad=s.id_unidad,
            id_pieza=s.id_pieza,
            tipo_servicio=s.tipo_servicio
        ).first()

        # Consultar nombres
        unidad = Unidades.query.get(s.id_unidad)
        pieza = Piezas.query.get(s.id_pieza)
        marca = MarcasPiezas.query.get(s.id_marca)

        resultado.append({
            "id_solicitud": s.id_solicitud,
            "id_unidad": s.id_unidad,
            "unidad": unidad.vehiculo if unidad else "No especificada",
            "id_pieza": s.id_pieza,
            "pieza": pieza.nombre_pieza if pieza else "No especificada",
            "id_marca": s.id_marca,
            "marca": marca.nombre_marca if marca else "No especificada",
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
    solicitudes = SolicitudFalla.query.order_by(SolicitudFalla.fecha_solicitud.desc()).all()
    resultado = []

    for s in solicitudes:
        unidad = db.session.get(Unidades, s.id_unidad)
        pieza = db.session.get(Piezas, s.id_pieza)
        marca = db.session.get(MarcasPiezas, s.id_marca)
        chofer = db.session.get(Usuarios, s.id_chofer)  # obtenemos el chofer

        resultado.append({
            "id_solicitud": s.id_solicitud,
            "id_unidad": s.id_unidad,
            "unidad": unidad.vehiculo if unidad else "No especificada",
            "id_pieza": s.id_pieza,
            "pieza": pieza.nombre_pieza if pieza else "No especificada",
            "id_marca": s.id_marca,
            "marca": marca.nombre_marca if marca else "No especificada",
            "tipo_servicio": s.tipo_servicio,
            "descripcion": s.descripcion,
            "estado": s.estado,
            "id_chofer": s.id_chofer,
            "chofer": {"nombre": chofer.nombre} if chofer else None,
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



# -------------------------------
# Crear mensaje para una solicitud
# -------------------------------
@app.route('/solicitudes_mensajes', methods=['POST'])
def crear_mensaje_solicitud():
    """
    Espera JSON: { id_solicitud, id_usuario, mensaje }
    """
    data = request.json
    id_solicitud = data.get('id_solicitud')
    id_usuario = data.get('id_usuario')
    mensaje = data.get('mensaje')

    print("Datos recibidos:", data)

    if not id_solicitud or not id_usuario or not mensaje:
        print("Error: faltan datos")
        return jsonify({"msg": "Faltan datos"}), 400

    # Verificar que la solicitud exista
    solicitud = SolicitudFalla.query.get(id_solicitud)
    if not solicitud:
        return jsonify({"msg": "La solicitud no existe"}), 404

    nuevo_mensaje = SolicitudFallaMensajes(
        id_solicitud=id_solicitud,
        id_usuario=id_usuario,
        mensaje=mensaje,
        fecha=datetime.utcnow()
    )

    db.session.add(nuevo_mensaje)
    db.session.commit()

    return jsonify({"msg": "Mensaje enviado correctamente", "id_mensaje": nuevo_mensaje.id_mensaje}), 201


# -------------------------------
# Rechazar una solicitud (ADMIN)
# -------------------------------
@app.route('/solicitudes/<int:id_solicitud>/rechazar', methods=['POST'])
def rechazar_solicitud(id_solicitud):
    """
    Actualiza estado a 'rechazada' y guarda la razón de rechazo
    """
    data = request.json
    razon_rechazo = data.get('razon_rechazo')

    if not razon_rechazo:
        return jsonify({"msg": "Falta el motivo de rechazo"}), 400

    solicitud = SolicitudFalla.query.get_or_404(id_solicitud)
    solicitud.estado = 'rechazada'
    solicitud.razon_rechazo = razon_rechazo  # Asegúrate de tener esta columna en tu modelo

    db.session.commit()

    return jsonify({"msg": "Solicitud rechazada y mensaje enviado al chofer"})  


@app.route("/mis_mensajes/<int:id_chofer>", methods=["GET"])
def mis_mensajes(id_chofer):
    # Incluir solicitudes rechazadas y pendientes
    solicitudes = SolicitudFalla.query.filter(
        SolicitudFalla.id_chofer == id_chofer,
        SolicitudFalla.estado.in_(["rechazada", "pendiente"])
    ).all()

    mensajes_res = []

    for s in solicitudes:
        mensajes = SolicitudFallaMensajes.query.filter_by(id_solicitud=s.id_solicitud)\
            .order_by(SolicitudFallaMensajes.fecha.asc()).all()

        msgs_formateados = []
        for m in mensajes:
            quien = "chofer" if m.id_usuario == id_chofer else "admin"
            msgs_formateados.append({
                "id_mensaje": m.id_mensaje,
                "mensaje": m.mensaje,
                "archivo_adjunto": m.archivo_adjunto,
                "fecha": m.fecha,
                "quien": quien
            })

        if msgs_formateados:  # Solo agregar solicitudes con mensajes
            mensajes_res.append({
                "id_solicitud": s.id_solicitud,
                "tipo_servicio": s.tipo_servicio,
                "mensajes": msgs_formateados,
                "estado": s.estado
            })

    return jsonify(mensajes_res)

#/fallas_mensajes/usuario/





@app.route("/uploads/mensajes/<filename>")
def subir_mensajes(filename):
    return send_from_directory("uploads/mensajes", filename)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/solicitudes_mensajes/responder", methods=["POST"])
def responder_solicitud():
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads/mensajes")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "webm", "ogg", "pdf"}
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    id_solicitud = request.form.get("id_solicitud")
    id_usuario = request.form.get("id_usuario")
    mensaje = request.form.get("mensaje")
    archivo = request.files.get("archivo")

    print("===== Datos recibidos =====")
    print("id_solicitud:", id_solicitud)
    print("id_usuario:", id_usuario)
    print("mensaje:", mensaje)
    print("archivo:", archivo)
    if archivo:
        print("Nombre original del archivo:", archivo.filename)

    if not id_solicitud or not id_usuario or not mensaje:
        return jsonify({"msg": "Faltan datos obligatorios"}), 400

    solicitud = SolicitudFalla.query.get(id_solicitud)
    if not solicitud:
        return jsonify({"msg": "Solicitud no encontrada"}), 404

    archivo_nombre = None
    if archivo and allowed_file(archivo.filename):
        filename = secure_filename(f"{datetime.utcnow().timestamp()}_{archivo.filename}")
        ruta_completa = os.path.join(UPLOAD_FOLDER, filename)
        archivo.save(ruta_completa)
        archivo_nombre = filename
        print("Archivo guardado en:", ruta_completa)

    # Crear mensaje
    nuevo_mensaje = SolicitudFallaMensajes(
        id_solicitud=id_solicitud,
        id_usuario=id_usuario,
        mensaje=mensaje,
        archivo_adjunto=archivo_nombre
    )

    db.session.add(nuevo_mensaje)

    # Si quieres, puedes reactivar la solicitud solo si estaba rechazada
    if solicitud.estado == "rechazada":
        solicitud.estado = "pendiente"

    db.session.commit()

    print("Mensaje creado con ID:", nuevo_mensaje.id_mensaje)
    return jsonify({"msg": "Respuesta enviada correctamente"})

@app.route("/solicitudes/<int:id_solicitud>/mensajes_admin", methods=["GET"])
def obtener_mensajes(id_solicitud):
    try:
        # Obtener la solicitud (esto ya valida existencia)
        solicitud = SolicitudFalla.query.get_or_404(id_solicitud)

        # Optimizar: cargar mensajes + usuario en una sola consulta JOIN
        mensajes = (
            db.session.query(SolicitudFallaMensajes, Usuarios)
            .join(Usuarios, SolicitudFallaMensajes.id_usuario == Usuarios.id_usuario)
            .filter(SolicitudFallaMensajes.id_solicitud == id_solicitud)
            .order_by(SolicitudFallaMensajes.fecha.asc())
            .all()
        )

        result = []
        for m, usuario in mensajes:
            result.append({
                "id_mensaje": m.id_mensaje,
                "mensaje": m.mensaje,
                "archivo_adjunto": m.archivo_adjunto,
                "fecha": m.fecha.isoformat(),
                "id_usuario": m.id_usuario,
                "rol": usuario.rol,
                "nombre": usuario.nombre
            })

        return jsonify(result)

    finally:
        # Importante para evitar saturar el pool
        db.session.remove()



####################################

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    # Carpeta 'uploads' absoluta
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')  # Ajusta si tu carpeta está en otro lugar

    # filename puede ser 'fallasmecanicas/falla_24.pdf'
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)

from flask import jsonify
from sqlalchemy.orm import joinedload
from datetime import datetime

@app.route('/fallas/chofer/<int:id_usuario>', methods=['GET'])
def fallas_por_chofer(id_usuario):
    usuario = db.session.get(Usuarios, id_usuario)
    if not usuario or not usuario.id_chofer:
        return jsonify([])

    asignacion = Asignaciones.query.filter_by(id_chofer=usuario.id_chofer, fecha_fin=None).first()
    if not asignacion:
        return jsonify([])

    fallas = FallaMecanica.query.filter_by(id_unidad=asignacion.id_unidad).all()
    resultado = []

    for f in fallas:
        unidad = Unidades.query.get(f.id_unidad)
        pieza = Piezas.query.get(f.id_pieza)
        marca = MarcasPiezas.query.get(f.id_marca)
        lugar = LugarReparacion.query.get(f.id_lugar)

        resultado.append({
            "id_falla": f.id_falla,
            "id_unidad": f.id_unidad,
            "id_pieza": f.id_pieza,
            "id_marca": f.id_marca,
            "id_lugar": f.id_lugar,

            "unidad": unidad.vehiculo if unidad else "No especificada",
            "pieza": pieza.nombre_pieza if pieza else "No especificada",
            "marca": marca.nombre_marca if marca else "No especificada",
            "lugar_reparacion": lugar.nombre_lugar if lugar else "No especificado",

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

#========================================================================================================
#Placas
#========================================================================================================

@app.route('/placas', methods=['GET'])
def get_placas():
    try:
        search = request.args.get('search', "", type=str)
        id_unidad = request.args.get('id_unidad', type=int)

        query = Placas.query

        # Filtro de búsqueda por placa o folio
        if search:
            query = query.filter(
                (Placas.placa.ilike(f"%{search}%")) |
                (Placas.folio.ilike(f"%{search}%"))
            )

        # Filtro por unidad
        if id_unidad:
            query = query.filter_by(id_unidad=id_unidad)

        # Orden por ID descendente
        query = query.order_by(Placas.id_placa.desc())

        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        placas_query = query.paginate(page=page, per_page=per_page, error_out=False)

        placas = [p.to_dict() for p in placas_query.items]

        return jsonify({
            "total": placas_query.total,
            "page": page,
            "per_page": per_page,
            "placas": placas
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
    print("📌 Iniciando envío de alertas")
    hoy = date.today()
    seis_meses = hoy + timedelta(days=180)

    # Obtener placas próximas a vencer o ya vencidas
    placas_alerta = Placas.query.filter(
        Placas.fecha_vigencia <= seis_meses
    ).all()
    
    print(f"Total placas encontradas para alerta: {len(placas_alerta)}")
    if not placas_alerta:
        print("❌ No hay placas próximas a vencer o vencidas")
        return

    # --- 1. Administradores ---
    admins = Usuarios.query.filter_by(rol='admin').all()
    emails_admin = [a.correo for a in admins if a.correo]
    print(f"Administradores con correo: {emails_admin}")

    if emails_admin:
        lista_admin_html = "".join([
            f"<li>Placa: <strong>{p.placa}</strong> | Unidad: {p.id_unidad} | Vence el: {p.fecha_vigencia}</li>"
            for p in placas_alerta
        ])
        cuerpo_admin = f"<html><body><h2>Placas próximas a vencer</h2><ul>{lista_admin_html}</ul></body></html>"
        msg_admin = Message(subject="Listado placas próximas a vencer", recipients=emails_admin, html=cuerpo_admin)
        mail.send(msg_admin)
        print(f"✅ Correos enviados a administradores: {emails_admin}")

        # Crear alertas en BD
        for p in placas_alerta:
            alerta = Alerta(
                id_unidad=p.id_unidad,
                tipo_alerta="placa",
                descripcion=f"La placa {p.placa} está próxima a vencer el {p.fecha_vigencia}",
                estado="pendiente",
                detalle={"id_placa": p.id_placa}
            )
            db.session.add(alerta)
        db.session.commit()
        print(f"✅ Alertas registradas para administradores")

    # --- 2. Choferes ---
    choferes = Usuarios.query.filter_by(rol='chofer').all()
    print(f"Choferes encontrados: {[c.id_chofer for c in choferes]}")
    for user in choferes:
        if not user.correo:
            continue
        asignaciones_activas = Asignaciones.query.filter(
            Asignaciones.id_chofer == user.id_chofer,
            (Asignaciones.fecha_fin == None) | (Asignaciones.fecha_fin >= hoy)
        ).all()
        unidades_usuario = [a.id_unidad for a in asignaciones_activas]
        placas_usuario = [p for p in placas_alerta if p.id_unidad in unidades_usuario]

        print(f"Usuario {user.id_chofer} - placas a alertar: {[p.placa for p in placas_usuario]}")
        if not placas_usuario:
            continue

        lista_usuario_html = "".join([
            f"<li>Placa: <strong>{p.placa}</strong> | Unidad: {p.id_unidad} | Vence el: {p.fecha_vigencia}</li>"
            for p in placas_usuario
        ])
        cuerpo_usuario = f"<html><body><h2>Placas próximas a vencer de sus unidades</h2><ul>{lista_usuario_html}</ul></body></html>"
        msg_usuario = Message(subject="Placas próximas a vencer de sus unidades", recipients=[user.correo], html=cuerpo_usuario)
        mail.send(msg_usuario)
        print(f"✅ Correo enviado a chofer {user.id_chofer} - {user.correo}")

        for p in placas_usuario:
            alerta = Alerta(
                id_unidad=p.id_unidad,
                tipo_alerta="placa",
                descripcion=f"La placa {p.placa} de su unidad está próxima a vencer el {p.fecha_vigencia}",
                estado="pendiente",
                detalle={"id_placa": p.id_placa, "id_chofer": user.id_chofer}
            )
            db.session.add(alerta)
        db.session.commit()
        print(f"✅ Alertas registradas para chofer {user.id_chofer}")

    print("✅ Envío de alertas completado")


def guardar_archivo_unico(file, carpeta='placas'):
    """Guarda un archivo (imagen o PDF) con nombre único en la carpeta especificada."""
    
    # Extensiones permitidas (PDF + imágenes)
    permitidos = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
    
    ext = os.path.splitext(file.filename)[1].lower()  # extensión real
    if ext not in permitidos:
        raise ValueError("Tipo de archivo no permitido. Solo imágenes y PDFs.")
    
    # Crear carpeta final
    UPLOAD_DIR = os.path.join("uploads", carpeta)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Nombre único
    nombre_unico = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, nombre_unico)

    # Guardar archivo
    file.save(path)

    return path.replace("\\", "/")




@app.route("/placas/registrar", methods=["POST"])
def registrar_o_actualizar_placa():
    # ---------------- Directorios ----------------
    UPLOAD_DIR = 'placas/'
    HISTORIAL_DIR = 'historial_placas/'
    PAGO_DIR = 'pagos/'
    HISTORIAL_PAGO_DIR = 'historial_pagos/'
    TARJETA_DIR = 'tarjetas_circulacion/'
    HISTORIAL_TARJETA_DIR = 'historial_tarjetas_circulacion/'

    data = request.form
    usuarioId = data.get("usuarioId", "sistema")  # <-- reemplaza USUARIO_SISTEMA

    id_unidad = data.get("id_unidad")
    nueva_placa = data.get("placa")
    folio = data.get("folio")
    fecha_expedicion = data.get("fecha_expedicion")
    fecha_vigencia = data.get("fecha_vigencia")
    monto_pago = data.get("monto_pago", 0)

    # Validación básica
    if not id_unidad or not nueva_placa or not fecha_vigencia:
        return jsonify({"error": "Unidad, placa y fecha de vigencia son obligatorios"}), 400


    hoy = date.today()
    placa_activa = Placas.query.filter_by(id_unidad=id_unidad).first()

    # ---------------- Funciones de archivos ----------------
    def mover_al_historial(field_name, carpeta_historial):
        old_path = getattr(placa_activa, field_name)
        if old_path and os.path.exists(old_path):
            os.makedirs(os.path.join("uploads", carpeta_historial), exist_ok=True)
            ext = old_path.rsplit('.', 1)[1].lower()
            nuevo_nombre = f"{uuid.uuid4()}.{ext}"
            dst = os.path.join("uploads", carpeta_historial, nuevo_nombre)
            shutil.move(old_path, dst)
            setattr(placa_activa, field_name, dst.replace("\\", "/"))

    def guardar_archivo_unico(archivo, carpeta):
        os.makedirs(os.path.join("uploads", carpeta), exist_ok=True)
        nombre = f"{uuid.uuid4()}_{archivo.filename}"
        ruta = os.path.join("uploads", carpeta, nombre)
        archivo.save(ruta)
        return ruta.replace("\\", "/")

    # ---------------- Actualización de placa existente ----------------
    if placa_activa:
        dias_restantes = (placa_activa.fecha_vigencia - hoy).days if placa_activa.fecha_vigencia else 0
        if dias_restantes > 180:
            return jsonify({
                "error": f"No se puede registrar nueva placa. Vigencia actual hasta {placa_activa.fecha_vigencia}"
            }), 400

        # Mover archivos antiguos al historial
        mover_al_historial("url_placa_frontal", HISTORIAL_DIR)
        mover_al_historial("url_placa_trasera", HISTORIAL_DIR)
        mover_al_historial("url_comprobante_pago", HISTORIAL_PAGO_DIR)
        mover_al_historial("url_tarjeta_circulacion", HISTORIAL_TARJETA_DIR)

        # Guardar en historial usando usuario del frontend
        historial = HistorialPlaca(
            id_placa=placa_activa.id_placa,
            id_unidad=placa_activa.id_unidad,
            folio=placa_activa.folio,
            placa=placa_activa.placa,
            fecha_expedicion=placa_activa.fecha_expedicion,
            fecha_vigencia=placa_activa.fecha_vigencia,
            monto_pago=placa_activa.monto_pago,
            url_placa_frontal=placa_activa.url_placa_frontal,
            url_placa_trasera=placa_activa.url_placa_trasera,
            url_comprobante_pago=placa_activa.url_comprobante_pago,
            url_tarjeta_circulacion=placa_activa.url_tarjeta_circulacion,
            usuario=usuarioId
        )
        db.session.add(historial)

        # Actualizar placa activa
        placa_activa.placa = nueva_placa
        placa_activa.folio = folio
        placa_activa.fecha_expedicion = fecha_expedicion
        placa_activa.fecha_vigencia = fecha_vigencia
        placa_activa.monto_pago = monto_pago

        # Guardar archivos nuevos
        file_fields = {
            "url_placa_frontal": UPLOAD_DIR,
            "url_placa_trasera": UPLOAD_DIR,
            "comprobante": PAGO_DIR,
            "tarjeta_circulacion": TARJETA_DIR
        }

        for field_name, carpeta in file_fields.items():
            archivo = request.files.get(field_name)
            if archivo:
                ruta = guardar_archivo_unico(archivo, carpeta)
                if field_name == "comprobante":
                    placa_activa.url_comprobante_pago = ruta
                elif field_name == "tarjeta_circulacion":
                    placa_activa.url_tarjeta_circulacion = ruta
                else:
                    setattr(placa_activa, field_name, ruta)

        placa_activa.requiere_renovacion = False
        db.session.commit()

        # 🔹 Marcar alertas como completadas tras la renovación
        alertas_pendientes = Alerta.query.filter_by(
            id_unidad=id_unidad,
            tipo_alerta="placa",
            estado="pendiente"
        ).all()
        for alerta in alertas_pendientes:
            alerta.estado = "completada"
            alerta.fecha_resuelta = datetime.utcnow()
        db.session.commit()

        return jsonify({"message": "Placa actualizada correctamente"}), 200

    # ---------------- Registro de nueva placa ----------------
    nueva = Placas(
        id_unidad=id_unidad,
        placa=nueva_placa,
        folio=folio,
        fecha_expedicion=fecha_expedicion,
        fecha_vigencia=fecha_vigencia,
        monto_pago=monto_pago,
        requiere_renovacion=False
    )

    # Guardar archivos nuevos
    file_fields = {
        "url_placa_frontal": UPLOAD_DIR,
        "url_placa_trasera": UPLOAD_DIR,
        "comprobante": PAGO_DIR,
        "tarjeta_circulacion": TARJETA_DIR
    }

    for field_name, carpeta in file_fields.items():
        archivo = request.files.get(field_name)
        if archivo:
            ruta = guardar_archivo_unico(archivo, carpeta)
            if field_name == "comprobante":
                nueva.url_comprobante_pago = ruta
            elif field_name == "tarjeta_circulacion":
                nueva.url_tarjeta_circulacion = ruta
            else:
                setattr(nueva, field_name, ruta)

    db.session.add(nueva)
    db.session.commit()

    return jsonify({"message": "Placa registrada correctamente"}), 200

# ---------------------------
# Scheduler diario
# ---------------------------
scheduler = BackgroundScheduler()

def job_envio_alertas():
    with app.app_context():  # Contexto de Flask activo
        print("📌 Iniciando envío de alertas")
        try:
            enviar_alertas_semanales()
            print("✅ Alertas enviadas correctamente")
        except Exception as e:
            print(f"❌ Error al enviar alertas: {e}")

# Ejecutar cada 100 segundos
scheduler.add_job(job_envio_alertas, 'interval', seconds=16060)
scheduler.start()



@app.route("/placas/<int:id_placa>", methods=["DELETE"])
def eliminar_placa(id_placa):
    UPLOAD_DIR = 'uploads/placas/'
    placa = Placas.query.get(id_placa)

    if not placa:
        return jsonify({"error": "Placa no encontrada"}), 404

    # Eliminar archivos asociados (solo los de placas)
    for field_name in ["url_placa_frontal", "url_placa_trasera"]:
        file_path = getattr(placa, field_name)
        if file_path and file_path.startswith(UPLOAD_DIR) and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error eliminando archivo {file_path}: {e}")

    # Eliminar registro de la base de datos
    db.session.delete(placa)
    db.session.commit()

    return jsonify({"message": "Placa y archivos asociados eliminados correctamente"}), 200

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



ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/placas/<int:id_placa>", methods=["PUT"])
def update_placa(id_placa):
    import pprint
    pp = pprint.PrettyPrinter(indent=2)

    # Carpetas de almacenamiento
    UPLOAD_FOLDER_PLACAS = "uploads/placas"
    UPLOAD_FOLDER_PAGOS = "uploads/pagos"
    UPLOAD_FOLDER_TARJETAS = "uploads/tarjetas_circulacion"

    # Obtener placa
    placa = Placas.query.get(id_placa)
    if not placa:
        return jsonify({"error": "Placa no encontrada"}), 404

    # Debug: imprimir lo que llega
    print("\n=== Datos recibidos en request.form ===")
    pp.pprint(request.form.to_dict())
    print("\n=== Archivos recibidos en request.files ===")
    pp.pprint(request.files.to_dict())

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

    # monto_pago
    monto_pago = request.form.get("monto_pago")
    if monto_pago:
        try:
            placa.monto_pago = float(monto_pago)
        except ValueError:
            return jsonify({"error": "Monto pago inválido"}), 400

    # Función para manejar archivos PDF, sobrescribiendo si existe
    # Función para manejar archivos PDF o imagen
    def handle_file(file_field_name, upload_dir, field_name_model=None):
        field_name_model = field_name_model or file_field_name

        file = request.files.get(file_field_name)
        if not file or file.filename == "":
            print(f"No se recibió archivo en '{file_field_name}'.")
            return

        ext = os.path.splitext(file.filename)[1].lower()
        permitidos = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
        if ext not in permitidos:
            print(f"Extensión no permitida en {file.filename}")
            return

        os.makedirs(upload_dir, exist_ok=True)

        old_path = getattr(placa, field_name_model)
        if old_path and os.path.exists(old_path):
            try:
                os.remove(old_path)
                print(f"Archivo viejo eliminado: {old_path}")
            except Exception as e:
                print(f"No se pudo eliminar {old_path}: {e}")

        nombre_unico = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(upload_dir, nombre_unico)
        file.save(file_path)

        file_path = file_path.replace("\\", "/")
        setattr(placa, field_name_model, file_path)

        print(f"Archivo nuevo guardado en: {file_path}")

    # Manejar todos los archivos con mapeo correcto
    handle_file("url_placa_frontal", UPLOAD_FOLDER_PLACAS)
    handle_file("url_placa_trasera", UPLOAD_FOLDER_PLACAS)
    handle_file("comprobante", UPLOAD_FOLDER_PAGOS, field_name_model="url_comprobante_pago")
    handle_file("tarjeta_circulacion", UPLOAD_FOLDER_TARJETAS, field_name_model="url_tarjeta_circulacion")

    # Commit
    try:
        db.session.commit()
        print("\nActualización de placa exitosa:", placa.to_dict())
        return jsonify({"message": "Placa actualizada correctamente", "placa": placa.to_dict()})
    except Exception as e:
        db.session.rollback()
        print("\nError al actualizar placa:", str(e))
        return jsonify({"error": str(e)}), 500

# ---------------------------
# Endpoint para obtener historial de placas 

@app.route("/placas/historial", methods=["GET"])
def get_historial_placas():
    historial = HistorialPlaca.query.order_by(HistorialPlaca.fecha_vigencia.desc()).all()
    historial_list = []

    for h in historial:
        unidad = Unidades.query.get(h.id_unidad)
        
        # Obtener nombre de usuario
        usuario_nombre = h.usuario  # por defecto
        if h.usuario:
            usuario_obj = Usuarios.query.get(h.usuario)
            if usuario_obj:
                usuario_nombre = usuario_obj.nombre

        historial_list.append({
            "id_historial": h.id_historial,
            "id_placa": h.id_placa,
            "id_unidad": h.id_unidad,
            "nombre_unidad": unidad.vehiculo if unidad else "N/A",
            "vehiculo": unidad.vehiculo if unidad else "N/A",
            "modelo": unidad.modelo if unidad else "N/A",
            "placa": h.placa,
            "folio": h.folio,
            "fecha_expedicion": h.fecha_expedicion.strftime("%Y-%m-%d") if h.fecha_expedicion else None,
            "fecha_vigencia": h.fecha_vigencia.strftime("%Y-%m-%d") if h.fecha_vigencia else None,
            "monto_pago": h.monto_pago,
            "url_placa_frontal": h.url_placa_frontal,
            "url_placa_trasera": h.url_placa_trasera,
            "url_comprobante_pago": h.url_comprobante_pago,
            "url_tarjeta_circulacion": h.url_tarjeta_circulacion,
            "usuario": usuario_nombre
        })

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

def save_uploaded_file(file_obj, id_unidad, fecha_pago):
    if not file_obj or file_obj.filename == "":
        return None
    if not allowed_file(file_obj.filename):
        return None

    # Carpeta única para todos los PDFs de Refrendo y Tenencia
    folder = os.path.join(app.root_path, "uploads", "refrendo_tenencia")
    os.makedirs(folder, exist_ok=True)

    ext = os.path.splitext(file_obj.filename)[1].lower()
    filename = f"{id_unidad}_{fecha_pago.isoformat()}_{uuid.uuid4().hex}{ext}"
    safe = secure_filename(filename)
    filepath = os.path.join(folder, safe)
    file_obj.save(filepath)

    # Retornar ruta relativa para almacenar en la base de datos
    return os.path.join("uploads", "refrendo_tenencia", safe).replace("\\", "/")

def move_file_to_historial(url):
    if not url:
        return None

    folder = os.path.join(app.root_path, "uploads", "historial_refrendo_tenencia")
    os.makedirs(folder, exist_ok=True)

    nombre = os.path.basename(url)
    src = os.path.join(app.root_path, url)
    dst = os.path.join(folder, nombre)

    if os.path.exists(src):
        shutil.move(src, dst)

    return os.path.join("uploads", "historial_refrendo_tenencia", nombre).replace("\\", "/")


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
    except Exception as e:
        print("Error en los datos:", e)
        return jsonify({"error": "Datos inválidos"}), 400

    unidad = Unidades.query.get(id_unidad)
    if not unidad:
        return jsonify({"error": "Unidad no encontrada"}), 404

    limite_pago = date(fecha_pago.year, 3, 31)
    reset_realizado = False

    # 1) Verificar si ya existe pago de este año
    existe_refrendo = Refrendo_Tenencia.query.filter(
        Refrendo_Tenencia.id_unidad == id_unidad,
        db.extract('year', Refrendo_Tenencia.fecha_pago) == fecha_pago.year
    ).first()

    if existe_refrendo:
        return jsonify({"error": "Ya existe un pago registrado para este año"}), 400

    # 2) Buscar registro previo
    registro = Refrendo_Tenencia.query.filter_by(id_unidad=id_unidad).first()

    if registro and registro.fecha_pago and registro.fecha_pago.year < fecha_pago.year:
        print("Registro previo encontrado, moviendo a historial y reseteando...")

        # MOVER ARCHIVO ANTES DE RESET
        ruta_historial = move_file_to_historial(registro.url_factura)

        historial = Historial_Refrendo_Tenencia(
            id_pago=registro.id_pago,
            id_unidad=registro.id_unidad,
            tipo_pago=registro.tipo_pago,
            monto=registro.monto,
            monto_refrendo=registro.monto_refrendo,
            monto_tenencia=registro.monto_tenencia,
            fecha_pago=registro.fecha_pago,
            url_factura=ruta_historial,     # ✔ YA MOVIDO
            observaciones=registro.observaciones,
            tipo_movimiento="REGISTRO",
            usuario_registro=usuario
        )
        db.session.add(historial)

        # Resetear registro
        registro.monto = 0
        registro.monto_refrendo = 0
        registro.monto_tenencia = 0
        registro.fecha_pago = None
        registro.tipo_pago = 'PENDIENTE'
        registro.observaciones = None
        registro.url_factura = None
        db.session.commit()

        reset_realizado = True
        print("Fila reseteada correctamente")

    # 3) Actualizar o crear registro
    if registro and reset_realizado:
        print("Actualizando registro reseteado con nuevos datos...")
        registro.fecha_pago = fecha_pago
        registro.limite_pago = limite_pago
        registro.tipo_pago = 'REFRENDO' if fecha_pago <= limite_pago else 'AMBOS'
        registro.monto_refrendo = monto_refrendo or monto_general
        registro.monto_tenencia = monto_tenencia or monto_general
        registro.monto = (monto_refrendo or monto_general) + (monto_tenencia or monto_general)
        registro.observaciones = data.get('observaciones')

    elif not registro:
        print("Creando nuevo registro...")
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

    # 4) Guardar PDF nuevo
    file_pdf = request.files.get('url_factura')
    if file_pdf:
        ruta_nueva = save_uploaded_file(file_pdf, id_unidad, fecha_pago)
        registro.url_factura = ruta_nueva

    db.session.commit()
    print(f"Pago registrado correctamente: ID {registro.id_pago}, Tipo {registro.tipo_pago}")

    # ---------------------------------------------------
    # 5) MARCAR ALERTAS COMO COMPLETADAS (AGREGADO AQUÍ)
    # ---------------------------------------------------
    alertas = Alerta.query.filter_by(
        id_unidad=id_unidad,
        tipo_alerta="refrendo_tenencia",
        estado="pendiente"
    ).all()

    for alerta in alertas:
        alerta.estado = "completada"
        alerta.fecha_resuelta = datetime.utcnow()

    db.session.commit()
    # ---------------------------------------------------

    return jsonify({
        "message": f"Pago {registro.tipo_pago} registrado correctamente",
        "id_pago": registro.id_pago
    }), 200


@app.route('/refrendo_tenencia', methods=['GET'])
def listar_pagos_refrendo_tenencia():
    try:
        # Obtener filtros desde query params
        filtro_unidad = request.args.get('unidad')  # id_unidad
        filtro_tipo_pago = request.args.get('tipo_pago')  # REFRENDO, TENENCIA, AMBOS
        filtro_fecha_inicio = request.args.get('fecha_inicio')  # YYYY-MM-DD
        filtro_fecha_fin = request.args.get('fecha_fin')  # YYYY-MM-DD

        # Construir query
        query = Refrendo_Tenencia.query.join(Unidades)

        if filtro_unidad:
            query = query.filter(Refrendo_Tenencia.id_unidad == filtro_unidad)

        if filtro_tipo_pago:
            query = query.filter(Refrendo_Tenencia.tipo_pago == filtro_tipo_pago)

        if filtro_fecha_inicio:
            query = query.filter(Refrendo_Tenencia.fecha_pago >= filtro_fecha_inicio)

        if filtro_fecha_fin:
            query = query.filter(Refrendo_Tenencia.fecha_pago <= filtro_fecha_fin)

        pagos = query.all()

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
                "usuario": getattr(pago, "usuario", ""),
                "observaciones": pago.observaciones or "",
                "url_factura": pago.url_factura,
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

    user_id = data.get("usuario")
    if not user_id:
        return jsonify({"error": "Usuario no proporcionado"}), 401

    registro = Refrendo_Tenencia.query.get(id_pago)
    if not registro:
        return jsonify({"error": "Registro no encontrado"}), 404

    try:
        cambios = False
        archivo_anterior = registro.url_factura  # ruta relativa guardada en DB

        # --------------------------
        # Campos normales
        # --------------------------
        if 'fecha_pago' in data and data['fecha_pago']:
            nueva_fecha = datetime.strptime(data['fecha_pago'], '%Y-%m-%d').date()
            if registro.fecha_pago != nueva_fecha:
                registro.fecha_pago = nueva_fecha
                registro.limite_pago = date(nueva_fecha.year, 3, 31)
                cambios = True

        if 'monto_refrendo' in data:
            registro.monto_refrendo = float(data['monto_refrendo'])
            cambios = True

        if 'monto_tenencia' in data:
            registro.monto_tenencia = float(data['monto_tenencia'])
            cambios = True

        if 'observaciones' in data:
            registro.observaciones = data['observaciones']
            cambios = True

        # Total
        registro.monto = (registro.monto_refrendo or 0) + (registro.monto_tenencia or 0)

        # --------------------------
        # Manejo del archivo nuevo
        # --------------------------
        file_pdf = request.files.get('url_factura')

        if file_pdf:
            # 1) Eliminar archivo viejo si existía
            if archivo_anterior:
                ruta_completa = os.path.join(app.root_path, archivo_anterior)
                if os.path.exists(ruta_completa):
                    os.remove(ruta_completa)

            # 2) Guardar nuevo archivo
            registro.url_factura = save_uploaded_file(file_pdf, registro.id_unidad, registro.fecha_pago)
            cambios = True

        # --------------------------
        # Registrar historial
        # --------------------------


        registro.usuario = user_id

        if not cambios:
            return jsonify({"message": "No hubo cambios que actualizar"}), 200

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
                "url_factura": h.url_factura,            # <-- AHORA SOLO UNO
                "observaciones": h.observaciones,
                "fecha_registro": h.fecha_registro.strftime("%Y-%m-%d %H:%M:%S") if h.fecha_registro else None,
                "tipo_movimiento": h.tipo_movimiento,    # <-- SE MANTIENE
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
    fin_periodo = date(año_actual, 3, 31)

    unidades = Unidades.query.all()
    if not unidades:
        return []

    # Almacena alertas completas
    alertas_generadas = []

    # ------------------------------------------------------------------------------------------------
    # 1. Administradores
    # ------------------------------------------------------------------------------------------------
    admins = Usuarios.query.filter_by(rol='admin').all()
    emails_admin = [a.correo for a in admins if a.correo]

    pendientes = []

    for u in unidades:
        pago = Refrendo_Tenencia.query.filter(
            Refrendo_Tenencia.id_unidad == u.id_unidad,
            db.extract("year", Refrendo_Tenencia.fecha_pago) == año_actual
        ).first()

        if not pago:
            mensaje = (
                "Pague refrendo antes del 31 de marzo"
                if hoy <= fin_periodo
                else "Debe pagar refrendo y tenencia. Se aplicarán recargos."
            )

            pendientes.append({
                "id_unidad": u.id_unidad,
                "vehiculo": u.vehiculo,
                "modelo": u.modelo,
                "mensaje": mensaje
            })

    # -------- Enviar correos a Administradores
    if emails_admin and pendientes:
        lista_html = "".join([
            f"<li><strong>{p['vehiculo']} {p['modelo']}</strong> (ID {p['id_unidad']}): {p['mensaje']}</li>"
            for p in pendientes
        ])

        cuerpo_html = f"""
        <html>
        <body>
            <h2>Unidades con refrendo/tenencia pendiente</h2>
            <ul>{lista_html}</ul>
        </body>
        </html>
        """

        msg = Message(
            subject=f"Avisos de refrendo/tenencia {año_actual}",
            recipients=emails_admin,
            html=cuerpo_html
        )
        mail.send(msg)

        # Registrar alertas para admin
        for p in pendientes:
            alerta = Alerta(
                id_unidad=p["id_unidad"],
                tipo_alerta="refrendo_tenencia",
                descripcion=f"La unidad {p['vehiculo']} {p['modelo']} ({p['id_unidad']}) requiere pago: {p['mensaje']}",
                estado="pendiente",
                detalle={"rol": "admin"}
            )
            db.session.add(alerta)
            alertas_generadas.append(alerta)

        db.session.commit()
        print(f"[ADMIN] Alertas enviadas y registradas para {len(emails_admin)} administradores.")

    # ------------------------------------------------------------------------------------------------
    # 2. Choferes
    # ------------------------------------------------------------------------------------------------
    choferes = Usuarios.query.filter_by(rol="chofer").all()

    for user in choferes:
        if not user.correo:
            continue

        # Unidades asignadas al chofer
        asignaciones = Asignaciones.query.filter(
            Asignaciones.id_chofer == user.id_chofer,
            (Asignaciones.fecha_fin == None) | (Asignaciones.fecha_fin >= hoy)
        ).all()

        ids_unidades_user = [a.id_unidad for a in asignaciones]

        pendientes_user = [
            p for p in pendientes if p["id_unidad"] in ids_unidades_user
        ]

        if not pendientes_user:
            continue

        lista_html = "".join([
            f"<li><strong>{p['vehiculo']} {p['modelo']}</strong> (ID {p['id_unidad']}): {p['mensaje']}</li>"
            for p in pendientes_user
        ])

        cuerpo_html = f"""
        <html>
        <body>
            <h2>Refrendo/tenencia pendiente de sus unidades</h2>
            <ul>{lista_html}</ul>
        </body>
        </html>
        """

        msg_user = Message(
            subject="Aviso de refrendo/tenencia",
            recipients=[user.correo],
            html=cuerpo_html
        )
        mail.send(msg_user)

        # Registrar alertas personalizadas para chofer
        for p in pendientes_user:
            alerta = Alerta(
                id_unidad=p["id_unidad"],
                tipo_alerta="refrendo_tenencia",
                descripcion=f"La unidad {p['vehiculo']} {p['modelo']} ({p['id_unidad']}) requiere pago: {p['mensaje']}",
                estado="pendiente",
                detalle={"id_chofer": user.id_chofer, "rol": "chofer"}
            )
            db.session.add(alerta)
            alertas_generadas.append(alerta)

        db.session.commit()
        print(f"[CHOFER] Alertas enviadas al chofer {user.id_chofer}")

    print(f"[INFO] Total alertas registradas: {len(alertas_generadas)}")
    return alertas_generadas


# --------------------------------------------
# Programador semanal automático
# --------------------------------------------

scheduler = BackgroundScheduler()
def job_enviar_alertas_refrendo_tenencia():
    with app.app_context():
        enviar_alertas_refrendo_tenencia()

scheduler.add_job(job_enviar_alertas_refrendo_tenencia, 'interval', seconds=25080)
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
        Unidades.modelo,
        Unidades.clase_tipo,
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
            "modelo": row.modelo,
            "clase_tipo": row.clase_tipo,
            "placa": row.placa,
            "marca": row.marca,
            "tipo": row.nombre_tipo,
            "kilometraje_actual": row.kilometraje_actual,
            "fecha_ultimo_mantenimiento": row.fecha_ultimo_mantenimiento.isoformat() if row.fecha_ultimo_mantenimiento else None,
            "kilometraje_ultimo": row.kilometraje_ultimo,
            "proximo_mantenimiento": row.proximo_mantenimiento.isoformat() if row.proximo_mantenimiento else None,
            "proximo_kilometraje": row.proximo_kilometraje
        })
    
    return jsonify(resultado)

# ---------------------
# RUTA: registrar mantenimiento realizado (y reprogramar)
# ---------------------

UPLOAD_FOLDER = "uploads/mantenimientos"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/mantenimientos', methods=['POST'])
def registrar_mantenimiento():
    # Crear carpeta de uploads si no existe
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Usar request.form y request.files para multipart/form-data
    data = request.form
    archivo = request.files.get("url_comprobante")  # ⚡ archivo

    id_unidad = data.get('id_unidad')
    tipo_nombre = data.get('tipo_mantenimiento')
    kilometraje = data.get('kilometraje')
    descripcion = data.get('descripcion')
    id_mp = data.get('id_mantenimiento_programado')

    if not id_unidad or not tipo_nombre or kilometraje is None:
        return jsonify({"error":"id_unidad, tipo_mantenimiento y kilometraje son requeridos"}), 400

    try:
        kilometraje = int(kilometraje)
    except (TypeError, ValueError):
        return jsonify({"error":"Kilometraje debe ser un número válido"}), 400

    unidad = Unidades.query.get(id_unidad)
    if not unidad:
        return jsonify({"error":"Unidad no encontrada"}), 404

    tipo = TiposMantenimiento.query.filter_by(nombre_tipo=tipo_nombre).first()
    if not tipo:
        return jsonify({"error":"Tipo de mantenimiento no válido"}), 400

    # Obtener mantenimiento programado
    if not id_mp:
        mp = MantenimientosProgramados.query.filter_by(
            id_unidad=id_unidad, 
            id_tipo_mantenimiento=tipo.id_tipo_mantenimiento
        ).first()
    else:
        mp = MantenimientosProgramados.query.get(id_mp)

    fecha_real = date.today()

    # Guardar archivo si existe
    url_comprobante = None
    if archivo and allowed_file(archivo.filename):
        filename = secure_filename(f"{id_unidad}_{tipo_nombre}_{fecha_real}_{archivo.filename}")
        archivo.save(os.path.join(UPLOAD_FOLDER, filename))
        url_comprobante = f"{UPLOAD_FOLDER}/{filename}"

    # Crear historial
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
        url_comprobante = url_comprobante
    )
    db.session.add(nuevo)

    frecuencia = FrecuenciasPorMarca.query.filter_by(
        marca=unidad.marca, 
        id_tipo_mantenimiento=tipo.id_tipo_mantenimiento
    ).first()

    # Actualizar o crear registro programado
    if mp:
        mp.fecha_ultimo_mantenimiento = fecha_real
        mp.kilometraje_ultimo = kilometraje
        if frecuencia:
            mp.proximo_mantenimiento = fecha_real + timedelta(days=frecuencia.frecuencia_tiempo)
            mp.proximo_kilometraje = kilometraje + frecuencia.frecuencia_kilometraje
        db.session.add(mp)
    else:
        if frecuencia:
            proximo_fecha = fecha_real + timedelta(days=frecuencia.frecuencia_tiempo)
            proximo_km = kilometraje + frecuencia.frecuencia_kilometraje
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

    # Actualizar kilometraje actual de la unidad
    if unidad.kilometraje_actual is None or kilometraje > (unidad.kilometraje_actual or 0):
        unidad.kilometraje_actual = kilometraje
        db.session.add(unidad)

    db.session.commit()
    return jsonify({"message":"Mantenimiento registrado y programado actualizado."}), 201

# ---------------------
# RUTA: historial de mantenimientos
# ---------------------
@app.route('/mantenimientos', methods=['GET'])
def listar_mantenimientos():
    mantenimientos = Mantenimientos.query.order_by(
        Mantenimientos.fecha_realizacion.desc()
    ).all()

    salida = []
    for m in mantenimientos:
        salida.append({
            "id_mantenimiento": m.id_mantenimiento,
            "id_mantenimiento_programado": m.id_mantenimiento_programado,
            "id_unidad": m.id_unidad,
            "tipo_mantenimiento": m.tipo_mantenimiento,
            "descripcion": m.descripcion,
            "fecha_realizacion": m.fecha_realizacion.isoformat() if m.fecha_realizacion else None,
            "kilometraje": m.kilometraje,
            "realizado_por": m.realizado_por,
            "empresa_garantia": m.empresa_garantia,
            "cobertura_garantia": m.cobertura_garantia,
            "costo": str(m.costo) if m.costo is not None else None,
            "observaciones": m.observaciones,
            "url_comprobante": m.url_comprobante
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


##empresas
#======================================================

# --------- Obtener todas las empresas ---------
@app.route('/empresas', methods=['GET'])
def get_empresas():
    empresas = Empresa.query.all()
    resultado = []
    for e in empresas:
        resultado.append({
            'id_empresa': e.id_empresa,
            'razon_social': e.razon_social,
            'rfc': e.rfc,
            'regimen_fiscal': e.regimen_fiscal,
            'nombre_comercial': e.nombre_comercial,
            'direccion': e.direccion,
            'inicio_operaciones': e.inicio_operaciones.strftime('%Y-%m-%d'),
            'estatus': e.estatus,
            'actividad_economica': e.actividad_economica
        })
    return jsonify(resultado)

# --------- Insertar empresa ---------
@app.route('/empresas', methods=['POST'])
def crear_empresa():
    data = request.get_json()
    nueva_empresa = Empresa(
        razon_social=data.get('razon_social'),
        rfc=data.get('rfc'),
        regimen_fiscal=data.get('regimen_fiscal'),
        nombre_comercial=data.get('nombre_comercial'),
        direccion=data.get('direccion'),
        inicio_operaciones=date.fromisoformat(data.get('inicio_operaciones')),
        estatus=data.get('estatus'),
        actividad_economica=data.get('actividad_economica')
    )
    db.session.add(nueva_empresa)
    db.session.commit()
    return jsonify({'message': 'Empresa creada', 'id_empresa': nueva_empresa.id_empresa})

# --------- Actualizar empresa ---------
@app.route('/empresas/<int:id_empresa>', methods=['PUT'])
def actualizar_empresa(id_empresa):
    data = request.get_json()
    empresa = Empresa.query.get(id_empresa)
    if not empresa:
        return jsonify({'message': 'Empresa no encontrada'}), 404
    empresa.razon_social = data.get('razon_social')
    empresa.rfc = data.get('rfc')
    empresa.regimen_fiscal = data.get('regimen_fiscal')
    empresa.nombre_comercial = data.get('nombre_comercial')
    empresa.direccion = data.get('direccion')
    empresa.inicio_operaciones = date.fromisoformat(data.get('inicio_operaciones'))
    empresa.estatus = data.get('estatus')
    empresa.actividad_economica = data.get('actividad_economica')
    db.session.commit()
    return jsonify({'message': 'Empresa actualizada'})

# --------- Eliminar empresa ---------
@app.route('/empresas/<int:id_empresa>', methods=['DELETE'])
def eliminar_empresa(id_empresa):
    empresa = Empresa.query.get(id_empresa)
    if not empresa:
        return jsonify({'message': 'Empresa no encontrada'}), 404
    db.session.delete(empresa)
    db.session.commit()
    return jsonify({'message': 'Empresa eliminada'})



# -------------------------------
# Listar sucursales (opcional por empresa)
# -------------------------------
@app.route("/sucursales", methods=["GET"])
def get_sucursal():
    id_empresa = request.args.get("empresa")
    if id_empresa:
        sucursales = Sucursal.query.filter_by(id_empresa=id_empresa).all()
    else:
        sucursales = Sucursal.query.all()
    return jsonify([{
        "id_sucursal": s.id_sucursal,
        "nombre": s.nombre,
        "direccion": s.direccion,
        "telefono": s.telefono,
        "correo": s.correo,
        "horario": s.horario,
        "id_empresa": s.id_empresa
    } for s in sucursales])

# -------------------------------
# Crear sucursal
# -------------------------------
@app.route("/sucursales", methods=["POST"])
def create_sucursal():
    data = request.get_json()
    # Validar empresa
    empresa = Empresa.query.get(data.get("id_empresa"))
    if not empresa:
        return jsonify({"error": "La empresa no existe"}), 400

    nueva = Sucursal(
        nombre=data.get("nombre"),
        direccion=data.get("direccion"),
        telefono=data.get("telefono"),
        correo=data.get("correo"),
        horario=data.get("horario"),
        id_empresa=data.get("id_empresa")
    )
    db.session.add(nueva)
    db.session.commit()
    return jsonify({"message": "Sucursal creada exitosamente", "id_sucursal": nueva.id_sucursal})

# -------------------------------
# Actualizar sucursal
# -------------------------------
@app.route("/sucursales/<int:id>", methods=["PUT"])
def update_sucursal(id):
    sucursal = Sucursal.query.get_or_404(id)
    data = request.get_json()
    # Validar empresa si se actualiza
    if "id_empresa" in data:
        empresa = Empresa.query.get(data["id_empresa"])
        if not empresa:
            return jsonify({"error": "La empresa no existe"}), 400
        sucursal.id_empresa = data["id_empresa"]

    sucursal.nombre = data.get("nombre", sucursal.nombre)
    sucursal.direccion = data.get("direccion", sucursal.direccion)
    sucursal.telefono = data.get("telefono", sucursal.telefono)
    sucursal.correo = data.get("correo", sucursal.correo)
    sucursal.horario = data.get("horario", sucursal.horario)

    db.session.commit()
    return jsonify({"message": "Sucursal actualizada exitosamente"})

# -------------------------------
# Eliminar sucursal
# -------------------------------
@app.route("/sucursales/<int:id>", methods=["DELETE"])
def delete_sucursal(id):
    sucursal = Sucursal.query.get_or_404(id)
    db.session.delete(sucursal)
    db.session.commit()
    return jsonify({"message": "Sucursal eliminada exitosamente"})




#===================================================================
#FILTROS
#=====================================================================
@app.route('/api/placas', methods=['GET'])
def listar_placas():
    try:
        search = request.args.get("search", "", type=str)
        unidad = request.args.get("unidad", "", type=str)
        vigencia_inicio = request.args.get("vigencia_inicio", "", type=str)
        vigencia_fin = request.args.get("vigencia_fin", "", type=str)
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("perPage", 10, type=int)

        query = Placas.query

        # Filtro: búsqueda general
        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    Placas.placa.like(like),
                    Placas.folio.like(like)
                )
            )

        # Filtro: unidad
        if unidad:
            try:
                unidad = int(unidad)
                query = query.filter(Placas.id_unidad == unidad)
            except ValueError:
                pass

        # Filtro: vigencia inicio
        if vigencia_inicio:
            fi = datetime.strptime(vigencia_inicio, "%Y-%m-%d").date()
            query = query.filter(Placas.fecha_vigencia >= fi)

        # Filtro: vigencia fin
        if vigencia_fin:
            ff = datetime.strptime(vigencia_fin, "%Y-%m-%d").date()
            query = query.filter(Placas.fecha_vigencia <= ff)

        # Paginación
        total = query.count()
        placas = (
            query.order_by(Placas.fecha_vigencia.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return jsonify({
            "total": total,
            "data": [p.to_dict() for p in placas]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/api/dashboard/unidades_completo', methods=['GET'])
def dashboard_unidades_completo():
    conn = db.engine.raw_connection()
    try:
        cursor = conn.cursor()

        id_empresa = request.args.get('id_empresa')
        sucursal = request.args.get('sucursal')

        filtros = []
        params = []

        if id_empresa:
            filtros.append("U.id_empresa = %s")
            params.append(id_empresa)

        if sucursal:
            filtros.append("U.sucursal = %s")
            params.append(sucursal)

        where_clause = f"WHERE {' AND '.join(filtros)}" if filtros else ""

        # ===================================================================
        # TOTALES GENERALES
        # ===================================================================
        query = f"""
        SELECT
            COUNT(U.id_unidad) AS total_unidades,
            COUNT(G.id_garantia) AS total_polizas
        FROM Unidades U
        LEFT JOIN (
            SELECT * FROM Garantias G1
            WHERE G1.id_garantia = (
                SELECT G2.id_garantia 
                FROM Garantias G2 
                WHERE G2.id_unidad = G1.id_unidad 
                ORDER BY G2.vigencia DESC LIMIT 1
            )
        ) G ON U.id_unidad = G.id_unidad
        {where_clause};
        """
        cursor.execute(query, tuple(params))
        row = cursor.fetchone()
        columnas = [desc[0] for desc in cursor.description]
        totales_sql = dict(zip(columnas, row))

        total_unidades = totales_sql["total_unidades"]
        total_polizas = totales_sql["total_polizas"]

        # ===================================================================
        # POR SUCURSAL (DETALLE REAL CON NOMBRE DE SUCURSAL)
        # ===================================================================
        query_sucursal = f"""
        SELECT
            U.id_unidad,
            U.marca,
            U.vehiculo,
            S.nombre AS sucursal,
            MAX(V.ultima_verificacion) AS ultima_verificacion,
            MAX(V.holograma) AS holograma,
            MAX(V.engomado) AS engomado,
            (
                SELECT COUNT(*) 
                FROM Garantias G 
                WHERE G.id_unidad = U.id_unidad
            ) AS polizas
        FROM Unidades U
        LEFT JOIN (
            SELECT * FROM VerificacionVehicular V1
            WHERE V1.id_verificacion = (
                SELECT V2.id_verificacion 
                FROM VerificacionVehicular V2 
                WHERE V2.id_unidad = V1.id_unidad 
                ORDER BY V2.ultima_verificacion DESC LIMIT 1
            )
        ) V ON U.id_unidad = V.id_unidad
        LEFT JOIN Sucursales S ON U.sucursal = S.id_sucursal
        {where_clause}
        GROUP BY U.id_unidad, U.marca, U.vehiculo, S.nombre;
        """
        cursor.execute(query_sucursal, tuple(params))
        columns_suc = [desc[0] for desc in cursor.description]
        sucursales_raw = cursor.fetchall()

        hoy = datetime.today().date()
        sucursales = {}

        for row in sucursales_raw:
            s = dict(zip(columns_suc, row))
            suc = s["sucursal"] or "N/A"

            if suc not in sucursales:
                sucursales[suc] = {
                    "sucursal": suc,
                    "unidades": 0,
                    "polizas": 0,
                    "verificacion_activa": 0,
                    "verificacion_vencida": 0,
                    "sin_verificacion": 0,
                    "proxima_verificacion": None,
                    "estado_verificacion": "N/A"
                }

            sucursales[suc]["unidades"] += 1
            sucursales[suc]["polizas"] += s["polizas"]

            fecha_base = s.get("ultima_verificacion")
            holo = (s.get("holograma") or "").strip()
            eng = (s.get("engomado") or "").strip()

            if fecha_base:
                if isinstance(fecha_base, datetime):
                    fecha_base = fecha_base.date()
                else:
                    fecha_base = datetime.strptime(str(fecha_base), "%Y-%m-%d").date()

                proxima = calcular_siguiente_verificacion(fecha_base, holo, eng)
                if proxima:
                    proxima_str = proxima.strftime("%Y-%m-%d")
                    sucursales[suc]["proxima_verificacion"] = proxima_str

                    if hoy > proxima:
                        sucursales[suc]["verificacion_vencida"] += 1
                        sucursales[suc]["estado_verificacion"] = "ATRASADA"
                    else:
                        sucursales[suc]["verificacion_activa"] += 1
                        sucursales[suc]["estado_verificacion"] = "EN TIEMPO"
                else:
                    sucursales[suc]["sin_verificacion"] += 1
                    sucursales[suc]["estado_verificacion"] = "PENDIENTE"
            else:
                sucursales[suc]["sin_verificacion"] += 1
                sucursales[suc]["estado_verificacion"] = "PENDIENTE"

        # ===================================================================
        # POR ASEGURADORA
        # ===================================================================
        query_aseguradora = f"""
        SELECT
            g.aseguradora,
            COUNT(g.id_garantia) AS total_polizas
        FROM Garantias g
        JOIN Unidades u ON g.id_unidad = u.id_unidad
        {where_clause.replace('U.', 'u.')}
        GROUP BY g.aseguradora;
        """
        cursor.execute(query_aseguradora, tuple(params))
        columns_aseg = [desc[0] for desc in cursor.description]
        aseguradoras = [dict(zip(columns_aseg, row)) for row in cursor.fetchall()]

        # ===================================================================
        # UNIDADES SIN POLIZA
        # ===================================================================
        query_sin_poliza = f"""
        SELECT u.id_unidad, u.marca, u.vehiculo, S.nombre AS sucursal
        FROM Unidades u
        LEFT JOIN Garantias g ON g.id_unidad = u.id_unidad
        LEFT JOIN Sucursales S ON u.sucursal = S.id_sucursal
        {where_clause}
        WHERE g.id_garantia IS NULL;
        """
        cursor.execute(query_sin_poliza, tuple(params))
        columns_sin = [desc[0] for desc in cursor.description]
        sin_poliza = [dict(zip(columns_sin, row)) for row in cursor.fetchall()]

        # ===================================================================
        # SALIDA FINAL
        # ===================================================================
        dashboard = {
            "totales": {
                "total_unidades": total_unidades,
                "total_polizas": total_polizas,
                "verificacion_activa": sum(s["verificacion_activa"] for s in sucursales.values()),
                "verificacion_vencida": sum(s["verificacion_vencida"] for s in sucursales.values()),
                "sin_verificacion": sum(s["sin_verificacion"] for s in sucursales.values()),
            },
            "por_sucursal": list(sucursales.values()),
            "por_aseguradora": aseguradoras,
            "unidades_sin_poliza": sin_poliza
        }

        return jsonify(dashboard), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error al generar dashboard completo", "detalle": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

##===================================================================
#Alertas del sistema mensajes
#=====================================================================                                                      
from sqlalchemy import cast, Integer

@app.route("/alertas/usuario/<int:user_id>", methods=["GET"])
def get_alertas_usuario(user_id):
    
    # Obtener usuario para verificar rol
    usuario = Usuarios.query.get(user_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    
    if usuario.rol == "admin":
        # Admin: devuelve todas las alertas
        alertas = Alerta.query.order_by(Alerta.fecha_generada.desc()).all()
        print(f"📬 Admin, total alertas: {len(alertas)}")
    else:
        # Chofer: devuelve solo alertas asignadas a su id_chofer
        if not usuario.id_chofer:
            alertas = []
        else:
            alertas = Alerta.query.filter(
                cast(Alerta.detalle['id_chofer'], Integer) == usuario.id_chofer
            ).order_by(Alerta.fecha_generada.desc()).all()
            print(f"📬 Chofer, alertas encontradas para id_chofer {usuario.id_chofer}: {len(alertas)}")

    # Construir resultado
    resultado = []
    for a in alertas:
        resultado.append({
            "id_alerta": a.id_alerta,
            "id_unidad": a.id_unidad,
            "tipo_alerta": a.tipo_alerta,
            "descripcion": a.descripcion,
            "estado": a.estado,
            "fecha_generada": a.fecha_generada.isoformat(),
            "fecha_resuelta": a.fecha_resuelta.isoformat() if a.fecha_resuelta else None,
            "detalle": a.detalle
        })

    return jsonify({"alertas": resultado})




if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000, debug=True)