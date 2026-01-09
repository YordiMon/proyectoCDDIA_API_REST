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

class PacienteEspera(db.Model):
    __tablename__ = 'lista_espera'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), nullable=False)
    numero_afiliacion = db.Column(db.String(8), unique=True, nullable=False)
    estado = db.Column(db.String(1), nullable=False)


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
    
    # 1. Extraer el número de afiliación para validar
    n_afiliacion = data.get('numero_afiliacion')

    # 2. Buscar si ya existe un paciente con ese número
    paciente_existente = Paciente.query.filter_by(numero_afiliacion=n_afiliacion).first()

    if paciente_existente:
        # Si ya existe, enviamos un mensaje de error
        return jsonify({
            "error": "Conflict",
            "mensaje": f"El número de afiliación {n_afiliacion} ya está registrado a nombre de {paciente_existente.nombre}."
        }), 409  # 409 es el código estándar para conflictos de datos duplicados

    # 3. Si no existe, procedemos con la creación normal
    try:
        # Convertir string de fecha "YYYY-MM-DD" a objeto Date de Python
        fecha_dt = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()

        nuevo_paciente = Paciente(
            nombre=data['nombre'],
            numero_afiliacion=n_afiliacion,
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
        
    except Exception as e:
        return jsonify({"error": "Error al procesar la fecha o datos", "detalle": str(e)}), 400

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
            "recibe_donaciones": p.recibe_donaciones,
            "direccion": p.direccion,
            "celular": p.celular,
            "contacto_emergencia": p.contacto_emergencia,
            "enfermedades": p.enfermedades,
            "alergias": p.alergias,
            "cirugias_previas": p.cirugias_previas,
            "medicamentos_actuales": p.medicamentos_actuales,
        })
    return jsonify(resultado)

@app.route('/crear_paciente_en_espera', methods=['POST'])
def crear_paciente_en_espera():
    data = request.get_json()
    n_afiliacion = data.get('numero_afiliacion')

    # 1. Buscar si el paciente ya existe en la base de datos
    paciente_existente = PacienteEspera.query.filter_by(numero_afiliacion=n_afiliacion).first()

    if paciente_existente:
        # 2. Si existe, simplemente actualizamos su estado a "1" (en espera)
        # También podrías actualizar el nombre por si cambió o se escribió mal antes
        paciente_existente.estado = "1"
        paciente_existente.nombre = data.get('nombre', paciente_existente.nombre)
        
        db.session.commit()
        
        return jsonify({
            "mensaje": "Paciente re-ingresado a la lista de espera", 
            "id": paciente_existente.id,
            "estado": "re-activado"
        }), 200

    else:
        # 3. Si no existe, creamos el nuevo registro desde cero
        nuevo_paciente = PacienteEspera(
            nombre=data['nombre'],
            numero_afiliacion=n_afiliacion,
            estado="1",
        )
        
        db.session.add(nuevo_paciente)
        db.session.commit()
        
        return jsonify({
            "mensaje": "Nuevo paciente registrado con éxito", 
            "id": nuevo_paciente.id,
            "estado": "nuevo"
        }), 201

@app.route('/lista_pacientes_en_espera', methods=['GET'])
def obtener_pacientes_en_espera():
    lista_pacientes = PacienteEspera.query.all()
    resultado = []
    for p in lista_pacientes:
        resultado.append({
            "id": p.id,
            "nombre": p.nombre,
            "numero_afiliacion": p.numero_afiliacion,
            "estado": p.estado,
        })
    return jsonify(resultado)

@app.route('/atender_paciente/<int:id>', methods=['PUT'])
def atender_paciente(id):
    # 1. Buscar al paciente por su ID
    paciente = PacienteEspera.query.get(id)

    # 2. Verificar si el paciente existe
    if not paciente:
        return jsonify({"error": "Paciente no encontrado"}), 404

    # 3. Cambiar el estado de 1 a 2
    if paciente.estado == "1":
        paciente.estado = "2"
        db.session.commit()
        return jsonify({
            "mensaje": f"Estado del paciente {paciente.nombre} actualizado a 2 (Atendido)",
            "id": paciente.id,
            "nuevo_estado": paciente.estado
        }), 200
    else:
        return jsonify({"mensaje": "El paciente ya tenía un estado diferente a 1"}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)