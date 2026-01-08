import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Configuración de la conexión
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la Base de Datos
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

with app.app_context():
    intentos = 0
    while intentos < 10:
        try:
            db.create_all()
            print("¡Base de datos conectada y tablas creadas!")
            break
        except Exception as e:
            intentos += 1
            print(f"Esperando a la base de datos... (Intento {intentos}/10)")
            time.sleep(2) 

# --- RUTAS DE LA API ---

@app.route('/crear_paciente', methods=['POST'])
def crear_paciente():
    data = request.get_json()
    
    # Convertir string de fecha "YYYY-MM-DD" a objeto Date de Python
    fecha_dt = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()

    nuevo_paciente = Paciente(
        nombre=data['nombre'],
        numero_afiliacion=data['numero_afiliacion'],
        fecha_nacimiento=fecha_dt,
        sexo=data['sexo'],
        tipo_sangre=data['tipo_sangre'],
        recibe_donaciones=data['recibe_donaciones'],
        direccion=data['direccion'],
        celular=data['celular'],
        contacto_emergencia=data['contacto_emergencia'],
        enfermedades=data.get('enfermedades'),
        alergias=data.get('alergias'),
        cirugias_previas=data.get('cirugias_previas'),
        medicamentos_actuales=data.get('medicamentos_actuales')
    )
    
    db.session.add(nuevo_paciente)
    db.session.commit()
    return jsonify({"mensaje": "Paciente registrado con éxito", "id": nuevo_paciente.id}), 201

@app.route('/lista_pacientes', methods=['GET'])
def obtener_pacientes():
    lista_pacientes = Paciente.query.all()
    resultado = []
    for p in lista_pacientes:
        resultado.append({
            "id": p.id,
            "nombre": p.nombre,
            "numero_afiliacion": p.numero_afiliacion,
            "fecha_nacimiento": p.fecha_nacimiento.strftime('%Y-%m-%d'),
            "sexo": p.sexo,
            "tipo_sangre": p.tipo_sangre,
            "enfermedades": p.enfermedades
        })
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)