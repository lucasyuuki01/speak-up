"""Testes automáticos. Execute com:  python -m unittest discover -s tests -v"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import content  # noqa: E402
from app import app  # noqa: E402


class TesteConteudo(unittest.TestCase):
    def test_ids_unicos_e_campos_obrigatorios(self):
        ids = [p["id"] for p in content.PALAVRAS]
        self.assertEqual(len(ids), len(set(ids)))
        for p in content.PALAVRAS:
            for campo in ("en", "pt", "pron", "ex_en", "ex_pt", "visual", "alt"):
                self.assertTrue(p[campo], f"{p['id']} sem {campo}")

    def test_dez_modulos(self):
        self.assertEqual(len(content.MODULOS), 10)

    def test_alfabeto_completo(self):
        letras = [p["en"] for p in content.MODULO_POR_SLUG["alfabeto"]["palavras"]]
        self.assertEqual("".join(letras), "ABCDEFGHIJKLMNOPQRSTUVWXYZ")


class TestePaginas(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()

    def test_paginas_principais(self):
        for url in ["/", "/aulas", "/exercicios", "/progresso"] + [f"/modulo/{m['slug']}" for m in content.MODULOS]:
            r = self.c.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertIn("Speak Up", r.get_data(as_text=True), url)

    def test_erros_da_api_sao_json_e_amigaveis(self):
        r = self.c.get("/api/nao-existe")
        self.assertEqual(r.status_code, 404)
        self.assertIn("erro", r.get_json())
        r = self.c.get("/api/responder")  # método errado (deveria ser POST)
        self.assertEqual(r.status_code, 405)
        self.assertIn("erro", r.get_json())
        r = self.c.post("/")  # método errado numa página
        self.assertEqual(r.status_code, 405)
        self.assertIn("Algo deu errado", r.get_data(as_text=True))

    def test_404(self):
        self.assertEqual(self.c.get("/modulo/nao-existe").status_code, 404)
        self.assertEqual(self.c.get("/pagina-inexistente").status_code, 404)


class TesteApi(unittest.TestCase):
    def setUp(self):
        self.c = app.test_client()

    def exercicio(self, tipo, modulo, n=6):
        return self.c.get(f"/api/exercicio?tipo={tipo}&modulo={modulo}&n={n}")

    def test_perguntas_nao_revelam_resposta(self):
        d = self.exercicio("quiz", "animais").get_json()
        self.assertEqual(len(d["perguntas"]), 6)
        for q in d["perguntas"]:
            self.assertEqual(len(q["opcoes"]), 4)
            self.assertEqual(len({o["valor"] for o in q["opcoes"]}), 4)
            self.assertNotIn("correta", q)
            self.assertNotIn("resposta", q)

    def test_acerto_e_erro(self):
        d = self.exercicio("quiz", "animais").get_json()
        q = d["perguntas"][0]
        palavra = content.POR_ID[q["palavra_id"]]
        certo = self.c.post("/api/responder", json={"palavra_id": q["palavra_id"], "tipo": "quiz", "resposta": palavra["en"]}).get_json()
        self.assertTrue(certo["correto"])
        self.assertEqual(certo["pontos_ganhos"], 10)
        self.assertEqual(certo["resumo"]["pontos"], 10)
        errado = self.c.post("/api/responder", json={"palavra_id": q["palavra_id"], "tipo": "quiz", "resposta": "xyz"}).get_json()
        self.assertFalse(errado["correto"])
        self.assertEqual(errado["pontos_ganhos"], 0)
        self.assertEqual(errado["resumo"]["pontos"], 10)  # errar não tira pontos

    def test_segunda_tentativa_nao_pontua(self):
        pid = "animais-dog"
        r = self.c.post("/api/responder", json={"palavra_id": pid, "tipo": "associacao", "resposta": "dog", "tentativa": 2}).get_json()
        self.assertTrue(r["correto"])
        self.assertEqual(r["pontos_ganhos"], 0)

    def test_modo_som_do_alfabeto(self):
        d = self.exercicio("quiz", "alfabeto").get_json()
        q = d["perguntas"][0]
        palavra = content.POR_ID[q["palavra_id"]]
        self.assertIn(palavra["pron"], [o["valor"] for o in q["opcoes"]])
        r = self.c.post("/api/responder", json={"palavra_id": q["palavra_id"], "tipo": "quiz", "resposta": palavra["pron"]}).get_json()
        self.assertTrue(r["correto"])

    def test_traducoes(self):
        r = self.c.post("/api/responder", json={"palavra_id": "animais-dog", "tipo": "traducao", "resposta": "cachorro"}).get_json()
        self.assertTrue(r["correto"])
        r = self.c.post("/api/responder", json={"palavra_id": "animais-dog", "tipo": "traducao_inversa", "resposta": "dog"}).get_json()
        self.assertTrue(r["correto"])

    def test_progresso_persiste_na_sessao_e_reinicia(self):
        self.c.post("/api/responder", json={"palavra_id": "animais-cat", "tipo": "quiz", "resposta": "cat"})
        p = self.c.get("/api/progresso").get_json()
        self.assertEqual(p["pontos"], 10)
        self.assertEqual(p["palavras_sabidas"], 1)
        self.assertEqual(p["modulos"]["animais"]["sabidas"], 1)
        self.assertIn(">10<", self.c.get("/progresso").get_data(as_text=True).replace(" ", "").replace("\n", ""))
        p = self.c.post("/api/reiniciar").get_json()
        self.assertEqual(p["pontos"], 0)
        self.assertEqual(p["palavras_sabidas"], 0)

    def test_modulo_concluido(self):
        for w in content.MODULO_POR_SLUG["animais"]["palavras"]:
            self.c.post("/api/carta", json={"palavra_id": w["id"], "sabia": True})
        p = self.c.get("/api/progresso").get_json()
        self.assertTrue(p["modulos"]["animais"]["concluido"])
        self.assertEqual(p["modulos_concluidos"], 1)

    def test_revisao(self):
        r = self.exercicio("revisao", "todos")
        self.assertEqual(r.status_code, 400)  # nada estudado ainda
        self.c.post("/api/responder", json={"palavra_id": "animais-dog", "tipo": "quiz", "resposta": "errado"})
        self.c.post("/api/responder", json={"palavra_id": "frutas-alimentos-apple", "tipo": "quiz", "resposta": "apple"})
        d = self.exercicio("revisao", "todos").get_json()
        self.assertEqual(len(d["perguntas"]), 2)

    def test_associacao_e_flashcards(self):
        d = self.exercicio("associacao", "objetos").get_json()
        self.assertEqual(len(d["itens"]), 4)
        self.assertEqual(len(d["palavras"]), 4)
        d = self.exercicio("flashcards", "familia-pessoas").get_json()
        self.assertEqual(len(d["cartas"]), 10)
        self.assertTrue(any(c["frente"] == "ingles" for c in d["cartas"]))  # mother/father... só texto

    def test_so_texto_fora_do_quiz_de_imagens(self):
        so_texto = {p["id"] for p in content.PALAVRAS if p.get("so_texto")}
        for _ in range(10):
            d = self.exercicio("quiz", "familia-pessoas", 10).get_json()
            for q in d["perguntas"]:
                self.assertNotIn(q["palavra_id"], so_texto)

    def test_validacoes(self):
        self.assertEqual(self.exercicio("quiz", "inexistente").status_code, 400)
        self.assertEqual(self.exercicio("quiz", "todos").status_code, 400)
        self.assertEqual(self.exercicio("quiz", "saudacoes").status_code, 400)  # módulo só de frases
        self.assertEqual(self.exercicio("foo", "animais").status_code, 400)
        self.assertEqual(self.c.get("/api/exercicio?tipo=quiz&modulo=animais&n=abc").status_code, 400)
        post = self.c.post
        self.assertEqual(post("/api/responder", data="não é json").status_code, 400)
        self.assertEqual(post("/api/responder", json={"palavra_id": "x", "tipo": "quiz", "resposta": "a"}).status_code, 400)
        self.assertEqual(post("/api/responder", json={"palavra_id": "animais-dog", "tipo": "quiz", "resposta": ""}).status_code, 400)
        self.assertEqual(post("/api/responder", json={"palavra_id": "animais-dog", "tipo": "quiz", "resposta": 5}).status_code, 400)
        self.assertEqual(post("/api/responder", json={"palavra_id": "animais-dog", "tipo": "xyz", "resposta": "dog"}).status_code, 400)
        self.assertEqual(post("/api/responder", json={"palavra_id": "animais-dog", "tipo": "quiz", "resposta": "a" * 500}).status_code, 400)
        self.assertEqual(post("/api/carta", json={"palavra_id": "animais-dog", "sabia": "sim"}).status_code, 400)

    def test_todas_as_perguntas_de_todos_os_modulos(self):
        """Gera exercícios de cada tipo em cada módulo e confere se a resposta certa está entre as opções."""
        for m in content.MODULOS:
            for tipo in m["exercicios"]:
                if tipo == "revisao":
                    continue
                for _ in range(5):
                    d = self.exercicio(tipo, m["slug"], 10).get_json()
                    if tipo == "flashcards":
                        self.assertEqual(len(d["cartas"]), len(m["palavras"]))
                    elif tipo == "associacao":
                        self.assertEqual(len({i["palavra_id"] for i in d["itens"]}), 4)
                    else:
                        for q in d["perguntas"]:
                            self.assertEqual(len(q["opcoes"]), 4, (m["slug"], tipo))
                            import logic
                            certa = logic.resposta_correta(content.POR_ID[q["palavra_id"]], q["tipo"])
                            self.assertIn(certa, [o["valor"] for o in q["opcoes"]])


class TestePonteEBuild(unittest.TestCase):
    """Versão que roda no navegador (Pyodide): ponte.py e build_static.py."""

    def test_ponte_fluxo_completo(self):
        import json
        import ponte
        d = json.loads(ponte.exercicio("", "quiz", "animais", "6", "{}"))
        self.assertIsNone(d["erro"])
        q = d["dados"]["perguntas"][0]
        palavra = content.POR_ID[q["palavra_id"]]
        corpo = json.dumps({"palavra_id": q["palavra_id"], "tipo": "quiz", "resposta": palavra["en"]})
        r = json.loads(ponte.responder("", corpo))
        self.assertTrue(r["dados"]["correto"])
        self.assertEqual(r["resumo"]["pontos"], 10)
        estado = json.dumps(r["estado"])  # o navegador guarda e devolve este texto
        r2 = json.loads(ponte.responder(estado, corpo))
        self.assertEqual(r2["resumo"]["pontos"], 20)
        r3 = json.loads(ponte.carta(estado, json.dumps({"palavra_id": "animais-cat", "sabia": True})))
        self.assertEqual(r3["resumo"]["palavras_sabidas"], 2)
        zerado = json.loads(ponte.reiniciar(estado))
        self.assertEqual(zerado["resumo"]["pontos"], 0)

    def test_ponte_entradas_invalidas(self):
        import json
        import ponte
        self.assertIsNotNone(json.loads(ponte.exercicio("", "quiz", "animais", "abc"))["erro"])
        self.assertIsNotNone(json.loads(ponte.exercicio("", "quiz", "nao-existe", "6"))["erro"])
        self.assertIsNotNone(json.loads(ponte.responder("", "não é json"))["erro"])
        self.assertIsNotNone(json.loads(ponte.carta("", json.dumps({"palavra_id": "animais-dog", "sabia": "sim"})))["erro"])
        # estado salvo corrompido não quebra nada
        self.assertIsNone(json.loads(ponte.exercicio("{lixo", "quiz", "animais", "6"))["erro"])
        corrompido = '{"pts": "x", "ok": "y", "fr": [999, -1, "a", true], "resp": null, "ac": 1.5}'
        d = json.loads(ponte.exercicio(corrompido, "quiz", "animais", "6"))
        self.assertIsNone(d["erro"])
        self.assertEqual(d["resumo"]["pontos"], 0)
        self.assertEqual(d["resumo"]["palavras_sabidas"], 0)
        self.assertEqual(d["resumo"]["para_revisar"], 0)

    def test_build_estatico(self):
        import re
        import tempfile
        from pathlib import Path
        import build_static
        with tempfile.TemporaryDirectory() as tmp:
            saida = build_static.construir(Path(tmp) / "docs")
            for arquivo in ["index.html", "aulas.html", "exercicios.html", "progresso.html", ".nojekyll", "imagens.json",
                            "python/content.py", "python/logic.py", "python/ponte.py", "static/js/script.js",
                            "static/css/style.css", "static/images/logo.png"]:
                self.assertTrue((saida / arquivo).exists(), arquivo)
            self.assertEqual(len(list(saida.glob("modulo-*.html"))), 10)
            for html in saida.glob("*.html"):
                texto = html.read_text(encoding="utf-8")
                self.assertIn("SPEAKUP_ESTATICO = true", texto, html.name)
                self.assertIsNone(re.search(r'(href|src)="/(?!/)', texto), html.name)  # sem endereços absolutos
        self.assertFalse(build_static.app.config.get("ESTATICO"))  # o Flask volta ao modo normal

    def test_destino(self):
        import build_static
        self.assertEqual(build_static.destino("/exercicios?modulo=animais&tipo=quiz"), "exercicios.html?modulo=animais&tipo=quiz")
        self.assertEqual(build_static.destino("/modulo/corpo"), "modulo-corpo.html")
        with self.assertRaises(ValueError):
            build_static.destino("/rota-desconhecida")


if __name__ == "__main__":
    unittest.main()
