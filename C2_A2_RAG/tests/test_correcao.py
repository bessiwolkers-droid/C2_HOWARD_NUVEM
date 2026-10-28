"""Casos adicionais para verificar as correções críticas."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from servicos.ingestao import app as ingestao
from servicos.ingestao import worker
from servicos.recuperacao import app as recuperacao
from servicos.geracao import app as geracao
from servicos.comum.circuit_breaker import CircuitBreaker


class TestIndexacaoIdempotente(unittest.TestCase):
    def test_mesmo_job_nao_duplica_apos_recarregar(self):
        with tempfile.TemporaryDirectory() as pasta:
            anterior_path, anterior_indice = ingestao.INDICE_PATH, ingestao.INDICE
            try:
                ingestao.INDICE_PATH = Path(pasta) / "indice.json"
                ingestao.INDICE = []
                lote = ingestao.LoteDocumentos(
                    job_id="teste-123",
                    documentos=[ingestao.Documento(texto="consistência e tolerância a partições", origem="cap")],
                )
                self.assertEqual(ingestao.processar(lote)["indexados"], 1)
                ingestao.INDICE = []
                ingestao._carregar()
                self.assertTrue(ingestao.processar(lote)["reprocessado"])
                self.assertEqual(len(ingestao.INDICE), 1)
            finally:
                ingestao.INDICE_PATH, ingestao.INDICE = anterior_path, anterior_indice


class TestBuscaRelevancia(unittest.TestCase):
    def test_texto_sem_similaridade_nao_retorna_contexto(self):
        retorno = type("Resposta", (), {
            "json": lambda self: {"itens": [{"texto": "lua estrelas planetas", "origem": "astronomia"}]},
            "raise_for_status": lambda self: None,
        })()
        with patch.object(recuperacao.requests, "get", return_value=retorno):
            result = recuperacao.buscar(recuperacao.Consulta(pergunta="consistência disponibilidade"))
        self.assertEqual(result["resultados"], [])


class TestGeracaoSegura(unittest.TestCase):
    def test_sem_contexto_nao_chama_llm(self):
        retorno = type("Resposta", (), {
            "json": lambda self: {"resultados": []},
            "raise_for_status": lambda self: None,
        })()
        with patch.object(geracao.requests, "post", return_value=retorno), patch.object(geracao, "gerar") as gerar:
            resposta = geracao.perguntar(geracao.Pergunta(pergunta="Pergunta sem documentos"))
        self.assertEqual(resposta["modo"], "sem_contexto")
        self.assertEqual(resposta["fontes"], [])
        gerar.assert_not_called()

    def test_falha_llm_conserva_contexto_no_erro(self):
        retorno = type("Resposta", (), {
            "json": lambda self: {"resultados": [{"texto": "contexto recuperado", "origem": "livro"}]},
            "raise_for_status": lambda self: None,
        })()
        with patch.object(geracao.requests, "post", return_value=retorno), patch.object(geracao, "gerar", side_effect=RuntimeError("fora")):
            with self.assertRaises(HTTPException) as erro:
                geracao.perguntar(geracao.Pergunta(pergunta="Exemplo"))
        self.assertEqual(erro.exception.status_code, 502)
        self.assertEqual(erro.exception.detail["fontes"], ["livro"])


class TestWorker(unittest.TestCase):
    def test_restitui_tarefas_pendentes_a_fila(self):
        cliente = MagicMock()
        cliente.rpoplpush.side_effect = ["job-1", "job-2", None]
        worker.recuperar_pendentes(cliente)
        self.assertEqual(cliente.rpoplpush.call_count, 3)
        cliente.rpoplpush.assert_any_call(worker.PENDENTES, worker.FILA)

    def test_erro_transitorio_reenfileira_sem_perder_mensagem(self):
        cliente = MagicMock()
        mensagem = '{"job_id": "j123", "documentos": [{"texto": "texto", "origem": "x"}]}'
        with patch.object(worker.requests, "post", side_effect=worker.requests.Timeout()), patch.object(worker.time, "sleep"):
            worker.processar_mensagem(cliente, mensagem)
        pipeline = cliente.pipeline.return_value.__enter__.return_value
        pipeline.lrem.assert_called_once_with(worker.PENDENTES, 1, mensagem)
        self.assertEqual(pipeline.lpush.call_count, 1)
        pipeline.execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
