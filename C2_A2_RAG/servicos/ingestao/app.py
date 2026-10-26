"""Servico de ingestao: fila tarefas de indexacao e persiste o indice vetorial."""
import json
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import redis

from servicos.comum.embeddings import Vetorizador

app = FastAPI(title="Ingestao - C2.A2")
INDICE_PATH = Path(os.getenv("INDICE_PATH", "/app/dados/indice.json"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FILA_INDEXACAO = "c2a2:ingestao:fila"
vetorizador = Vetorizador()
INDICE = []


class Documento(BaseModel):
    texto: str = Field(min_length=1)
    origem: str = "desconhecida"


class LoteDocumentos(BaseModel):
    documentos: list[Documento]


def _vetorizar_indice():
    if not INDICE:
        return
    vetorizador.ajustar([item["texto"] for item in INDICE])
    for item in INDICE:
        item["vetor"] = vetorizador.vetorizar(item["texto"])


def _persistir():
    INDICE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temporario = tempfile.mkstemp(prefix="indice-", suffix=".json", dir=INDICE_PATH.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
            json.dump(INDICE, arquivo, ensure_ascii=False)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, INDICE_PATH)
    finally:
        if os.path.exists(temporario):
            os.unlink(temporario)


def _carregar():
    global INDICE
    if INDICE_PATH.exists():
        conteudo = json.loads(INDICE_PATH.read_text(encoding="utf-8"))
        if not isinstance(conteudo, list):
            raise RuntimeError("O arquivo do índice deve conter uma lista.")
        INDICE = [
            {"texto": str(item["texto"]), "origem": str(item.get("origem", "desconhecida"))}
            for item in conteudo
        ]
        _vetorizar_indice()


@app.on_event("startup")
def carregar_indice():
    _carregar()


@app.post("/indexar", status_code=202)
def indexar(lote: LoteDocumentos):
    """Publica a indexação na fila; o worker processa o job."""
    if not lote.documentos:
        raise HTTPException(status_code=400, detail="Envie ao menos um documento.")
    job_id = os.urandom(16).hex()
    chave = f"c2a2:ingestao:job:{job_id}"
    tarefa = {"job_id": job_id, "documentos": [d.model_dump() for d in lote.documentos]}
    try:
        cliente = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        cliente.ping()
        cliente.hset(chave, mapping={"status": "na_fila", "indexados": "0"})
        cliente.expire(chave, 86400)
        cliente.lpush(FILA_INDEXACAO, json.dumps(tarefa, ensure_ascii=False))
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail="Fila de indexação indisponível.") from exc
    return {"job_id": job_id, "status": "na_fila"}


@app.get("/indexar/{job_id}")
def status_indexacao(job_id: str):
    cliente = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
    try:
        estado = cliente.hgetall(f"c2a2:ingestao:job:{job_id}")
    except redis.RedisError as exc:
        raise HTTPException(status_code=503, detail="Fila de indexação indisponível.") from exc
    if not estado:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada ou expirada.")
    resultado = {"job_id": job_id, **estado}
    resultado["indexados"] = int(resultado.get("indexados", 0))
    return resultado


@app.post("/processar", include_in_schema=False)
def processar(lote: LoteDocumentos):
    """Endpoint interno chamado pelo worker para aplicar um lote."""
    if not lote.documentos:
        raise HTTPException(status_code=400, detail="Lote vazio.")
    INDICE.extend(d.model_dump() for d in lote.documentos)
    _vetorizar_indice()
    _persistir()
    return {"indexados": len(INDICE)}


@app.get("/indice")
def indice():
    return {"total": len(INDICE), "itens": INDICE}


@app.get("/saude")
def saude():
    return {"status": "ok", "documentos": len(INDICE), "persistencia": str(INDICE_PATH)}
