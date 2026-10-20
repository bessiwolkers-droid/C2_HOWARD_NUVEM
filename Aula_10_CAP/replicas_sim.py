#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aula 10 — Replicação, consistência e o teorema CAP.

Simula duas réplicas em Python puro. Durante a partição, demonstra a
escolha entre disponibilidade (AP) e consistência (CP) e aplica uma
regra de negócio de acordo com o tipo do dado.
"""


class Replica:
    """Uma cópia do dado, identificada por nome, valor e versão."""

    def __init__(self, nome):
        self.nome = nome
        self.valor = None
        self.versao = 0

    def aplicar(self, valor, versao):
        self.valor = valor
        self.versao = versao


class Cluster:
    def __init__(self):
        self.A = Replica("A")
        self.B = Replica("B")
        self.particionado = False
        self.versao_global = 0
        self.divergiu_em = None

    def escrever(self, valor):
        self.versao_global += 1
        versao = self.versao_global
        self.A.aplicar(valor, versao)
        print(f'    A <- "{valor}" (v{versao})')
        if not self.particionado:
            self.B.aplicar(valor, versao)
            print(f'    B <- "{valor}" (v{versao})   [replicado]')
        else:
            print(f'    B  x  NAO recebe (particao) - continua em v{self.B.versao}')
            if self.divergiu_em is None:
                self.divergiu_em = versao
                print(
                    f'    >>> MOMENTO DA DIVERGENCIA: '
                    f'A=v{versao}  B=v{self.B.versao} <<<'
                )

    def ler_de_B(self, modo="AP"):
        desatualizada = self.B.versao < self.versao_global
        if self.particionado and desatualizada:
            if modo == "CP":
                return "503 INDISPONIVEL (CP: prioriza Consistencia)"
            return (
                f'"{self.B.valor}" (v{self.B.versao}) '
                "DESATUALIZADO (AP: prioriza Disponibilidade)"
            )
        return f'"{self.B.valor}" (v{self.B.versao})'

    def particionar(self):
        self.particionado = True
        print("    ## rede PARTICIONADA: A e B nao se falam ##")

    def curar(self):
        self.particionado = False
        self.B.aplicar(self.A.valor, self.A.versao)
        self.divergiu_em = None
        print(
            f'    ## rede CURADA: B reconcilia -> '
            f'"{self.B.valor}" (v{self.B.versao}) ##'
        )


def ler_por_tipo(cluster, dado):
    """Escolhe CP para dados críticos e AP para dados tolerantes a atraso."""
    modos = {
        "saldo": "CP",
        "estoque": "CP",
        "curtidas": "AP",
        "catalogo": "AP",
    }
    modo = modos.get(dado)
    if modo is None:
        raise ValueError(f"Tipo de dado sem política configurada: {dado}")
    resposta = cluster.ler_de_B(modo=modo)
    print(f"    leitura de {dado} ({modo}): {resposta}")
    return resposta


def titulo(texto):
    print("\n" + texto)
    print("-" * len(texto))


if __name__ == "__main__":
    cluster = Cluster()

    titulo("Cenario 1 - rede OK: replicacao e consistencia eventual")
    cluster.escrever("preco=10")
    print(f"    leitura em B: {cluster.ler_de_B()}")
    print("    => A e B concordam (consistencia alcancada).")

    titulo("Cenario 2 - PARTICAO: escritas e divergencia")
    cluster.particionar()
    cluster.escrever("preco=20")
    cluster.escrever("preco=30")
    print(f"    leitura em A: \"{cluster.A.valor}\" (v{cluster.A.versao})")
    print(f"    leitura em B: \"{cluster.B.valor}\" (v{cluster.B.versao})")
    diferenca_versoes = cluster.A.versao - cluster.B.versao
    print(f"    A ficou {diferenca_versoes} versao(oes) a frente de B.")

    titulo("Cenario 3 - politica CAP por tipo de dado sob a mesma particao")
    print(f"    leitura AP explicita: {cluster.ler_de_B(modo='AP')}")
    print(f"    leitura CP explicita: {cluster.ler_de_B(modo='CP')}")
    ler_por_tipo(cluster, "saldo")
    ler_por_tipo(cluster, "curtidas")
    print("    => saldo prioriza consistencia; curtidas priorizam disponibilidade.")

    titulo("Cenario 4 - cura da particao: reconciliacao")
    cluster.curar()
    print(f"    leitura em B: {cluster.ler_de_B()}")
    print("    => passada a particao, as replicas voltam a concordar.")

    print(
        f"\nResumo: a divergencia comecou na versao v{cluster.divergiu_em or 2}; "
        "durante a particao, a escolha e entre C e A."
    )
