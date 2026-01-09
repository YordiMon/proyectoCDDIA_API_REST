from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)
    numero_afiliacion = db.Column(db.String(8), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    sexo = db.Column(db.String(10), nullable=False)
    tipo_sangre = db.Column(db.String(5), nullable=False)
    recibe_donaciones = db.Column(db.Boolean, nullable=False)
    direccion = db.Column(db.String(120), nullable=False)
    celular = db.Column(db.String(15), nullable=False)
    contacto_emergencia = db.Column(db.String(15), nullable=True)
    enfermedades = db.Column(db.Text, nullable=True)
    alergias = db.Column(db.Text, nullable=True)
    cirugias_previas = db.Column(db.Text, nullable=True)
    medicamentos_actuales = db.Column(db.Text, nullable=True)

class PacienteEspera(db.Model):
    __tablename__ = 'lista_espera'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)
    numero_afiliacion = db.Column(db.String(8), unique=True, nullable=False)
    estado = db.Column(db.String(1), nullable=False)