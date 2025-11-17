from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import uvicorn

print("MICROSSERVIÇO DE VERIFICAÇÃO DE DISPONIBILIDADE")
print("=" * 60)

app = FastAPI(
    title="Serviço de Verificação de Disponibilidade",
    description="Microserviço responsável por verificar se uma sala está disponível em determinado horário.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== BANCO DE DADOS SIMULADO ==================
# Cada sala tem uma lista de reservas (intervalos de horário ocupados)
reservas_db = [
    {"id_sala": 1, "reservas": [("2025-10-20 14:00", "2025-10-20 15:00")]},
    {"id_sala": 2, "reservas": [("2025-10-20 09:00", "2025-10-20 11:00")]},
    {"id_sala": 3, "reservas": []},
    {"id_sala": 4, "reservas": [("2025-10-20 08:00", "2025-10-20 10:00")]},
    {"id_sala": 5, "reservas": [("2025-10-20 13:00", "2025-10-20 14:00")]},
]

class Verificacao(BaseModel):
    id_sala: int
    inicio: str  # formato: "YYYY-MM-DD HH:MM"
    fim: str     # formato: "YYYY-MM-DD HH:MM"

@app.get("/")
def home():
    return {
        "servico": "verificar_disponibilidade",
        "status": "online",
        "descricao": "Verifica se uma sala está livre em um horário específico.",
        "endpoints": {
            "verificar": "/verificar",
            "todas_reservas": "/reservas",
        }
    }

@app.get("/reservas")
def listar_reservas():
    """Lista todas as reservas registradas (banco simulado)."""
    return {"total": len(reservas_db), "reservas": reservas_db}

@app.post("/verificar")
def verificar_disponibilidade(dados: Verificacao):
    """Verifica se a sala informada está disponível no horário solicitado."""
    try:
        inicio = datetime.strptime(dados.inicio, "%Y-%m-%d %H:%M")
        fim = datetime.strptime(dados.fim, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use o formato: YYYY-MM-DD HH:MM")

    if inicio >= fim:
        raise HTTPException(status_code=400, detail="A data/hora inicial deve ser anterior à final.")

    # Busca a sala nas reservas
    for registro in reservas_db:
        if registro["id_sala"] == dados.id_sala:
            # Verifica sobreposição de horários
            for reserva in registro["reservas"]:
                inicio_reserva = datetime.strptime(reserva[0], "%Y-%m-%d %H:%M")
                fim_reserva = datetime.strptime(reserva[1], "%Y-%m-%d %H:%M")

                # Se houver conflito de horário
                if not (fim <= inicio_reserva or inicio >= fim_reserva):
                    return {
                        "id_sala": dados.id_sala,
                        "disponivel": False,
                        "mensagem": f"Sala ocupada entre {reserva[0]} e {reserva[1]}."
                    }
            # Se não houver conflito
            return {
                "id_sala": dados.id_sala,
                "disponivel": True,
                "mensagem": "Sala disponível no horário solicitado."
            }

    # Se a sala não existir no banco
    raise HTTPException(status_code=404, detail="Sala não encontrada.")

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("verificar_disponibilidade_service:app", host="0.0.0.0", port=8005, reload=True)