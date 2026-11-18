"""Publicação no canal do Telegram via Bot API."""
import html
import os
import random

import requests

ABERTURAS = [
    "🏠 ACHADO PRA CASA",
    "🔥 PREÇO BOM HOJE",
    "✨ VALE A PENA",
    "🛒 OLHA ESSE",
    "💡 RESOLVE O PROBLEMA",
]


def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def legenda(o: dict, link: str) -> str:
    nome = html.escape(o["nome"][:110])
    linhas = [f"<b>{random.choice(ABERTURAS)}</b>", "", nome, ""]
    if o.get("preco_antigo") and o["desconto"] >= 5:
        linhas.append(f"<s>{brl(o['preco_antigo'])}</s> ➜ <b>{brl(o['preco'])}</b> (-{int(o['desconto'])}%)")
    else:
        linhas.append(f"💰 <b>{brl(o['preco'])}</b>")
    linhas.append(f"⭐ {o['nota']:.1f} · {o['vendas']:,} vendidos".replace(",", "."))
    linhas += ["", f"👉 {link}", "", "<i>Preço pode mudar a qualquer momento.</i>"]
    return "\n".join(linhas)


class Telegram:
    def __init__(self, token=None, chat_id=None, session=None):
        self.token = token or os.environ.get("TELEGRAM_TOKEN", "")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
        if not self.token or not self.chat_id:
            raise RuntimeError("Faltam TELEGRAM_TOKEN e TELEGRAM_CHAT_ID nos Secrets do GitHub.")
        self.http = session or requests.Session()

    def postar(self, o: dict, link: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        r = self.http.post(url, timeout=30, data={
            "chat_id": self.chat_id,
            "photo": o["imagem"],
            "caption": legenda(o, link),
            "parse_mode": "HTML",
            "reply_markup": '{"inline_keyboard":[[{"text":"🛒 Ver na Shopee","url":"%s"}]]}' % link,
        })
        if not r.ok:
            raise RuntimeError(f"Telegram recusou: {r.status_code} {r.text[:200]}")
