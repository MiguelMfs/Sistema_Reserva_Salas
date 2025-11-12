from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import requests



app = FastAPI(
    title="Serviço de disparo de email após confirmação da reserva de sala",
    description="Microserviço responsável pela disparo de email",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DadosEmail(BaseModel):
    email_pessoa: str
    nome_sala: str
    data_reserva: str
    hora_inicio: str
    nome_pessoa: str

@app.get("/")
def home():
    return {
        "servico": "Disparo de email",
        "status": "online",
        "descricao": "Microserviço de disparo de email ativo e pronto para o gateway",
        "endpoints": {
            "enviar_confirmacao_reserva": "/email",
        }
    }

@app.post("/email")
def disparo_de_email(dadosEmail: DadosEmail):


    corpo_texto = f"""
    Olá {dadosEmail.nome_pessoa},

    Este é o e-mail de confirmação da reserva de sala.

    Detalhes da Reserva:
    - Sala: {dadosEmail.nome_sala}
    - Data: {dadosEmail.data_reserva}
    - Hora: {dadosEmail.hora_inicio}
    - Destinatário: {dadosEmail.email_pessoa}

    Obrigado!
    """

    print("=" * 60)
    print("DISPARO DE E-MAIL BEM-SUCEDIDO!")
    print(corpo_texto)
    print("=" * 60)


    return {
        "mensagem": "E-mail de confirmação disparado com sucesso!",
        "destinatario": dadosEmail.email_pessoa,
        "sala": dadosEmail.nome_sala
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004, reload=False)