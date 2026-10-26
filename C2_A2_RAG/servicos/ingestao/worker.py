"""Worker que consome a fila Redis e solicita ao serviço a persistência dos documentos."""
import json
import os
import time

import redis
import requests

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
URL_INGESTAO = os.getenv("URL_INGESTAO", "http://ingestao:8001")
FILA = "c2a2:ingestao:fila"


def executar():
    cliente = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    print(f"Worker ativo; aguardando mensagens em {FILA}.", flush=True)
    while True:
        try:
            mensagem = cliente.brpop(FILA, timeout=5)
            if mensagem is None:
                continue
            tarefa = json.loads(mensagem[1])
            job_id = tarefa["job_id"]
            chave = f"c2a2:ingestao:job:{job_id}"
            cliente.hset(chave, mapping={"status": "processando"})
            try:
                resposta = requests.post(
                    f"{URL_INGESTAO}/processar",
                    json={"documentos": tarefa["documentos"]}, timeout=30,
                )
                resposta.raise_for_status()
                resultado = resposta.json()
                cliente.hset(chave, mapping={"status": "concluido", "indexados": resultado["indexados"]})
                print(f"Job {job_id} concluído; índice com {resultado['indexados']} documentos.", flush=True)
            except (requests.RequestException, ValueError, KeyError) as exc:
                cliente.hset(chave, mapping={"status": "erro", "erro": str(exc)[:500]})
                print(f"Falha no job {job_id}: {exc}", flush=True)
        except redis.RedisError as exc:
            print(f"Redis indisponível: {exc}; nova tentativa em 2s.", flush=True)
            time.sleep(2)


if __name__ == "__main__":
    executar()
