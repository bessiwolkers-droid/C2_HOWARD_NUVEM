# Aula 10 — Replicação, consistência e teorema CAP

## Objetivo

Este laboratório demonstra por que sistemas distribuídos mantêm réplicas, como uma partição de rede pode deixá-las divergentes e por que, durante essa falha, é preciso priorizar consistência (CP) ou disponibilidade (AP). A simulação foi feita em Python puro, sem dependências externas.

## Arquivos da atividade

- `replicas_sim.py` — simulação com quatro cenários, incluindo escrita extra durante a partição e política AP/CP por tipo de dado.
- `saida_experimento.txt` — saída completa obtida ao executar a simulação.
- `PROMPTS.md` — registro do uso de fontes e assistência por IA.

## Experimento e divergência

Com a rede funcionando, a escrita `preco=10` foi replicada de A para B e ambas ficaram na versão v1. Durante a partição, A recebeu `preco=20` na versão v2, mas B não recebeu a atualização. A saída identifica esse primeiro desencontro como `MOMENTO DA DIVERGENCIA: A=v2 B=v1`. Uma segunda escrita, `preco=30`, levou A à versão v3, enquanto B permaneceu em v1: naquele ponto, A estava duas versões à frente e as leituras retornavam valores diferentes.

Ao curar a rede, a simulação reconcilia B com A. B passa a guardar `preco=30` na versão v3, e as réplicas voltam a concordar. Isso representa consistência eventual: as cópias podem divergir durante uma falha, mas convergem após a comunicação ser restabelecida e a reconciliação ocorrer.

## Decisão CAP por tipo de dado

A função `ler_por_tipo()` define CP para `saldo` e `estoque`, pois uma leitura desatualizada pode levar a decisões financeiras ou operacionais incorretas. Durante a partição, a leitura de saldo retorna 503 em vez de apresentar um valor potencialmente antigo. Nesse caso, prioriza-se consistência e sacrifica-se disponibilidade temporariamente.

Para `curtidas` e `catalogo`, a política escolhida é AP. Uma quantidade de curtidas ou uma listagem de catálogo ligeiramente desatualizada costuma ser aceitável, enquanto continuar respondendo pode ser mais útil. Durante a partição, a leitura AP devolve o valor de B e sinaliza que está desatualizado. Essa decisão depende das regras do produto: catálogo de medicamentos, por exemplo, pode exigir controles mais fortes do que um catálogo de conteúdo.

## Índice vetorial do C2.A2

Para uma busca RAG comum, eu escolheria AP para a leitura do índice vetorial: manter a busca disponível mesmo que uma réplica esteja temporariamente atrasada tende a ser preferível a recusar toda consulta. Nesse arranjo, uma consulta pode não encontrar imediatamente um documento recém-indexado; a atualização deve convergir entre réplicas depois que a comunicação voltar.

Essa escolha pressupõe que a resposta possa tolerar algum atraso de indexação. Se a consulta exigir que uma informação recém-publicada ou removida seja refletida imediatamente — por exemplo, por requisito de segurança, conformidade ou controle de acesso — a leitura do índice e/ou a validação da resposta precisa de um caminho com garantias mais fortes, possivelmente CP. O CAP não torna AP ou CP universalmente melhor: a política depende do impacto de ler dado antigo e do custo de indisponibilidade.

## Execução

Na pasta `Aula_10_CAP`, execute:

```bash
python3 replicas_sim.py
```

A saída reproduzida e conferida está em `saida_experimento.txt`. A simulação implementa as quatro missões do guia: replicação normal, partição com escritas adicionais e divergência explícita, escolha CAP por tipo de dado e reconciliação após a cura.

## C2.A2

Este repositório C2 contém somente o README inicial além desta atividade; não havia implementação do serviço de recuperação/RAG para validar ou alterar neste trabalho. Portanto, este relatório registra a decisão projetual para um índice vetorial hipoteticamente replicado, mas não afirma que o serviço do C2.A2 foi iniciado ou testado.

## Referências

- [Aula 10 — Replicação, consistência e o teorema CAP](https://howardroatti.github.io/sistemas-distribuidos-faesa/aulas/aula-10-replicacao-consistencia-cap.html)
- [Guia do Laboratório — Aula 10 · CAP](https://howardroatti.github.io/sistemas-distribuidos-faesa/aulas/lab-10-missoes.html)
- [Repositório da disciplina](https://github.com/howardroatti/sd-2026-2-kit-c1a2)
