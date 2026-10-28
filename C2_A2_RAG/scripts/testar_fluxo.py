"""Teste de integração real dos três serviços e do worker com Redis.

Com Docker Compose em execução, rode:
    docker compose exec geracao python scripts/testar_fluxo.py
"""
import os
import time
import uuid

import requests

URL_INGESTAO = os.getenv("URL_INGESTAO", "http://ingestao:8001")
URL_RECUPERACAO = os.getenv("URL_RECUPERACAO", "http://recuperacao:8002")
URL_GERACAO = os.getenv("URL_GERACAO", "http://geracao:8003")


def main():
    origem = "teste-integracao-" + uuid.uuid4().hex[:8]
    documentos = [
        {"texto": "O teorema CAP envolve consistência, disponibilidade e tolerância a partições.", "origem": origem},
        {"texto": "O protocolo Raft utiliza um líder para coordenar um log replicado.", "origem": "teste-raft"},
    ]
    inicio = requests.post(f"{URL_INGESTAO}/indexar", json={"documentos": documentos}, timeout=10)
    inicio.raise_for_status()
    job_id = inicio.json()["job_id"]
    print(f"Indexação enfileirada: {job_id}")

    limite = time.monotonic() + 60
    while time.monotonic() < limite:
        estado = requests.get(f"{URL_INGESTAO}/indexar/{job_id}", timeout=5)
        estado.raise_for_status()
        status = estado.json()["status"]
        if status == "concluido":
            break
        if status == "erro":
            raise RuntimeError(f"Indexação falhou: {estado.json()}")
        time.sleep(1)
    else:
        raise TimeoutError("Worker não concluiu a indexação em 60s")
    print("Indexação concluída")

    pergunta = "O que o teorema CAP aborda?"
    busca = requests.post(f"{URL_RECUPERACAO}/buscar", json={"pergunta": pergunta, "top_k": 3}, timeout=10)
    busca.raise_for_status()
    assert any(t["origem"] == origem for t in busca.json()["resultados"]), "Documento novo não foi recuperado"
    print("Recuperação de documento confirmada")

    geracao = requests.post(f"{URL_GERACAO}/perguntar", json={"pergunta": pergunta}, timeout=35)
    geracao.raise_for_status()
    resposta = geracao.json()
    assert resposta["resposta"], "Resposta de geração vazia"
    assert origem in resposta["fontes"], "Fonte esperada não citada"
    print("Geração concluída e fontes confirmadas:")
    print(resposta)
    print("TESTE INTEGRADO: OK")


if __name__ == "__main__":
    main()
