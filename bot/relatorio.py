"""Relatório semanal de vendas: puxa conversões da Shopee e grava em data/relatorios/.

Uso: python -m bot.relatorio [dias]   (padrão: 7)
"""
import collections
import json
import pathlib
import sys
import time
from datetime import datetime, timezone, timedelta

from bot.shopee import Shopee

RAIZ = pathlib.Path(__file__).resolve().parent.parent
BRT = timezone(timedelta(hours=-3))


def resumir(conversoes: list[dict]) -> dict:
    por_item = collections.defaultdict(lambda: {"nome": "", "pedidos": 0, "comissao": 0.0})
    por_hora = collections.Counter()
    por_canal = collections.Counter()
    total = 0.0
    for c in conversoes:
        com = float(c.get("totalCommission") or 0)
        total += com
        hora = datetime.fromtimestamp(int(c.get("clickTime") or c.get("purchaseTime") or 0), BRT).hour
        por_hora[hora] += 1
        por_canal[(c.get("utmContent") or "sem_subid").split("-")[0]] += com
        for pedido in c.get("orders") or []:
            for it in pedido.get("items") or []:
                k = str(it.get("itemId"))
                por_item[k]["nome"] = it.get("itemName", "")
                por_item[k]["pedidos"] += 1
                por_item[k]["comissao"] += float(it.get("itemTotalCommission") or 0)
    top = sorted(por_item.items(), key=lambda kv: kv[1]["comissao"], reverse=True)[:20]
    return {
        "conversoes": len(conversoes),
        "comissao_total": round(total, 2),
        "por_canal": {k: round(v, 2) for k, v in por_canal.items()},
        "por_hora_clique": dict(sorted(por_hora.items())),
        "top_produtos": [{"id": k, **v} for k, v in top],
    }


def main(dias=7):
    fim = int(time.time())
    inicio = fim - dias * 86400
    resumo = resumir(Shopee().conversoes(inicio, fim))
    resumo["periodo"] = [datetime.fromtimestamp(inicio, BRT).isoformat(), datetime.fromtimestamp(fim, BRT).isoformat()]
    pasta = RAIZ / "data" / "relatorios"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / f"{datetime.now(BRT):%Y-%m-%d}.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1))
    print(json.dumps(resumo, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 7)
