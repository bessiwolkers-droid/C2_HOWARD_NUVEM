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
        trechos = r.json().get("resultados", [])
        contexto = [t["texto"] for t in trechos] if isinstance(trechos, list) else []
        fontes = list(dict.fromkeys(t.get("origem", "desconhecida") for t in trechos)) if contexto else []
    except (requests.RequestException, ValueError, KeyError) as exc:
        raise HTTPException(status_code=502, detail="Serviço de recuperação indisponível ou resposta inválida.") from exc
    if not contexto:
        return {
            "pergunta": p.pergunta,
            "resposta": "Não encontrei informações relevantes nos documentos para responder à pergunta.",
            "contexto": [], "fontes": [], "modo": "sem_contexto",
        }
    try:
        resposta = disjuntor.chamar(gerar, p.pergunta, contexto)
    except CircuitoAberto as exc:
        raise HTTPException(status_code=503, detail={
            "mensagem": "LLM temporariamente indisponível (circuit breaker aberto).",
            "contexto": contexto, "fontes": fontes,
        }) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail={
            "mensagem": "Falha ao consultar o LLM; trechos recuperados disponíveis para consulta.",
            "contexto": contexto, "fontes": fontes,
        }) from exc
    return {"pergunta": p.pergunta, "resposta": resposta, "contexto": contexto, "fontes": fontes}


@app.get("/saude")
def saude():
    return {"status": "ok", "disjuntor": disjuntor.estado}
