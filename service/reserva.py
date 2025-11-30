from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List
import uvicorn

print("⭐ MICROSSERVIÇO DE RESERVA DE SALA")
print("=" * 60)

app = FastAPI(
    title="Serviço de Reserva de Sala",
    description="Microserviço responsável por registrar reservas e confirmar status.",
    version="1.0.0"
)

# ================== CONFIGURAÇÃO CORS ==================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== BANCO SIMULADO ==================
confirmacoes_db = []

# ================== MODELO QUE BATE COM O GATEWAY ==================
class ReservaEntrada(BaseModel):
    sala_id: int
    data: str = Field(..., description="YYYY-MM-DD")
    hora_inicio: str = Field(..., description="HH:MM")
    hora_fim: str = Field(..., description="HH:MM")
    usuario_nome: str
    usuario_email: EmailStr

# Modelo de retorno opcional para listar
class StatusConfirmacao(BaseModel):
    reserva_id: int
    sala_id: int
    inicio: str
    fim: str
    status: str
    confirmado_em: str
    usuario_email: str

# ================== LISTAR RESERVAS ==================
@app.get("/confirmacoes", response_model=List[StatusConfirmacao])
def listar_confirmacoes():
    return confirmacoes_db

# ================== NOVA ROTA /reservar ==================
@app.post("/reservar")
def registrar_reserva(reserva: ReservaEntrada):
    inicio = f"{reserva.data} {reserva.hora_inicio}"
    fim = f"{reserva.data} {reserva.hora_fim}"

    # 1. Verificar duplicação
    for r in confirmacoes_db:
        if r["sala_id"] == reserva.sala_id and r["inicio"] == inicio:
            raise HTTPException(
                status_code=409,
                detail=f"Sala '{reserva.sala_id}' em '{inicio}' já reservada."
            )

    # 2. Registrar reserva
    novo = {
        "reserva_id": len(confirmacoes_db) + 1,
        "sala_id": reserva.sala_id,
        "inicio": inicio,
        "fim": fim,
        "status": "CONFIRMADA",
        "confirmado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "usuario_email": reserva.usuario_email
    }

    confirmacoes_db.append(novo)

    return {
        "mensagem": "Reserva registrada com sucesso!",
        "detalhes": {"reserva_id": novo["reserva_id"], **novo}
    }

# ================== HEALTH CHECK ==================
@app.get("/health")
def health():
    return {"status": "ok"}

# ================== EXECUÇÃO ==================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003, reload=False)
