# Revisão do projeto C2.A2 — 27/10/2026

A estrutura original do repositório e os arquivos de `Aula_10_CAP` foram preservados.

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
