"""Gera o site estático de ofertas (GitHub Pages, pasta docs/)."""
import html
from datetime import datetime, timezone, timedelta

from bot.telegram import brl

BRT = timezone(timedelta(hours=-3))

MODELO = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo}</title>
<meta name="description" content="Achados úteis para casa, cozinha e organização com desconto. Atualizado todo dia.">
<style>
:root{{--bg:#faf7f2;--card:#fff;--ink:#2b2622;--muted:#7a716a;--accent:#e2572b}}
*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}}
header{{padding:28px 20px 12px;max-width:1100px;margin:auto}}
h1{{margin:0;font-size:28px}}header p{{color:var(--muted);margin:6px 0 0}}
.cta{{display:inline-block;margin-top:14px;background:#229ED9;color:#fff;padding:10px 16px;border-radius:999px;text-decoration:none;font-weight:600}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:16px;padding:16px 20px 40px;max-width:1100px;margin:auto}}
.card{{background:var(--card);border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);display:flex;flex-direction:column}}
.card img{{width:100%;aspect-ratio:1;object-fit:cover;background:#eee}}
.info{{padding:12px;display:flex;flex-direction:column;gap:6px;flex:1}}
.nome{{font-size:14px;line-height:1.3;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.preco{{font-size:20px;font-weight:700}}.antigo{{color:var(--muted);text-decoration:line-through;font-size:13px}}
.tag{{background:var(--accent);color:#fff;font-size:12px;padding:2px 6px;border-radius:6px;margin-left:6px}}
.meta{{color:var(--muted);font-size:12px}}
.btn{{margin-top:auto;text-align:center;background:var(--accent);color:#fff;padding:9px;border-radius:10px;text-decoration:none;font-weight:600}}
footer{{text-align:center;color:var(--muted);font-size:12px;padding:20px}}
</style></head><body>
<header><h1>{marca}</h1><p>Achados úteis pra casa, cozinha e organização. Atualizado em {quando}.</p>
<a class="cta" href="https://t.me/{canal}">Receber ofertas no Telegram</a></header>
<main>
{cards}
</main>
<footer>Links de afiliado: ao comprar por eles, ganhamos uma pequena comissão sem custo extra para você. Preços podem mudar.</footer>
</body></html>"""

CARD = """<article class="card"><img loading="lazy" src="{img}" alt="{nome}">
<div class="info"><div class="nome">{nome}</div>
<div>{antigo}<span class="preco">{preco}</span>{tag}</div>
<div class="meta">⭐ {nota} · {vendas} vendidos</div>
<a class="btn" href="{link}" rel="sponsored nofollow" target="_blank">Ver na Shopee</a></div></article>"""


def gerar(itens: list[dict], cfg: dict) -> str:
    cards = []
    for o in itens[: cfg["site"]["max_ofertas"]]:
        tem_desc = o.get("preco_antigo") and o["desconto"] >= 5
        cards.append(CARD.format(
            img=html.escape(o["imagem"]), nome=html.escape(o["nome"]),
            antigo=f'<span class="antigo">{brl(o["preco_antigo"])}</span><br>' if tem_desc else "",
            preco=brl(o["preco"]), tag=f'<span class="tag">-{int(o["desconto"])}%</span>' if tem_desc else "",
            nota=f'{o["nota"]:.1f}', vendas=f'{o["vendas"]:,}'.replace(",", "."),
            link=html.escape(o.get("link_site") or o["link_oferta"]),
        ))
    return MODELO.format(
        titulo=html.escape(cfg["marca"]["site_titulo"]), marca=html.escape(cfg["marca"]["nome"]),
        canal=cfg["marca"]["canal_telegram"].lstrip("@"),
        quando=datetime.now(BRT).strftime("%d/%m/%Y às %H:%M"), cards="\n".join(cards),
    )
