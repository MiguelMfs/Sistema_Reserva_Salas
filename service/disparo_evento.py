from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import tempfile
import os
from datetime import datetime
import uvicorn

app = FastAPI(
    title="Serviço de Disparo de Evento (.ics)",
    description="Microserviço responsável por gerar e enviar eventos de calendário após reserva",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DadosEvento(BaseModel):
    email: EmailStr
    titulo: str
    descricao: str
    local: str
    data: str          
    hora_inicio: str    
    hora_fim: str       
    organizador: str

def gerar_arquivo_ics(dados: DadosEvento) -> str:
    """Gera um arquivo .ics temporário com os detalhes do evento"""

    inicio = datetime.strptime(f"{dados.data} {dados.hora_inicio}", "%Y-%m-%d %H:%M")
    fim = datetime.strptime(f"{dados.data} {dados.hora_fim}", "%Y-%m-%d %H:%M")

    conteudo_ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Sistema de Reservas//Disparo de Evento//PT-BR
BEGIN:VEVENT
UID:{dados.email}-{inicio.strftime('%Y%m%dT%H%M%S')}
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{inicio.strftime('%Y%m%dT%H%M%S')}
DTEND:{fim.strftime('%Y%m%dT%H%M%S')}
SUMMARY:{dados.titulo}
DESCRIPTION:{dados.descricao}
LOCATION:{dados.local}
ORGANIZER;CN={dados.organizador}:MAILTO:{dados.email}
END:VEVENT
END:VCALENDAR
""".strip()

    arquivo_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".ics")
    with open(arquivo_temp.name, "w", encoding="utf-8") as f:
        f.write(conteudo_ics)

    return arquivo_temp.name

def enviar_email_com_anexo(dados: DadosEvento, caminho_ics: str):
    """Simula o envio de um e-mail com o arquivo .ics anexado"""

    remetente = "noreply@reserva-salas.com"
    destinatario = dados.email

    mensagem = MIMEMultipart("mixed")
    mensagem["From"] = remetente
    mensagem["To"] = destinatario
    mensagem["Subject"] = f"Convite de Calendário: {dados.titulo}"

    corpo_email = f"""
Olá {dados.organizador},

Segue o convite de calendário referente à sua reserva.

- Evento: {dados.titulo}
- Local: {dados.local}
- Data: {dados.data}
- Horário: {dados.hora_inicio} - {dados.hora_fim}

Um arquivo .ics foi anexado para adicionar o evento ao seu calendário.

Atenciosamente,
Equipe do Sistema de Reserva de Salas
"""

    mensagem.attach(MIMEText(corpo_email, "plain"))

    # Adiciona o arquivo .ics como anexo
    with open(caminho_ics, "rb") as arquivo:
        parte = MIMEBase("text", "calendar", method="REQUEST", name=os.path.basename(caminho_ics))
        parte.set_payload(arquivo.read())
        encoders.encode_base64(parte)
        parte.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(caminho_ics)}"
        )
        mensagem.attach(parte)

    print("=" * 60)
    print("SIMULAÇÃO DE ENVIO DE E-MAIL COM EVENTO (.ics)")
    print(f"De: {remetente}")
    print(f"Para: {destinatario}")
    print("-" * 60)
    print(corpo_email)
    print("-" * 60)
    print(f"Anexo gerado: {caminho_ics}")
    print("=" * 60)

@app.get("/", tags=["Health"])
def health_check():
    """Verifica se o serviço está online"""
    return {
        "status": "online",
        "servico": "Disparo de Evento",
        "descricao": "Gera e envia eventos de calendário (.ics) via e-mail",
        "porta": 8005,
        "endpoint_principal": "/enviar_evento"
    }

@app.post("/enviar_evento", tags=["Evento"])
def enviar_evento(dados: DadosEvento):
    """Recebe os dados da reserva, gera o arquivo .ics e simula o envio do e-mail"""
    try:
        caminho_ics = gerar_arquivo_ics(dados)
        enviar_email_com_anexo(dados, caminho_ics)
        os.remove(caminho_ics)

        return {
            "status": "sucesso",
            "mensagem": "Evento de calendário enviado com sucesso!",
            "destinatario": dados.email,
            "titulo": dados.titulo,
            "arquivo": ".ics"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar evento: {str(e)}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Serviço de Disparo de Evento (.ics)")
    print("="*60)
    print("Porta: 8005")
    print("Documentação: http://localhost:8005/docs")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8005)
