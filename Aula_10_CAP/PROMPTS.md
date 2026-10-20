# Registro de fontes e assistência — Aula 10 CAP

## Missão 1 — replicação e leitura das réplicas
- Fonte: guia do laboratório do professor e repositório oficial da disciplina; assistência de IA generativa.
- O que perguntei: "Observe o repositório do professor e o meu repositório anterior. Agora estamos na C2: leia a aula e realize o laboratório da Aula 10 no repositório C2_HOWARD_NUVEM, mantendo o padrão de nomes das atividades."
- Resposta (resumo): O guia pede uma simulação de duas réplicas, uma escrita replicada quando a rede está disponível e leitura do valor atualizado. O script oficial foi usado como referência para preservar os conceitos e o formato básico do experimento.
- O que foi feito com isso: O código foi organizado em `replicas_sim.py` dentro de `Aula_10_CAP`. A simulação foi executada e sua saída foi guardada em `saida_experimento.txt`.

## Missão 2 — provocar partição e registrar divergência
- Fonte: guia do laboratório e assistência de IA generativa.
- O que perguntei: o mesmo pedido acima; em seguida, pedi a preparação da atividade em arquivos do repositório seguindo o guia da aula.
- Resposta (resumo): Durante a partição, uma escrita pode chegar a A e não chegar a B; o guia pede uma escrita adicional, comparação das leituras e registro do instante da primeira divergência.
- O que foi feito com isso: Foram acrescentadas duas escritas durante a partição. A saída registrada mostra a primeira divergência em `A=v2 B=v1`, a leitura de `preco=30` em A contra `preco=10` em B e A duas versões à frente.

## Missão 3 — escolha AP/CP por tipo de dado
- Fonte: aula e guia do professor; assistência de IA generativa.
- O que perguntei: o mesmo pedido acima.
- Resposta (resumo): A decisão CAP sob partição depende do custo de indisponibilidade e do risco de responder com dado desatualizado. O guia sugere CP para saldo/estoque e AP para curtidas/catálogo.
- O que foi feito com isso: A função `ler_por_tipo()` aplica CP a saldo e estoque e AP a curtidas e catálogo. A execução demonstra saldo recusado com 503 e curtidas respondendo com aviso de dado desatualizado.

## Missão 4 — relatório e decisão sobre o índice vetorial
- Fonte: aula e guia do professor; assistência de IA generativa.
- O que perguntei: o mesmo pedido acima.
- Resposta (resumo): Para uma busca RAG genérica, AP pode manter consultas disponíveis com eventual atraso de indexação. Situações em que dado recente ou removido precisa ser refletido imediatamente podem exigir garantias mais fortes.
- O que foi feito com isso: A decisão e suas premissas foram documentadas em `Relatorio_CAP.md`. O repositório C2 continha apenas o README inicial; por isso, o serviço do C2.A2 não foi declarado como implementado nem testado.
