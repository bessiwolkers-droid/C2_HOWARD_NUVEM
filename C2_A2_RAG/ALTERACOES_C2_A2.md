# Revisão do projeto C2.A2 — 27/10/2026

A estrutura original do projeto C2.A2 foi preservada.

## Correções aplicadas

1. **Ingestão (`servicos/ingestao/app.py`)**: `job_id` opcional nos lotes, identificação de jobs já persistidos, serialização das alterações de índice e reversão em caso de falha na persistência.
2. **Worker (`servicos/ingestao/worker.py`)**: fila Redis de pendentes (`BRPOPLPUSH`), recuperação após reinício com um único worker, reencaminhamento com transação e máximo de três tentativas.
3. **Recuperação (`servicos/recuperacao/app.py`)**: descarta resultados com similaridade igual a zero.
4. **Geração (`servicos/geracao/app.py`)**: responde adequadamente sem contexto, informa fontes dos trechos e mantém fontes/contexto no corpo de erros do LLM (HTTP 502/503).
5. **Docker e testes**: Dockerfile agora inclui `tests/` e `scripts/`; Compose aguarda serviços saudáveis e inclui serviço de testes sob profile `test`.
6. **Documentação**: README revisto com instruções para Windows, roteiro integrado e limites das garantias.

## Verificação realizada neste ambiente

- Todos os arquivos `.py` passaram por `compileall`.
- `docker-compose.yml` passou por parsing YAML.
- **12 testes unitários passaram**, incluindo testes de reentrega simulada do worker, persistência idempotente, busca, contexto e resiliência.
- Para os testes Python locais, a interface da biblioteca Redis foi substituída por um stub isolado, pois o pacote `redis` não está instalado no ambiente de validação. Nos contêineres Docker a dependência é instalada pelo `requirements.txt`.
- **Não foi possível iniciar Docker Compose, Redis real ou chamar um LLM real** neste ambiente. Esse teste precisa ser feito na máquina de entrega.

## Revisão de 29/10/2026

- **Recuperação**: `/buscar` deixou de devolver o campo `vetor` de cada documento (vinha do índice da ingestão, não era usado e aumentava a resposta). Teste adicionado.
- **Testes**: o `if __name__ == "__main__"` de `tests/test_nucleo.py` foi movido para o fim do arquivo; antes, ao rodar o arquivo diretamente, as classes declaradas depois dele não executavam.
- **13 testes unitários passaram** (`python -m unittest discover -s tests`).
- **Fluxo integrado executado sem Docker**: os três serviços e o worker rodando com `uvicorn`, usando um servidor Redis simulado (`fakeredis`) na porta TCP. `scripts/testar_fluxo.py` terminou com `TESTE INTEGRADO: OK`.
- **Falhas induzidas** no mesmo ambiente:
  - LLM apontado para uma porta fechada: três respostas HTTP 502 com contexto e fontes, quarta resposta HTTP 503 e `/saude` da geração mostrando `"disjuntor": "aberto"`.
  - Serviço de recuperação derrubado: `/perguntar` responde HTTP 502 e a ingestão continua com o mesmo número de documentos.
- Continua pendente a execução via Docker Compose com Redis real.

## Comandos recomendados para validação final

Execute na pasta `C2_A2_RAG` com Docker Desktop aberto:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
docker compose --profile test run --build --rm testes
docker compose exec geracao python scripts/testar_fluxo.py
```

A execução integrada deve terminar com `TESTE INTEGRADO: OK`.
