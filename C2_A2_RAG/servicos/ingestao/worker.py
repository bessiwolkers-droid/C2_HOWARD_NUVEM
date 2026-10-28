"""Worker Redis com fila de pendentes e reprocessamento idempotente de jobs."""
import json
import os
import time

import redis
import requests

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
URL_INGESTAO = os.getenv("URL_INGESTAO", "http://ingestao:8001")
FILA = "c2a2:ingestao:fila"
PENDENTES = "c2a2:ingestao:pendentes"
MAX_TENTATIVAS = 3


def recuperar_pendentes(cliente):
    """Devolve à fila os jobs capturados antes de uma interrupção do worker.

    O compose mantém somente um worker; não executar esta recuperação com vários
    workers em paralelo, pois poderia recuperar um job ainda em andamento.
    """
    total = 0
    while cliente.rpoplpush(PENDENTES, FILA) is not None:
        total += 1
    if total:
        print(f"Recuperados {total} jobs pendentes após reinício.", flush=True)


def processar_mensagem(cliente, mensagem):
    """Processa ou reencaminha um job; só remove de pendentes após resultado."""
    try:
        tarefa = json.loads(mensagem)
        job_id = tarefa["job_id"]
        documentos = tarefa["documentos"]
    except (ValueError, KeyError, TypeError) as exc:
        print(f"Mensagem inválida descartada: {exc}", flush=True)
        cliente.lrem(PENDENTES, 1, mensagem)
        return

    chave = f"c2a2:ingestao:job:{job_id}"
    cliente.hset(chave, mapping={"status": "processando"})
    try:
        resposta = requests.post(
            f"{URL_INGESTAO}/processar",
            json={"documentos": documentos, "job_id": job_id},
            timeout=30,
        )
        resposta.raise_for_status()
        resultado = resposta.json()
        indexados = int(resultado["indexados"])
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        tentativas = int(tarefa.get("tentativas", 0)) + 1
        if tentativas < MAX_TENTATIVAS:
            tarefa["tentativas"] = tentativas
            # Transação: uma falha entre remover e reenfileirar não perde a tarefa.
            with cliente.pipeline(transaction=True) as operacoes:
                operacoes.lrem(PENDENTES, 1, mensagem)
                operacoes.lpush(FILA, json.dumps(tarefa, ensure_ascii=False))
                operacoes.hset(chave, mapping={"status": "na_fila", "tentativas": str(tentativas)})
                operacoes.execute()
            print(f"Job {job_id}: falha transitória ({exc}); tentando novamente.", flush=True)
            time.sleep(1)
        else:
            with cliente.pipeline(transaction=True) as operacoes:
                operacoes.hset(chave, mapping={"status": "erro", "erro": str(exc)[:500]})
                operacoes.lrem(PENDENTES, 1, mensagem)
                operacoes.execute()
            print(f"Job {job_id} falhou após {tentativas} tentativas: {exc}", flush=True)
    else:
        with cliente.pipeline(transaction=True) as operacoes:
            operacoes.hset(chave, mapping={"status": "concluido", "indexados": str(indexados)})
            operacoes.lrem(PENDENTES, 1, mensagem)
            operacoes.execute()
        print(f"Job {job_id} concluído; índice com {indexados} documentos.", flush=True)


def executar():
    cliente = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=3)
    print(f"Worker ativo; aguardando mensagens em {FILA}.", flush=True)
    recuperados = False
    while True:
        try:
            if not recuperados:
                recuperar_pendentes(cliente)
                recuperados = True
            # BRPOPLPUSH: move para pendentes ANTES de processar.
            mensagem = cliente.brpoplpush(FILA, PENDENTES, timeout=5)
            if mensagem is not None:
                processar_mensagem(cliente, mensagem)
        except redis.RedisError as exc:
            recuperados = False
            print(f"Redis indisponível: {exc}; nova tentativa em 2s.", flush=True)
            time.sleep(2)


if __name__ == "__main__":
    executar()
