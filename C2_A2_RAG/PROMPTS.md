# Registro de fontes e apoio — C2.A2

## Desenvolvimento do núcleo obrigatório
- Fonte: kit C2.A2 e TAREFAS.md do professor; guia do laboratório da Aula 10; apoio de ferramenta de IA generativa.
- Solicitação: implementar no repositório do grupo as tarefas obrigatórias do kit C2.A2, mantendo as entregas anteriores, documentando a arquitetura e validando o fluxo dos serviços.
- Síntese do apoio: decompor o trabalho em persistência do índice, recuperação por similaridade, proteção da chamada ao LLM, fila com worker, fluxo de pergunta ponta a ponta e documentação reproduzível. O guia da Aula 10 também solicita registrar a escolha AP/CP para um índice vetorial replicado.
- Aplicação e entendimento: a equipe deve revisar e explicar as decisões no código. O índice usa JSON local com reindexação dos vetores na inicialização; a busca ordena os documentos por similaridade cosseno; a ingestão publica tarefas em uma fila Redis consumida por worker; a chamada ao LLM é protegida por circuit breaker; e a busca RAG usa modo AP como escolha de disponibilidade, aceitando atraso de indexação conforme descrito no README.

## Validação
- Fontes: testes automatizados em `tests/test_nucleo.py` e execução local dos serviços com Redis.
- Resultado registrado: testes de persistência, busca e circuit breaker passaram; o fluxo de enfileiramento, indexação, recuperação e resposta simulada foi exercitado localmente. A execução via Docker Compose e o corte real de internet ainda precisam ser confirmados em ambiente com Docker/rede controlada.
