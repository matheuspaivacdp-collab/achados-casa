"""Testes com dados simulados (sem internet)."""
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bot import main, selecao  # noqa: E402
from bot.relatorio import resumir  # noqa: E402
from bot.shopee import Shopee  # noqa: E402
from bot.telegram import legenda, brl  # noqa: E402


def no(i, **kw):
    base = {"itemId": i, "productName": f"Organizador de gaveta modelo {i}", "shopName": "Loja",
            "price": "39.90", "priceMin": "39.90", "priceDiscountRate": 40, "sales": 2500,
            "ratingStar": "4.8", "commissionRate": "0.08", "commission": "3.19",
            "imageUrl": f"https://img/{i}.jpg", "productLink": f"https://shopee.com.br/p/{i}",
            "offerLink": f"https://s.shopee.com.br/{i}"}
    base.update(kw)
    return base


class FakeShopee:
    def __init__(self):
        self.links = []

    def buscar(self, termo, limite=30, pagina=1):
        return [no(1), no(2, ratingStar="4.1"), no(3, productName="Suplemento melatonina"),
                no(4, priceMin="999"), no(5, sales=50), no(6, commissionRate="0.20"), no(1)]

    def link_curto(self, url, subs):
        self.links.append(subs)
        return url.replace("https://shopee.com.br/p/", "https://s.shopee.com.br/x")


class FakeTelegram:
    def __init__(self):
        self.posts = []

    def postar(self, o, link):
        self.posts.append((o["id"], link, legenda(o, link)))


def test_assinatura():
    s = Shopee("123", "abc")
    h = s._headers('{"q":1}')["Authorization"]
    ts = h.split("Timestamp=")[1].split(",")[0]
    esperado = hashlib.sha256(("123" + ts + '{"q":1}' + "abc").encode()).hexdigest()
    assert h.endswith("Signature=" + esperado)
    assert h.startswith("SHA256 Credential=123, Timestamp=")


def test_filtros_e_ranking():
    import yaml
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    ofertas = [selecao.normalizar(n) for n in FakeShopee().buscar("x")]
    esc = selecao.escolher(ofertas, cfg, {}, 10)
    ids = [o["id"] for o in esc]
    assert ids == ["6", "1"]  # 6 tem comissão maior; 2,3,4,5 filtrados; 1 sem duplicar
    assert esc[0]["preco_antigo"] == 66.5


def test_rodada_completa(tmp_path, monkeypatch):
    for nome in ["config.yaml"]:
        shutil.copy(ROOT / nome, tmp_path / nome)
    (tmp_path / "data").mkdir()
    (tmp_path / "docs").mkdir()
    monkeypatch.setattr(main, "RAIZ", tmp_path)
    monkeypatch.setattr(main, "HIST", tmp_path / "data/historico.json")
    monkeypatch.setattr(main, "POSTS", tmp_path / "data/posts.jsonl")
    monkeypatch.setattr(main, "VITRINE", tmp_path / "data/vitrine.json")
    monkeypatch.setattr(main.time, "sleep", lambda s: None)
    sh, tg = FakeShopee(), FakeTelegram()
    main.rodar(shopee=sh, telegram=tg)
    assert len(tg.posts) == 2
    assert "R$ 39,90" in tg.posts[0][2] or "R$ 39,90" in tg.posts[1][2]
    assert "Ver na Shopee" in (tmp_path / "docs/index.html").read_text()
    assert ["site"] in sh.links
    # segunda rodada não repete
    tg2 = FakeTelegram()
    main.rodar(shopee=FakeShopee(), telegram=tg2)
    assert tg2.posts == []


def test_relatorio():
    r = resumir([{"totalCommission": "5.5", "clickTime": 1763500000, "utmContent": "telegram-organizador",
                  "orders": [{"items": [{"itemId": 1, "itemName": "A", "itemTotalCommission": "5.5"}]}]}])
    assert r["comissao_total"] == 5.5 and r["por_canal"] == {"telegram": 5.5}
    assert r["top_produtos"][0]["pedidos"] == 1


def test_brl():
    assert brl(1234.5) == "R$ 1.234,50"
