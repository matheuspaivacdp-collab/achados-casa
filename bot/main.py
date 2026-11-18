"""Rodada da máquina: busca ofertas, escolhe as melhores, posta no Telegram e atualiza o site.

Uso:
  python -m bot.main            # rodada normal
  python -m bot.main --teste    # busca e escolhe, mas não posta nem grava nada
"""
import json
import pathlib
import sys
import time
import unicodedata

import yaml

from bot.selecao import escolher, normalizar
from bot.shopee import Shopee
from bot import site

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HIST = RAIZ / "data" / "historico.json"
POSTS = RAIZ / "data" / "posts.jsonl"
VITRINE = RAIZ / "data" / "vitrine.json"


def ler_json(p, padrao):
    return json.loads(p.read_text()) if p.exists() else padrao


def coletar(shopee, cfg) -> list[dict]:
    ofertas = []
    for termo in cfg["buscas"]:
        try:
            for no in shopee.buscar(termo, cfg["resultados_por_busca"]):
                o = normalizar(no)
                o["busca"] = termo
                ofertas.append(o)
        except Exception as e:  # uma busca falhar não derruba a rodada
            print(f"[aviso] busca '{termo}' falhou: {e}")
        time.sleep(0.5)
    return ofertas


def rodar(teste=False, shopee=None, telegram=None):
    cfg = yaml.safe_load((RAIZ / "config.yaml").read_text())
    shopee = shopee or Shopee()
    historico = ler_json(HIST, {})

    ofertas = coletar(shopee, cfg)
    print(f"{len(ofertas)} ofertas coletadas")
    if not ofertas:
        raise SystemExit("Nenhuma oferta veio da Shopee. Verifique as credenciais.")

    escolhidas = escolher(ofertas, cfg, historico, cfg["postagem"]["ofertas_por_rodada"])
    print(f"{len(escolhidas)} escolhidas:")
    for o in escolhidas:
        print(f"  {o['score']:>6} | R$ {o['preco']:>7.2f} | {o['comissao']*100:.0f}% | {o['nome'][:70]}")

    if teste:
        return escolhidas

    if telegram is None:
        from bot.telegram import Telegram
        telegram = Telegram()

    agora = int(time.time())
    vitrine = ler_json(VITRINE, [])
    postados = 0
    for o in escolhidas:
        try:
            sub = unicodedata.normalize("NFKD", o["busca"]).encode("ascii", "ignore").decode()
            sub = "".join(c for c in sub if c.isalnum())[:30]
            link_tg = shopee.link_curto(o["link_produto"], ["telegram", sub])
            o["link_site"] = shopee.link_curto(o["link_produto"], ["site"])
            telegram.postar(o, link_tg)
        except Exception as e:
            print(f"[erro] não postou {o['id']}: {e}")
            continue
        postados += 1
        historico[o["id"]] = agora
        with POSTS.open("a") as f:
            f.write(json.dumps({"ts": agora, "id": o["id"], "nome": o["nome"], "preco": o["preco"],
                                "comissao": o["comissao"], "busca": o["busca"], "score": o["score"]},
                               ensure_ascii=False) + "\n")
        vitrine = [o] + [v for v in vitrine if v["id"] != o["id"]]

    vitrine = vitrine[: cfg["site"]["max_ofertas"]]
    HIST.write_text(json.dumps(historico, indent=0))
    VITRINE.write_text(json.dumps(vitrine, ensure_ascii=False, indent=1))
    (RAIZ / "docs" / "index.html").write_text(site.gerar(vitrine, cfg))
    print(f"{postados} ofertas postadas")
    if escolhidas and postados == 0:
        raise SystemExit("Nenhuma oferta foi postada. Veja os erros acima.")


if __name__ == "__main__":
    rodar(teste="--teste" in sys.argv)
