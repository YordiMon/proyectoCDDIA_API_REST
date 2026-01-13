from flask import Flask
from flask_cors import CORS
from .models import db
import os
import time
# IMPORTANTE: Estas dos importaciones son necesarias para los reintentos
from sqlalchemy.exc import OperationalError 

def create_app():
    app = Flask(__name__)
    
    # Configuración de CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Configuración de la base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

    # Lógica de reintentos para esperar a que el contenedor 'db' esté listo
    with app.app_context():
        retries = 10
        while retries > 0:
            try:
                db.create_all()
                print("¡Conexión a la base de datos establecida exitosamente!")
                break
            except (OperationalError, Exception) as e:
                retries -= 1
                print(f"Esperando a la base de datos... ({retries} reintentos restantes)")
                time.sleep(3) # Espera 3 segundos antes de volver a intentar
        
        if retries == 0:
            print("Error crítico: No se pudo conectar a la base de datos después de varios intentos.")

    # Registrar las rutas del Blueprint
    from .routes import api_bp
    app.register_blueprint(api_bp)

    return app