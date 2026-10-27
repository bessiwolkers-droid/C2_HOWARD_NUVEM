# C2.A2 — checklist do núcleo obrigatório

- [x] **1. Persistir o índice** — `servicos/ingestao/app.py`: grava JSON atomicamente e o recarrega ao iniciar.
- [x] **2. Busca por similaridade** — `servicos/recuperacao/app.py`: vetoriza a pergunta, calcula similaridade cosseno e retorna `top_k` ordenado.
- [x] **3. Circuit breaker no LLM** — `servicos/geracao/app.py`: executa `gerar(...)` por `disjuntor.chamar(...)`, usa timeout e retentativas progressivas para falhas transitórias, e responde HTTP 503 com circuito aberto.
- [x] **4. Mensageria** — Redis List + `servicos/ingestao/worker.py`: a rota `/indexar` enfileira; worker consome e processa o lote.
- [x] **5. Fluxo completo** — `/perguntar` chama recuperação, usa o contexto e devolve resposta com documentos de apoio.
- [x] **6. README com diagrama** — `README.md` documenta serviços, fluxo, operação e configuração.

## Antes de entregar — verificação

- [x] A geração tem modo simulado quando a chave está ausente; o segredo é lido de variável de ambiente.
- [ ] Confirmar a operação após desligar a internet e subir novamente os serviços.
- [ ] Derrubar o serviço de recuperação e confirmar que o cliente recebe erro sem corromper estado.
- [ ] Induzir falhas do LLM e confirmar três falhas, circuito aberto e retorno HTTP 503.
- [ ] Executar `docker compose up --build` em um ambiente com Docker habilitado e concluir o fluxo documentado.

As caixas ainda vazias são validações manuais de ambiente. Elas não são marcadas como realizadas sem execução observável.
