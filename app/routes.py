from pickle import GET
from flask import Blueprint, request, jsonify
from .models import db, Paciente, PacienteEspera
from . import models
from datetime import datetime
import pytz
from sqlalchemy import or_, and_

api_bp = Blueprint('api', __name__)

#rutas para crear pacientes
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
        fecha_nacimiento = data.get('fecha_nacimiento')
        if not fecha_nacimiento:
            return jsonify({"error": "El campo 'fecha_nacimiento' es obligatorio."}), 400

        fecha_dt = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
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

#ruta para obtener lista de pacientes
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

#para obtener paciente por numero de afiliacion
@api_bp.route('/paciente/<numero_afiliacion>', methods=['GET'])
def obtener_paciente_por_afiliacion(numero_afiliacion):
    """
    Obtiene los datos de un paciente por su número de afiliación
    """
    try:
        paciente = models.Paciente.query.filter_by(numero_afiliacion=numero_afiliacion).first()
        
        
        if not paciente:
            return jsonify({"error": "Paciente no encontrado"}), 404
        
        return jsonify({
            "paciente_id": paciente.id,
            "nombre": paciente.nombre,
            "numero_afiliacion": paciente.numero_afiliacion
        }), 200
    
    except Exception as e:
        return jsonify({"error": "Error al buscar paciente", "detalle": str(e)}), 500

#rutas para lista de espera
@api_bp.route('/crear_paciente_en_espera', methods=['POST'])
def crear_paciente_en_espera():
    data = request.get_json()
    n_afiliacion = data.get('numero_afiliacion')
    
    # Buscamos si el paciente ya tiene un registro en la tabla de espera
    paciente_existente = PacienteEspera.query.filter_by(numero_afiliacion=n_afiliacion).first()

    if paciente_existente:
        # ACTUALIZACIÓN: El paciente ya existía, así que "reciclamos" el registro
        paciente_existente.estado = "1"
        paciente_existente.nombre = data.get('nombre', paciente_existente.nombre)
        # Aquí actualizamos el área con el nuevo dato enviado
        paciente_existente.area = data.get('area', paciente_existente.area)
        
        db.session.commit()
        return jsonify({
            "mensaje": f"Paciente re-ingresado a {paciente_existente.area}", 
            "id": paciente_existente.id, 
            "estado": "re-activado"
        }), 200
    else:
        # CREACIÓN: Es la primera vez que este paciente entra a la tabla de espera
        nuevo_paciente = PacienteEspera(
            nombre=data['nombre'],
            numero_afiliacion=n_afiliacion,
            area=data['area'],
            estado="1",
        )
        db.session.add(nuevo_paciente)
        db.session.commit()
        return jsonify({
            "mensaje": f"Nuevo paciente registrado en {nuevo_paciente.area}", 
            "id": nuevo_paciente.id, 
            "estado": "nuevo"
        }), 201

#ruta para obtener lista de pacientes en espera
@api_bp.route('/lista_pacientes_en_espera', methods=['GET'])
def obtener_pacientes_en_espera():
    # 1. Obtener pacientes filtrados (Estado 1 y 2)
    lista_pacientes = PacienteEspera.query.filter(
        PacienteEspera.estado.in_(['1', '2'])
    ).order_by(PacienteEspera.creado.asc()).all()
    
    # 2. Contar cuántos están SOLO en espera (Estado 1) para el resumen
    conteo_espera = PacienteEspera.query.filter_by(estado='1').count()
    
    tz_hermosillo = pytz.timezone('America/Hermosillo')
    
    pacientes_json = []
    for p in lista_pacientes:
        if p.creado.tzinfo is None:
            fecha_utc = p.creado.replace(tzinfo=pytz.utc)
        else:
            fecha_utc = p.creado

        fecha_local = fecha_utc.astimezone(tz_hermosillo)
        fecha_formateada = fecha_local.strftime('%H:%M hrs')

        pacientes_json.append({
            "id": p.id,
            "nombre": p.nombre,
            "numero_afiliacion": p.numero_afiliacion,
            "area": p.area,
            "estado": p.estado,
            "creado": fecha_formateada 
        })
        
    # Devolvemos estructura completa
    return jsonify({
        "resumen": {
            "total_espera": conteo_espera
        },
        "pacientes": pacientes_json
    })

#ruta para quitar paciente de la lista de espera
@api_bp.route('/quitar_paciente/<int:id>', methods=['PUT'])
def quitar_paciente(id):
    paciente = PacienteEspera.query.get(id)
    if not paciente:
        return jsonify({"error": "Paciente no encontrado"}), 400

    # Cambiamos el estado a 3 (Inactivo/Quitado)
    paciente.estado = "3"
    db.session.commit()
    return jsonify({"mensaje": f"Paciente {paciente.nombre} removido de la lista", "id": paciente.id}), 200


#ruta para actualizar estado de paciente en espera
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
    
#Rutas para consultas

# Crear consulta
@api_bp.route('/consultas', methods=['POST'])
def crear_consulta():
    data = request.get_json()
    # Definimos la zona horaria de Sonora
    sonora_tz = pytz.timezone('America/Hermosillo')

    if not data:
        return jsonify({"error": "Cuerpo JSON vacío"}), 400

    # Validación de campos obligatorios
    paciente_id = data.get('paciente_id')
    motivo = data.get('motivo')
    if not paciente_id or not motivo:
        return jsonify({"error": "paciente_id y motivo son requeridos"}), 400

    # --- PROCESAMIENTO DE FECHA LOCAL ---
    fecha_raw = data.get('fecha_consulta')
    try:
        if fecha_raw:
            # Eliminamos la 'Z' (si existe) para que fromisoformat no la mande a UTC
            fecha_dt = datetime.fromisoformat(fecha_raw.replace('Z', ''))
            # Localizamos la fecha como "Hora de Sonora"
            fecha_dt = sonora_tz.localize(fecha_dt)
        else:
            # Si no hay fecha, capturamos el "Ahora" de Sonora directamente
            fecha_dt = datetime.now(sonora_tz)
    except Exception as e:
        return jsonify({"error": "Formato de fecha inválido", "detalle": str(e)}), 400

    nueva_consulta = models.Consulta(
        paciente_id=paciente_id,
        fecha_consulta=fecha_dt, # SQLAlchemy guardará con la info de zona horaria
        motivo=motivo,
        sintomas=data.get('sintomas'),
        tiempo_enfermedad=data.get('tiempo_enfermedad'),
        presion=data.get('presion'), # Recibido desde consultaData en React
        frecuencia_cardiaca=data.get('frecuencia_cardiaca'),
        frecuencia_respiratoria=data.get('frecuencia_respiratoria'),
        temperatura=data.get('temperatura'),
        peso=data.get('peso'),
        talla=data.get('talla'),
        diagnostico=data.get('diagnostico'),
        medicamentos_recetados=data.get('medicamentos_recetados'),
        observaciones=data.get('observaciones')
    )

    try:
        db.session.add(nueva_consulta)
        db.session.commit()
        return jsonify({
            "message": "Consulta creada exitosamente",
            "consulta_id": nueva_consulta.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error de base de datos", "detalle": str(e)}), 500

#consultar consultas por paciente

@api_bp.route('/consultas/paciente/<int:paciente_id>', methods=['GET'])
def consultas_por_paciente(paciente_id):
    # Zona horaria de Hermosillo
    sonora_tz = pytz.timezone('America/Hermosillo')

    resultados = db.session.query(models.Consulta, models.Paciente.nombre)\
        .join(models.Paciente, models.Consulta.paciente_id == models.Paciente.id)\
        .filter(models.Consulta.paciente_id == paciente_id)\
        .order_by(models.Consulta.fecha_consulta.desc())\
        .all()

    if not resultados:
        return jsonify({"message": "No se encontraron consultas para este paciente"}), 404

    lista_consultas = []
    for consulta, nombre_paciente in resultados:
        # 1. Obtener la fecha de la base de datos
        fecha_db = consulta.fecha_consulta
        
        # 2. Si la fecha no tiene zona horaria (naive), le asignamos la de Sonora
        # Si ya la tiene, la convertimos para asegurar que el offset sea -07:00
        if fecha_db.tzinfo is None:
            fecha_local = sonora_tz.localize(fecha_db)
        else:
            fecha_local = fecha_db.astimezone(sonora_tz)

        lista_consultas.append({
            "id": consulta.id,
            "paciente_id": consulta.paciente_id,
            "nombre_paciente": nombre_paciente,
            "fecha_consulta": fecha_local.isoformat(), # Enviará: 2024-05-20T14:30:00-07:00
            "motivo": consulta.motivo,
            "sintomas": consulta.sintomas,
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

    return jsonify(lista_consultas)

#obtener detalles de una consulta
@api_bp.route('/consultas/<int:consulta_id>', methods=['GET'])
def obtener_consulta(consulta_id):
    consulta = models.Consulta.query.get_or_404(consulta_id)

    return jsonify({
        "id": consulta.id,
        "paciente_id": consulta.paciente_id,
        "fecha_consulta": consulta.fecha_consulta.isoformat(),
        "motivo": consulta.motivo,
        "sintomas": consulta.sintomas,
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
    consulta = models.Consulta.query.get_or_404(consulta_id)
    data = request.json

    consulta.motivo = data.get('motivo', consulta.motivo)
    consulta.sintomas = data.get('sintomas', consulta.sintomas)
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
    consulta = models.Consulta.query.get_or_404(consulta_id)

    db.session.delete(consulta)
    db.session.commit()

    return jsonify({"message": "Consulta eliminada"})

#rutas para pacientes
#buscar nombre de paciente o numero de afiliacion en la tabla pacientes
@api_bp.route('/paciente_existe/<string:numero_afiliacion>', methods=['GET'])
def paciente_existe(numero_afiliacion):
    paciente = Paciente.query.filter_by(numero_afiliacion=numero_afiliacion).first()
    try:
        if paciente:
            return jsonify({
                "existe": True,
                "nombre": paciente.nombre
            }) 
        else:
            return jsonify({"existe": False})
    except Exception as e:
        return jsonify({
            "error": "Error al verificar paciente",
            "detalle": str(e)
        }), 500

@api_bp.route('/api/pacientes/buscar-historial', methods=['GET'])
def buscar_pacientes_historial():
    query_text = request.args.get('q', '')
    
    if not query_text or len(query_text) < 2:
        return jsonify([])

    # Realizamos la búsqueda con un JOIN
    resultados = (
        PacienteEspera.query
        # 1. Unimos con la tabla Paciente basándonos en el número de afiliación
        .join(Paciente, PacienteEspera.numero_afiliacion == Paciente.numero_afiliacion)
        # 2. Aplicamos los filtros
        .filter(
            and_(
                PacienteEspera.estado == '3',
                or_(
                    PacienteEspera.numero_afiliacion.ilike(f'%{query_text}%'),
                    PacienteEspera.nombre.ilike(f'%{query_text}%')
                )
            )
        )
        .limit(10)
        .all()
    )

    return jsonify([{
        'id': p.id,
        'nombre': p.nombre,
        'numero_afiliacion': p.numero_afiliacion,
        'area': p.area,
        'estado': p.estado
    } for p in resultados])

#ruta para quitar paciente de la lista de espera por numero de afiliacion
@api_bp.route('/quitar_paciente_por_afiliacion/<string:numero_afiliacion>', methods=['PUT'])
def quitar_paciente_por_afiliacion(numero_afiliacion):
    paciente = PacienteEspera.query.filter_by(numero_afiliacion=numero_afiliacion, estado='2').first()
    if not paciente:
        return jsonify({"error": "Paciente no encontrado o no está en estado '2'"}), 404

    # Cambiamos el estado a 3 (Inactivo/Quitado)
    paciente.estado = "3"
    db.session.commit()
    return jsonify({"mensaje": f"Paciente {paciente.nombre} removido de la lista", "id": paciente.id,
    "numero_afiliacion": paciente.numero_afiliacion,
    "estado": paciente.estado
}), 200


#ruta para actualizar estado de paciente en espera por numero de afiliacion
@api_bp.route('/marcar_paciente/<string:numero_afiliacion>', methods=['PUT'])
def marcar_paciente(numero_afiliacion):
    paciente = PacienteEspera.query.filter_by(
        numero_afiliacion=numero_afiliacion,
        estado='1'  # En espera
    ).first()

    if not paciente:
        return jsonify({
            "marcado": False,
            "mensaje": "Paciente no estaba en espera"
        }), 200

    paciente.estado = '2'  # En atención
    db.session.commit()

    return jsonify({
        "marcado": True,
        "id": paciente.id,
        "mensaje": "Paciente marcado como en atención"
    }), 200
