from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List
import uvicorn

print("⭐ MICROSSERVIÇO DE CONFIRMAÇÃO DE RESERVA")
print("=" * 60)

app = FastAPI(
    title="Serviço de Confirmação",
    description="Microserviço responsável por registrar e consultar o status de confirmação de uma reserva.",
    version="1.0.0"
)

# ================== CONFIGURAÇÃO DE CORS ==================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== BANCO DE DADOS SIMULADO ==================
# Armazena o ID da reserva e o carimbo de data/hora da confirmação
# Note: Em um sistema real, o ID da reserva seria gerado no MS de Reserva.
# Aqui, usaremos a combinação ID_SALA + INICIO como um ID composto.
confirmacoes_db = [
    # Exemplo de uma reserva já confirmada
    {"id_sala": 4, "inicio": "2025-10-20 08:00", "status": "CONFIRMADA", "confirmado_em": "2025-10-18 10:30"}
]

# ================== MODELO DE DADOS ==================
class DadosConfirmacao(BaseModel):
    id_sala: int
    inicio: str  # Chave composta para identificar a reserva
    nome_responsavel: str
    
class StatusConfirmacao(BaseModel):
    id_sala: int
    inicio: str
    status: str
    confirmado_em: str

# ================== ROTAS PRINCIPAIS ==================
@app.get("/")
def home():
    return {
        "servico": "confirmacao",
        "status": "online",
        "descricao": "Gerencia o status de confirmação (pago/validado) das reservas.",
        "endpoints": {
            "confirmar_reserva": "POST /confirmar",
            "listar_confirmacoes": "GET /confirmacoes",
        }
    }

@app.get("/confirmacoes", response_model=List[StatusConfirmacao])
def listar_confirmacoes():
    """Lista todas as reservas que possuem um registro de confirmação."""
    return confirmacoes_db

@app.post("/confirmar")
def registrar_confirmacao(dados: DadosConfirmacao):
    """
    Registra que uma reserva foi confirmada ou validada.
    """
    
    # Cria uma chave de busca única (ID_SALA + INICIO)
    chave_busca = {"id_sala": dados.id_sala, "inicio": dados.inicio}

    # 1. Verifica se a confirmação já existe
    for registro in confirmacoes_db:
        if registro["id_sala"] == dados.id_sala and registro["inicio"] == dados.inicio:
            raise HTTPException(status_code=409, detail=f"Reserva de Sala {dados.id_sala} em {dados.inicio} já está confirmada.")

    # 2. Cria o novo registro de confirmação
    novo_registro = {
        "id_sala": dados.id_sala,
        "inicio": dados.inicio,
        "status": "CONFIRMADA",
        "confirmado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 3. Adiciona ao banco de dados simulado
    confirmacoes_db.append(novo_registro)
    
    return {
        "mensagem": "Reserva confirmada e registrada com sucesso!",
        "detalhes": novo_registro
    }

# ================== HEALTH CHECK ==================
@app.get("/health")
def health():
    return {"status": "ok"}

# ================== EXECUÇÃO DIRETA ==================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003, reload=False)
