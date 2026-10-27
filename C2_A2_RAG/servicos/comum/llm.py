"""
Cliente de LLM - PRONTO, com modo simulado para funcionar offline.

Se a variavel de ambiente LLM_API_KEY existir, chama a API real.
Se NAO existir, entra em MODO SIMULADO e monta uma resposta a partir do
contexto recuperado. Assim o kit funciona no laboratorio sem internet.

IMPORTANTE: nunca escreva a chave no codigo. Use variavel de ambiente.
"""
import os
import time

import requests

API_KEY = os.getenv("LLM_API_KEY", "")
API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
MODELO = os.getenv("LLM_MODELO", "gpt-4o-mini")
TIMEOUT = float(os.getenv("LLM_TIMEOUT", "20"))
MAX_TENTATIVAS = max(1, int(os.getenv("LLM_MAX_TENTATIVAS", "3")))
ESPERA_RETENTATIVA = max(0.0, float(os.getenv("LLM_ESPERA_RETENTATIVA", "0.5")))


def _simulado(pergunta, contexto):
    trechos = " ".join(contexto)[:600]
    return (
        "[MODO SIMULADO - sem LLM_API_KEY configurada]\n"
        f"Pergunta: {pergunta}\n"
        f"Com base nos documentos recuperados: {trechos}"
    )


def gerar(pergunta: str, contexto: list) -> str:
    """Monta o prompt com o contexto recuperado e chama o LLM."""
    if not API_KEY:
        return _simulado(pergunta, contexto)

    prompt = (
        "Responda a pergunta usando SOMENTE o contexto abaixo. "
        "Se a resposta nao estiver no contexto, diga que nao sabe.\n\n"
        f"Contexto:\n{chr(10).join(contexto)}\n\nPergunta: {pergunta}"
    )
    payload = {
        "model": MODELO,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    ultima_falha = None
    for tentativa in range(MAX_TENTATIVAS):
        try:
            resposta = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                json=payload,
                timeout=TIMEOUT,
            )
            resposta.raise_for_status()
            return resposta.json()["choices"][0]["message"]["content"]
        except (requests.Timeout, requests.ConnectionError) as exc:
            ultima_falha = exc
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status != 429 and (status is None or status < 500):
                raise
            ultima_falha = exc

        if tentativa + 1 < MAX_TENTATIVAS:
            time.sleep(ESPERA_RETENTATIVA * (2 ** tentativa))

    raise ultima_falha
