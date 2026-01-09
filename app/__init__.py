from flask import Flask
from .models import db
import os

def create_app():
    app = Flask(__name__)
    
    # Configuración de la conexión
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)

    # Registrar las rutas del Blueprint
    from .routes import api_bp
    app.register_blueprint(api_bp)

    return app