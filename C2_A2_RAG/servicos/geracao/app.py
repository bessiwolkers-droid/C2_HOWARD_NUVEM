"""Servico de geracao: recupera contexto e chama o LLM protegido pelo disjuntor."""
import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from servicos.comum.circuit_breaker import CircuitBreaker, CircuitoAberto
from servicos.comum.llm import gerar

app = FastAPI(title="Geracao - C2.A2")
URL_RECUPERACAO = os.getenv("URL_RECUPERACAO", "http://localhost:8002")
disjuntor = CircuitBreaker(limite_falhas=3, espera_segundos=20)


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=1)


@app.post("/perguntar")
def perguntar(p: Pergunta):
    try:
        r = requests.post(
            f"{URL_RECUPERACAO}/buscar",
            json={"pergunta": p.pergunta, "top_k": 3}, timeout=8,
        )
        r.raise_for_status()
        contexto = [t["texto"] for t in r.json().get("resultados", [])]
    except (requests.RequestException, ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail="Serviço de recuperação indisponível ou resposta inválida.") from exc
    try:
        resposta = disjuntor.chamar(gerar, p.pergunta, contexto)
    except CircuitoAberto as exc:
        raise HTTPException(status_code=503, detail="Serviço de geração temporariamente indisponível (circuit breaker aberto).") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Falha ao consultar o serviço de geração.") from exc
    return {"pergunta": p.pergunta, "resposta": resposta, "contexto": contexto}


@app.get("/saude")
def saude():
    return {"status": "ok", "disjuntor": disjuntor.estado}
