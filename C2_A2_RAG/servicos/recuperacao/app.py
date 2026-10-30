"""Servico de recuperacao: busca trechos similares a uma pergunta."""
import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from servicos.comum.embeddings import similaridade

app = FastAPI(title="Recuperacao - C2.A2")
URL_INGESTAO = os.getenv("URL_INGESTAO", "http://localhost:8001")


class Consulta(BaseModel):
    pergunta: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)


@app.post("/buscar")
def buscar(consulta: Consulta):
    try:
        resposta = requests.get(f"{URL_INGESTAO}/indice", timeout=5)
        resposta.raise_for_status()
        itens = resposta.json().get("itens", [])
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Serviço de ingestão indisponível ou resposta inválida.") from exc
    if not itens:
        return {"pergunta": consulta.pergunta, "resultados": []}

    textos = [str(item.get("texto", "")) for item in itens]
    vetorizador = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    matriz = vetorizador.fit_transform(textos + [consulta.pergunta])
    vetor_pergunta = matriz[-1].toarray()[0].tolist()
    resultados = []
    for item, vetor_documento in zip(itens, matriz[:-1]):
        # O vetor gravado pela ingestão não é usado aqui e só incharia a resposta.
        registro = {chave: valor for chave, valor in item.items() if chave != "vetor"}
        registro["similaridade"] = similaridade(vetor_pergunta, vetor_documento.toarray()[0].tolist())
        resultados.append(registro)
    # Documentos sem qualquer semelhança lexical não devem fundamentar respostas.
    resultados = [item for item in resultados if item["similaridade"] > 0]
    resultados.sort(key=lambda item: item["similaridade"], reverse=True)
    return {"pergunta": consulta.pergunta, "resultados": resultados[:consulta.top_k]}


@app.get("/saude")
def saude():
    return {"status": "ok"}
