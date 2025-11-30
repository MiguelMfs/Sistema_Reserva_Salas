from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import uvicorn

print("🕒 MICROSSERVIÇO DE VERIFICAÇÃO DE DISPONIBILIDADE")
print("=" * 60)

app = FastAPI(
    title="Serviço de Verificação de Disponibilidade",
    description="Verifica se uma sala está disponível em um horário específico.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Banco simulado de reservas
# IDs iguais ao serviço de consulta:

reservas_db = [
    {"id_sala": "LAB-01", "reservas": [("2025-10-20 14:00", "2025-10-20 15:00")]},
    {"id_sala": "LAB-02", "reservas": [("2025-10-20 09:00", "2025-10-20 11:00")]},
    {"id_sala": "SALA-01", "reservas": []},
]

# -------------------------------
# Modelo para entrada
# -------------------------------
class Verificacao(BaseModel):
    id_sala: str
    inicio: str   # formato "YYYY-MM-DD HH:MM"
    fim: str      # formato "YYYY-MM-DD HH:MM"

@app.get("/", tags=["Health"])
def home():
    return {
        "servico": "verificar_disponibilidade",
        "status": "online",
        "descricao": "Verifica se uma sala está livre em um horário específico.",
        "endpoints": {
            "POST verificar": "/verificar",
            "GET todas_reservas": "/reservas",
        }
    }


@app.get("/reservas", tags=["Reservas"])
def listar_reservas():
    """Lista todas as reservas registradas."""
    return {"total": len(reservas_db), "reservas": reservas_db}


@app.post("/verificar", tags=["Verificação"])
def verificar_disponibilidade(dados: Verificacao):
    """Verifica se a sala está livre no horário solicitado."""

    # Conversão de datas
    try:
        inicio = datetime.strptime(dados.inicio, "%Y-%m-%d %H:%M")
        fim = datetime.strptime(dados.fim, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de data inválido. Use 'YYYY-MM-DD HH:MM'"
        )

    if inicio >= fim:
        raise HTTPException(
            status_code=400,
            detail="A data/hora inicial deve ser anterior à final."
        )

    # Procura a sala no banco
    for registro in reservas_db:
        if registro["id_sala"] == dados.id_sala:

            # Verifica conflitos com reservas existentes
            for reserva in registro["reservas"]:
                inicio_reserva = datetime.strptime(reserva[0], "%Y-%m-%d %H:%M")
                fim_reserva = datetime.strptime(reserva[1], "%Y-%m-%d %H:%M")

                # Verificar sobreposição
                if not (fim <= inicio_reserva or inicio >= fim_reserva):
                    return {
                        "id_sala": dados.id_sala,
                        "disponivel": False,
                        "mensagem": f"Sala ocupada entre {reserva[0]} e {reserva[1]}."
                    }

            # Sem conflitos → disponível
            return {
                "id_sala": dados.id_sala,
                "disponivel": True,
                "mensagem": "Sala disponível no horário solicitado."
            }

    # Se sala não encontrada
    raise HTTPException(status_code=404, detail="Sala não encontrada.")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


# -------------------------------
# Execução local
# -------------------------------
if __name__ == "__main__":
    print("\n🚀 Serviço de Verificação de Disponibilidade rodando na porta 8002\n")
    uvicorn.run(app, host="0.0.0.0", port=8002)
