import threading, time
import uvicorn

from service.consultar_salas import app as consultar_sala_app
from service.disparo_de_email import app as disparo_email_app
from service.disparo_evento import app as disparo_evento_app
from service.reserva import app as reserva_app
from service.verificar_disponibilidade import app as verificar_disponibilidade_app
from service.main import app as gateway_app

def run(app, port):
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info")
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    threads = [
        threading.Thread(target=run, args=(consultar_sala_app, 8001), daemon=True),
        threading.Thread(target=run, args=(disparo_email_app, 8004), daemon=True),
        threading.Thread(target=run, args=(disparo_evento_app, 8005), daemon=True),
        threading.Thread(target=run, args=(reserva_app, 8003), daemon=True), 
        threading.Thread(target=run, args=(verificar_disponibilidade_app, 8002), daemon=True), 
        threading.Thread(target=run, args=(gateway_app, 8010), daemon=True)
    ]
    for t in threads: t.start()
    print("Services up: academico:8010, salas:8001, turmas:8002, notas:8003")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")