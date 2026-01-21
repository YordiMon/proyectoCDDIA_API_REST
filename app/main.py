import time
import os
from app import create_app, db

app = create_app()

# Bloque de inicialización de Base de Datos
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

if __name__ == '__main__':
    # Importante: host 0.0.0.0 para que sea visible desde fuera de Docker
    app.run(host='0.0.0.0', port=5000)