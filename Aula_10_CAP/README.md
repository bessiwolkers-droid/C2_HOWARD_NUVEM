# Aula 10 — Replicação, consistência e teorema CAP

**Disciplina:** Sistemas Distribuídos e Computação em Nuvem · FAESA · 2026/2
**Unidade:** C2 · Coordenação e consistência
**Atividade:** Laboratório CAP — quatro missões

## Conteúdo

- [`replicas_sim.py`](replicas_sim.py) — simula replicação, partição, divergência, políticas AP/CP e reconciliação.
- [`saida_experimento.txt`](saida_experimento.txt) — saída gerada pela execução da simulação.
- [`Relatorio_CAP.md`](Relatorio_CAP.md) — análise do experimento, decisões CAP por tipo de dado e política proposta para índice vetorial.
- [`PROMPTS.md`](PROMPTS.md) — registro de fontes e apoios conforme o guia do laboratório.

## Execução

Requer Python 3.12 ou compatível; não utiliza bibliotecas externas.

```bash
python3 replicas_sim.py
```

## Entregáveis

O relatório registra o primeiro instante de divergência (`A=v2`, `B=v1`), a diferença de versões após uma escrita adicional, exemplos de decisão CP e AP e a política escolhida para busca em um índice vetorial replicado.

## Referências

- [Aula 10 — Replicação, consistência e o teorema CAP](https://howardroatti.github.io/sistemas-distribuidos-faesa/aulas/aula-10-replicacao-consistencia-cap.html)
- [Guia do Laboratório — Aula 10](https://howardroatti.github.io/sistemas-distribuidos-faesa/aulas/lab-10-missoes.html)
