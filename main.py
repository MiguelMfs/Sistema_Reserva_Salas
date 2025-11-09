"""
Gateway de Orquestração - Sistema de Reserva de Salas
Porta: 8010
Autor: Rodrigo
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import requests
from typing import Optional
import logging

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Instância FastAPI
app = FastAPI(
    title="Gateway - Sistema de Reserva de Salas",
    description="Orquestrador central para reserva de salas em microsserviços",
    version="1.0.0"
)

# URLs dos microsserviços
SERVICO_CONSULTA_SALA = "http://localhost:8001"
SERVICO_VERIFICAR_DISPONIBILIDADE = "http://localhost:8002"
SERVICO_RESERVAR_SALA = "http://localhost:8003"
SERVICO_DISPARO_EMAIL = "http://localhost:8004"
SERVICO_DISPARO_EVENTO = "http://localhost:8005"

# Modelos Pydantic
class ReservaRequest(BaseModel):
    """Modelo de requisição para reserva de sala"""
    sala_id: str = Field(..., description="ID da sala (ex: LAB-01)")
    data: str = Field(..., description="Data da reserva (YYYY-MM-DD)")
    hora_inicio: str = Field(..., description="Hora de início (HH:MM)")
    hora_fim: str = Field(..., description="Hora de término (HH:MM)")
    usuario_nome: str = Field(..., description="Nome do usuário")
    usuario_email: EmailStr = Field(..., description="Email do usuário")

    class Config:
        json_schema_extra = {
            "example": {
                "sala_id": "LAB-01",
                "data": "2025-11-10",
                "hora_inicio": "19:00",
                "hora_fim": "21:00",
                "usuario_nome": "João Silva",
                "usuario_email": "joao@example.com"
            }
        }


class ReservaResponse(BaseModel):
    """Modelo de resposta de reserva bem-sucedida"""
    status: str
    mensagem: str
    reserva: dict


class ErroResponse(BaseModel):
    """Modelo de resposta de erro"""
    status: str
    mensagem: str
    detalhe: Optional[str] = None


# Funções auxiliares para chamar microsserviços

def consultar_sala(sala_id: str) -> dict:
    """
    Chama o microsserviço de Consulta de Sala
    Porta: 8001
    Endpoint: GET /salas/{id}
    """
    try:
        logger.info(f"[1/5] Consultando sala {sala_id}...")
        url = f"{SERVICO_CONSULTA_SALA}/salas/{sala_id}"
        response = requests.get(url, timeout=5)

        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Sala '{sala_id}' não encontrada"
            )

        response.raise_for_status()
        sala = response.json()
        logger.info(f"✓ Sala encontrada: {sala.get('nome', sala_id)}")
        return sala

    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Erro ao consultar sala: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Serviço de Consulta de Sala indisponível: {str(e)}"
        )


def verificar_disponibilidade(sala_id: str, data: str, hora_inicio: str, hora_fim: str) -> dict:
    """
    Chama o microsserviço de Verificar Disponibilidade
    Porta: 8002
    Endpoint: POST /verificar
    """
    try:
        logger.info(f"[2/5] Verificando disponibilidade da sala {sala_id} em {data} {hora_inicio}-{hora_fim}...")
        url = f"{SERVICO_VERIFICAR_DISPONIBILIDADE}/verificar"
        payload = {
            "sala_id": sala_id,
            "data": data,
            "hora_inicio": hora_inicio,
            "hora_fim": hora_fim
        }

        response = requests.post(url, json=payload, timeout=5)

        if response.status_code == 409:
            resultado = response.json()
            raise HTTPException(
                status_code=409,
                detail=f"Sala não disponível: {resultado.get('mensagem', 'Conflito de horário')}"
            )

        response.raise_for_status()
        resultado = response.json()

        if not resultado.get('disponivel', False):
            raise HTTPException(
                status_code=409,
                detail=f"Sala não disponível no horário solicitado: {resultado.get('detalhe', '')}"
            )

        logger.info("✓ Sala disponível")
        return resultado

    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Erro ao verificar disponibilidade: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Serviço de Verificação de Disponibilidade indisponível: {str(e)}"
        )


def reservar_sala(reserva_data: ReservaRequest) -> dict:
    """
    Chama o microsserviço de Reservar Sala
    Porta: 8003
    Endpoint: POST /reservar
    """
    try:
        logger.info(f"[3/5] Registrando reserva da sala {reserva_data.sala_id}...")
        url = f"{SERVICO_RESERVAR_SALA}/reservar"
        payload = {
            "sala_id": reserva_data.sala_id,
            "data": reserva_data.data,
            "hora_inicio": reserva_data.hora_inicio,
            "hora_fim": reserva_data.hora_fim,
            "usuario_nome": reserva_data.usuario_nome,
            "usuario_email": reserva_data.usuario_email
        }

        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        resultado = response.json()

        logger.info(f"✓ Reserva registrada com ID: {resultado.get('reserva_id', 'N/A')}")
        return resultado

    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Erro ao reservar sala: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Serviço de Reserva de Sala indisponível: {str(e)}"
        )


def enviar_email(reserva_data: ReservaRequest, sala_info: dict) -> dict:
    """
    Chama o microsserviço de Disparo de Email
    Porta: 8004
    Endpoint: POST /email
    """
    try:
        logger.info(f"[4/5] Enviando email de confirmação para {reserva_data.usuario_email}...")
        url = f"{SERVICO_DISPARO_EMAIL}/email"
        payload = {
            "destinatario": reserva_data.usuario_email,
            "assunto": f"Confirmação de Reserva - Sala {reserva_data.sala_id}",
            "corpo": f"""
Olá {reserva_data.usuario_nome},

Sua reserva foi confirmada com sucesso!

Detalhes da Reserva:
- Sala: {sala_info.get('nome', reserva_data.sala_id)}
- Data: {reserva_data.data}
- Horário: {reserva_data.hora_inicio} - {reserva_data.hora_fim}

Atenciosamente,
Sistema de Reserva de Salas
            """.strip(),
            "sala_id": reserva_data.sala_id,
            "data": reserva_data.data,
            "horario": f"{reserva_data.hora_inicio} - {reserva_data.hora_fim}"
        }

        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        resultado = response.json()

        logger.info("✓ Email enviado com sucesso")
        return resultado

    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠ Erro ao enviar email (não crítico): {str(e)}")
        # Email não é crítico, retorna sucesso parcial
        return {"enviado": False, "erro": str(e)}


def enviar_evento_calendario(reserva_data: ReservaRequest, sala_info: dict) -> dict:
    """
    Chama o microsserviço de Disparo de Evento
    Porta: 8005
    Endpoint: POST /enviar_evento
    """
    try:
        logger.info(f"[5/5] Gerando evento de calendário (.ics)...")
        url = f"{SERVICO_DISPARO_EVENTO}/enviar_evento"
        payload = {
            "email": reserva_data.usuario_email,
            "titulo": f"Reserva de Sala - {reserva_data.sala_id}",
            "descricao": f"Reserva da sala {sala_info.get('nome', reserva_data.sala_id)}",
            "local": sala_info.get('localizacao', reserva_data.sala_id),
            "data": reserva_data.data,
            "hora_inicio": reserva_data.hora_inicio,
            "hora_fim": reserva_data.hora_fim,
            "organizador": reserva_data.usuario_nome
        }

        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        resultado = response.json()

        logger.info("✓ Evento de calendário enviado")
        return resultado

    except requests.exceptions.RequestException as e:
        logger.warning(f"⚠ Erro ao enviar evento (não crítico): {str(e)}")
        # Evento não é crítico, retorna sucesso parcial
        return {"enviado": False, "erro": str(e)}


# Rotas da API

@app.get("/", tags=["Health"])
def health_check():
    """
    Endpoint de health check do gateway
    """
    return {
        "status": "online",
        "servico": "Gateway - Sistema de Reserva de Salas",
        "versao": "1.0.0",
        "porta": 8010
    }


@app.post("/reservar", response_model=ReservaResponse, tags=["Reservas"])
def orquestrar_reserva(reserva: ReservaRequest):
    """
    Orquestra o processo completo de reserva de sala

    Fluxo:
    1. Consulta informações da sala (8001)
    2. Verifica disponibilidade (8002)
    3. Registra a reserva (8003)
    4. Envia email de confirmação (8004)
    5. Envia evento de calendário (8005)

    Retorna confirmação consolidada ou erro detalhado
    """
    logger.info("="*60)
    logger.info(f"Nova requisição de reserva recebida: {reserva.sala_id}")
    logger.info("="*60)

    try:
        # Etapa 1: Consultar sala
        sala_info = consultar_sala(reserva.sala_id)

        # Etapa 2: Verificar disponibilidade
        disponibilidade = verificar_disponibilidade(
            reserva.sala_id,
            reserva.data,
            reserva.hora_inicio,
            reserva.hora_fim
        )

        # Etapa 3: Reservar sala
        resultado_reserva = reservar_sala(reserva)

        # Etapa 4: Enviar email (não crítico)
        resultado_email = enviar_email(reserva, sala_info)
        email_enviado = resultado_email.get("enviado", True)

        # Etapa 5: Enviar evento de calendário (não crítico)
        resultado_evento = enviar_evento_calendario(reserva, sala_info)
        evento_enviado = resultado_evento.get("enviado", True)

        # Resposta consolidada
        logger.info("="*60)
        logger.info("✓ RESERVA CONCLUÍDA COM SUCESSO")
        logger.info("="*60)

        return {
            "status": "sucesso",
            "mensagem": "Reserva confirmada",
            "reserva": {
                "reserva_id": resultado_reserva.get("reserva_id"),
                "sala_id": reserva.sala_id,
                "sala_nome": sala_info.get("nome", reserva.sala_id),
                "usuario": reserva.usuario_nome,
                "data": reserva.data,
                "horario": f"{reserva.hora_inicio} - {reserva.hora_fim}",
                "email_enviado": email_enviado,
                "evento_calendario_enviado": evento_enviado
            }
        }

    except HTTPException as e:
        logger.error("="*60)
        logger.error(f"✗ FALHA NA RESERVA: {e.detail}")
        logger.error("="*60)
        raise

    except Exception as e:
        logger.error("="*60)
        logger.error(f"✗ ERRO INESPERADO: {str(e)}")
        logger.error("="*60)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno no gateway: {str(e)}"
        )


@app.get("/status", tags=["Health"])
def verificar_status_servicos():
    """
    Verifica o status de todos os microsserviços conectados
    """
    servicos = {
        "Consulta de Sala (8001)": SERVICO_CONSULTA_SALA,
        "Verificar Disponibilidade (8002)": SERVICO_VERIFICAR_DISPONIBILIDADE,
        "Reservar Sala (8003)": SERVICO_RESERVAR_SALA,
        "Disparo de Email (8004)": SERVICO_DISPARO_EMAIL,
        "Disparo de Evento (8005)": SERVICO_DISPARO_EVENTO
    }

    status_geral = {}

    for nome, url in servicos.items():
        try:
            response = requests.get(f"{url}/", timeout=2)
            status_geral[nome] = {
                "status": "online" if response.status_code == 200 else "degradado",
                "codigo": response.status_code
            }
        except Exception as e:
            status_geral[nome] = {
                "status": "offline",
                "erro": str(e)
            }

    return {
        "gateway": "online",
        "servicos": status_geral
    }


# Inicialização
if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("🚀 Gateway - Sistema de Reserva de Salas")
    print("="*60)
    print("Porta: 8010")
    print("Documentação: http://localhost:8010/docs")
    print("Status: http://localhost:8010/status")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8010)
