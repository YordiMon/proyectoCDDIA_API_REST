from flask import Flask
from flask_cors import CORS
from .models import db
import os
import time
from sqlalchemy.exc import OperationalError 

def create_app():
    app = Flask(__name__)
    
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

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
                time.sleep(3)
        
        if retries == 0:
            print("Error crítico: No se pudo conectar a la base de datos después de varios intentos.")

    from .routes import api_bp
    app.register_blueprint(api_bp)

    return app