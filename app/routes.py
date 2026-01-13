from flask import Blueprint, request, jsonify
from .models import Consulta, db, Paciente, PacienteEspera
from datetime import datetime

# Creamos el Blueprint para agrupar las rutas
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
    lista_pacientes = PacienteEspera.query.all()
    resultado = [{"id": p.id, "nombre": p.nombre, "numero_afiliacion": p.numero_afiliacion, "estado": p.estado} for p in lista_pacientes]
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
    
# rutas para consultas

#crear consulta
@api_bp.route('', methods=['POST'])
def crear_consulta():
    data = request.json

    nueva_consulta = Consulta(
        paciente_id=data['paciente_id'],
        fecha_consulta=datetime.fromisoformat(data['fecha_consulta']),
        motivo=data['motivo'],
        sintonmas=data.get('sintonmas'),
        tiempo_enfermedad=data.get('tiempo_enfermedad'),
        presion=data.get('presion'),
        frecuencia_cardiaca=data.get('frecuencia_cardiaca'),
        frecuencia_respiratoria=data.get('frecuencia_respiratoria'),
        temperatura=data.get('temperatura'),
        peso=data.get('peso'),
        talla=data.get('talla'),
        diagnostico=data.get('diagnostico'),
        medicamentos_recetados=data.get('medicamentos_recetados'),
        observaciones=data.get('observaciones')
    )

    db.session.add(nueva_consulta)
    db.session.commit()

    return jsonify({
        "message": "Consulta creada",
        "consulta_id": nueva_consulta.id
    }), 201

#consultar consultas por paciente

@api_bp.route('/consultas/paciente/<int:paciente_id>', methods=['GET'])
def consultas_por_paciente(paciente_id):
    consultas = Consulta.query.filter_by(
        paciente_id=paciente_id
    ).order_by(Consulta.fecha_consulta.desc()).all()

    return jsonify([
        {
            "id": c.id,
            "fecha_consulta": c.fecha_consulta.isoformat(),
            "motivo": c.motivo,
            "diagnostico": c.diagnostico
        } for c in consultas
    ])

#obtener detalles de una consulta
@api_bp.route('/consultas/<int:consulta_id>', methods=['GET'])
def obtener_consulta(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)

    return jsonify({
        "id": consulta.id,
        "paciente_id": consulta.paciente_id,
        "fecha_consulta": consulta.fecha_consulta.isoformat(),
        "motivo": consulta.motivo,
        "sintonmas": consulta.sintonmas,
        "tiempo_enfermedad": consulta.tiempo_enfermedad,
        "presion": consulta.presion,
        "frecuencia_cardiaca": consulta.frecuencia_cardiaca,
        "frecuencia_respiratoria": consulta.frecuencia_respiratoria,
        "temperatura": consulta.temperatura,
        "peso": consulta.peso,
        "talla": consulta.talla,
        "diagnostico": consulta.diagnostico,
        "medicamentos_recetados": consulta.medicamentos_recetados,
        "observaciones": consulta.observaciones
    })

#actualizar una consulta
@api_bp.route('/consultas/<int:consulta_id>', methods=['PUT'])
def actualizar_consulta(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    data = request.json

    consulta.motivo = data.get('motivo', consulta.motivo)
    consulta.sintonmas = data.get('sintonmas', consulta.sintonmas)
    consulta.tiempo_enfermedad = data.get('tiempo_enfermedad', consulta.tiempo_enfermedad)
    consulta.presion = data.get('presion', consulta.presion)
    consulta.frecuencia_cardiaca = data.get('frecuencia_cardiaca', consulta.frecuencia_cardiaca)
    consulta.frecuencia_respiratoria = data.get('frecuencia_respiratoria', consulta.frecuencia_respiratoria)
    consulta.temperatura = data.get('temperatura', consulta.temperatura)
    consulta.peso = data.get('peso', consulta.peso)
    consulta.talla = data.get('talla', consulta.talla)
    consulta.diagnostico = data.get('diagnostico', consulta.diagnostico)
    consulta.medicamentos_recetados = data.get('medicamentos_recetados', consulta.medicamentos_recetados)
    consulta.observaciones = data.get('observaciones', consulta.observaciones)

    db.session.commit()

    return jsonify({"message": "Consulta actualizada"})

# eliminar una consulta
@api_bp.route('/consultas/<int:consulta_id>', methods=['DELETE'])
def eliminar_consulta(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)

    db.session.delete(consulta)
    db.session.commit()

    return jsonify({"message": "Consulta eliminada"})
