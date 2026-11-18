"""Filtra e ranqueia ofertas."""
import math
import time


def _f(v, padrao=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return padrao


def normalizar(no: dict) -> dict:
    preco = _f(no.get("priceMin") or no.get("price"))
    desc = _f(no.get("priceDiscountRate"))
    antigo = round(preco / (1 - desc / 100), 2) if 0 < desc < 95 else None
    return {
        "id": str(no.get("itemId")),
        "nome": (no.get("productName") or "").strip(),
        "loja": no.get("shopName") or "",
        "preco": round(preco, 2),
        "preco_antigo": antigo,
        "desconto": desc,
        "vendas": int(_f(no.get("sales"))),
        "nota": _f(no.get("ratingStar")),
        "comissao": _f(no.get("commissionRate")),
        "comissao_rs": _f(no.get("commission")),
        "imagem": no.get("imageUrl") or "",
        "link_produto": no.get("productLink") or "",
        "link_oferta": no.get("offerLink") or "",
    }


def passa_filtros(o: dict, f: dict) -> bool:
    nome = o["nome"].lower()
    if any(p in nome for p in f.get("palavras_bloqueadas", [])):
        return False
    return (
        f["preco_min"] <= o["preco"] <= f["preco_max"]
        and o["nota"] >= f["nota_min"]
        and o["vendas"] >= f["vendas_min"]
        and o["comissao"] >= f["comissao_min"]
        and o["desconto"] >= f["desconto_min"]
        and o["imagem"] and o["link_produto"]
    )


def pontuar(o: dict, pesos: dict) -> float:
    return (
        pesos["vendas"] * math.log10(o["vendas"] + 1)
        + pesos["nota"] * (o["nota"] - 4) * 2
        + pesos["desconto"] * (o["desconto"] / 20)
        + pesos["comissao"] * (o["comissao"] * 20)
    )


def escolher(ofertas: list[dict], cfg: dict, historico: dict, n: int) -> list[dict]:
    limite = time.time() - cfg["postagem"]["nao_repetir_dias"] * 86400
    recentes = {k for k, ts in historico.items() if ts >= limite}
    vistos, candidatas = set(), []
    for o in ofertas:
        if o["id"] in recentes or o["id"] in vistos:
            continue
        if passa_filtros(o, cfg["filtros"]):
            vistos.add(o["id"])
            o["score"] = round(pontuar(o, cfg["pesos"]), 3)
            candidatas.append(o)
    candidatas.sort(key=lambda o: o["score"], reverse=True)
    return candidatas[:n]
