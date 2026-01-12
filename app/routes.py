from flask import Blueprint, request, jsonify
from .models import db, Paciente, PacienteEspera
from datetime import datetime
import pytz

api_bp = Blueprint('api', __name__)

@api_bp.route('/crear_paciente', methods=['POST'])
def crear_paciente():
    data = request.get_json()
    n_afiliacion = data.get('numero_afiliacion')
    paciente_existente = Paciente.query.filter_by(numero_afiliacion=n_afiliacion).first()

    if paciente_existente:
        return jsonify({
            "error": "Conflict",
            "mensaje": f"El número de afiliación {n_afiliacion} ya está registrado a nombre de {paciente_existente.nombre}."
        }), 409

    try:
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

@api_bp.route('/lista_pacientes', methods=['GET'])
def obtener_pacientes():
    lista_pacientes = Paciente.query.all()
    resultado = []
    for p in lista_pacientes:
        resultado.append({
            "id": p.id, "nombre": p.nombre, "numero_afiliacion": p.numero_afiliacion,
            "fecha_nacimiento": p.fecha_nacimiento.strftime('%Y-%m-%d'),
            "sexo": p.sexo, "tipo_sangre": p.tipo_sangre, "recibe_donaciones": p.recibe_donaciones,
            "direccion": p.direccion, "celular": p.celular, "contacto_emergencia": p.contacto_emergencia,
            "enfermedades": p.enfermedades, "alergias": p.alergias, 
            "cirugias_previas": p.cirugias_previas, "medicamentos_actuales": p.medicamentos_actuales,
        })
    return jsonify(resultado)

@api_bp.route('/crear_paciente_en_espera', methods=['POST'])
def crear_paciente_en_espera():
    data = request.get_json()
    n_afiliacion = data.get('numero_afiliacion')
    paciente_existente = PacienteEspera.query.filter_by(numero_afiliacion=n_afiliacion).first()

    if paciente_existente:
        paciente_existente.estado = "1"
        paciente_existente.nombre = data.get('nombre', paciente_existente.nombre)
        db.session.commit()
        return jsonify({"mensaje": "Paciente re-ingresado a la lista de espera", "id": paciente_existente.id, "estado": "re-activado"}), 200
    else:
        nuevo_paciente = PacienteEspera(
            nombre=data['nombre'],
            numero_afiliacion=n_afiliacion,
            estado="1",
        )
        db.session.add(nuevo_paciente)
        db.session.commit()
        return jsonify({"mensaje": "Nuevo paciente registrado con éxito", "id": nuevo_paciente.id, "estado": "nuevo"}), 201

@api_bp.route('/lista_pacientes_en_espera', methods=['GET'])
def obtener_pacientes_en_espera():
    lista_pacientes = PacienteEspera.query.order_by(PacienteEspera.creado.asc()).all()
    
    tz_hermosillo = pytz.timezone('America/Hermosillo')
    
    resultado = []
    for p in lista_pacientes:
        if p.creado.tzinfo is None:
            fecha_utc = p.creado.replace(tzinfo=pytz.utc)
        else:
            fecha_utc = p.creado

        fecha_local = fecha_utc.astimezone(tz_hermosillo)
        fecha_formateada = fecha_local.strftime('%H:%M hrs')

        resultado.append({
            "id": p.id,
            "nombre": p.nombre,
            "numero_afiliacion": p.numero_afiliacion,
            "estado": p.estado,
            "creado": fecha_formateada 
        })
        
    return jsonify(resultado)

@api_bp.route('/atender_paciente/<int:id>', methods=['PUT'])
def atender_paciente(id):
    paciente = PacienteEspera.query.get(id)
    if not paciente:
        return jsonify({"error": "Paciente no encontrado"}), 404

    if paciente.estado == "1":
        paciente.estado = "2"
        db.session.commit()
        return jsonify({"mensaje": f"Estado del paciente {paciente.nombre} actualizado a 2", "id": paciente.id, "nuevo_estado": paciente.estado}), 200
    else:
        return jsonify({"mensaje": "El paciente ya tenía un estado diferente a 1"}), 400