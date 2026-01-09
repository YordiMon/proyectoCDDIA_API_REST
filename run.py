import time
from app import create_app, db 

app = create_app()

if __name__ == '__main__':
    # Bloque de reintento para la base de datos
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

    # Iniciar servidor
    app.run(host='0.0.0.0', port=5000)