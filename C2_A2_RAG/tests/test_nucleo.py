import os
import tempfile
import unittest
from unittest.mock import patch


from servicos.comum.circuit_breaker import CircuitBreaker, CircuitoAberto
from servicos.ingestao import app as ingestao
from servicos.recuperacao import app as recuperacao
from servicos.geracao import app as geracao
from fastapi import HTTPException


class TestBusca(unittest.TestCase):
    def test_top_k_em_ordem_de_similaridade(self):
        dados = {
            "itens": [
                {"texto": "O teorema CAP explica consistência e disponibilidade.", "origem": "cap"},
                {"texto": "Raft coordena consenso entre servidores distribuídos.", "origem": "raft"},
            ]
        }
        resposta = type("Resposta", (), {"json": lambda self: dados, "raise_for_status": lambda self: None})()
        with patch.object(recuperacao.requests, "get", return_value=resposta):
            resultado = recuperacao.buscar(recuperacao.Consulta(pergunta="teorema CAP consistência", top_k=1))
        self.assertEqual(len(resultado["resultados"]), 1)
        self.assertEqual(resultado["resultados"][0]["origem"], "cap")
        self.assertGreater(resultado["resultados"][0]["similaridade"], 0)

    def test_indice_vazio_retorna_lista(self):
        resposta = type("Resposta", (), {"json": lambda self: {"itens": []}, "raise_for_status": lambda self: None})()
        with patch.object(recuperacao.requests, "get", return_value=resposta):
            resultado = recuperacao.buscar(recuperacao.Consulta(pergunta="qualquer coisa"))
        self.assertEqual(resultado["resultados"], [])


class TestPersistencia(unittest.TestCase):
    def test_grava_e_recarrega_indice(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "indice.json")
            anterior = ingestao.INDICE_PATH
            try:
                ingestao.INDICE_PATH = __import__("pathlib").Path(caminho)
                ingestao.INDICE.clear()
                lote = ingestao.LoteDocumentos(documentos=[
                    ingestao.Documento(texto="consistência eventual entre réplicas", origem="cap")
                ])
                resultado = ingestao.processar(lote)
                self.assertEqual(resultado["indexados"], 1)
                self.assertTrue(os.path.exists(caminho))
                ingestao.INDICE.clear()
                ingestao._carregar()
                self.assertEqual(ingestao.INDICE[0]["origem"], "cap")
                self.assertTrue(ingestao.INDICE[0]["vetor"])
            finally:
                ingestao.INDICE.clear()
                ingestao.INDICE_PATH = anterior


class TestCircuitBreaker(unittest.TestCase):
    def test_abre_apos_limite_de_falhas(self):
        disjuntor = CircuitBreaker(limite_falhas=3, espera_segundos=60)
        def falhar():
            raise RuntimeError("LLM fora do ar")
        for _ in range(3):
            with self.assertRaises(RuntimeError):
                disjuntor.chamar(falhar)
        self.assertEqual(disjuntor.estado, "aberto")
        with self.assertRaises(CircuitoAberto):
            disjuntor.chamar(lambda: "nao deveria executar")


if __name__ == "__main__":
    unittest.main()


class TestApiGeracao(unittest.TestCase):
    def test_disjuntor_aberto_responde_503(self):
        anterior = geracao.disjuntor
        try:
            geracao.disjuntor = CircuitBreaker(limite_falhas=1, espera_segundos=60)
            with self.assertRaises(RuntimeError):
                geracao.disjuntor.chamar(lambda: (_ for _ in ()).throw(RuntimeError("falha simulada")))
            resposta = type("Resposta", (), {
                "json": lambda self: {"resultados": [{"texto": "contexto de teste"}]},
                "raise_for_status": lambda self: None,
            })()
            with patch.object(geracao.requests, "post", return_value=resposta):
                with self.assertRaises(HTTPException) as erro:
                    geracao.perguntar(geracao.Pergunta(pergunta="pergunta de teste"))
            self.assertEqual(erro.exception.status_code, 503)
        finally:
            geracao.disjuntor = anterior
