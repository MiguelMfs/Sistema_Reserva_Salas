from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Serviço de Consulta de Salas",
    description="Gerencia e disponibiliza dados das salas cadastradas",
    version="1.0.0"
)

# Lista simulada de salas
salas = [
    {"id": "LAB-01", "nome": "Laboratório 1", "capacidade": 30, "disponivel": True},
    {"id": "LAB-02", "nome": "Laboratório 2", "capacidade": 25, "disponivel": False},
    {"id": "SALA-01", "nome": "Sala de Aula 1", "capacidade": 40, "disponivel": True}
]


@app.get("/", tags=["Health"])
def health_check():
    """Verifica se o serviço está online"""
    return {"status": "online", "servico": "Consulta de Salas", "porta": 8001}


@app.get("/salas", tags=["Salas"])
def listar_salas():
    """Lista todas as salas"""
    return salas


@app.get("/salas/disponiveis", tags=["Salas"])
def listar_salas_disponiveis():
    """Lista apenas as salas disponíveis"""
    return [s for s in salas if s["disponivel"]]


@app.get("/salas/{sala_id}", tags=["Salas"])
def obter_sala_por_id(sala_id: str):
    """Retorna detalhes de uma sala específica"""
    for sala in salas:
        if sala["id"] == sala_id:
            return sala
    raise HTTPException(status_code=404, detail="Sala não encontrada")


# Inicialização local
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Serviço de Consulta de Salas rodando na porta 8001\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)
