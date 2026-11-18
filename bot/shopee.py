"""Cliente da API oficial de afiliados da Shopee Brasil (GraphQL)."""
import hashlib
import json
import os
import time

import requests

ENDPOINT = "https://open-api.affiliate.shopee.com.br/graphql"


class ShopeeError(Exception):
    pass


class Shopee:
    def __init__(self, app_id=None, secret=None, session=None):
        self.app_id = app_id or os.environ.get("SHOPEE_APP_ID", "")
        self.secret = secret or os.environ.get("SHOPEE_SECRET", "")
        if not self.app_id or not self.secret:
            raise ShopeeError("Faltam SHOPEE_APP_ID e SHOPEE_SECRET nos Secrets do GitHub.")
        self.http = session or requests.Session()

    def _headers(self, payload: str) -> dict:
        ts = str(int(time.time()))
        sig = hashlib.sha256((self.app_id + ts + payload + self.secret).encode()).hexdigest()
        return {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={self.app_id}, Timestamp={ts}, Signature={sig}",
        }

    def query(self, gql: str, variables: dict | None = None) -> dict:
        payload = json.dumps({"query": gql, "variables": variables or {}}, separators=(",", ":"))
        r = self.http.post(ENDPOINT, data=payload, headers=self._headers(payload), timeout=30)
        r.raise_for_status()
        body = r.json()
        if body.get("errors"):
            msg = body["errors"][0].get("message", str(body["errors"]))
            raise ShopeeError(f"Shopee respondeu erro: {msg}")
        return body.get("data", {})

    def buscar(self, termo: str, limite: int = 30, pagina: int = 1) -> list[dict]:
        gql = """
        query Busca($kw: String, $page: Int, $limit: Int) {
          productOfferV2(keyword: $kw, sortType: 2, page: $page, limit: $limit) {
            nodes {
              itemId productName shopName
              price priceMin priceMax priceDiscountRate
              sales ratingStar commissionRate commission
              imageUrl productLink offerLink
            }
          }
        }"""
        data = self.query(gql, {"kw": termo, "page": pagina, "limit": limite})
        return (data.get("productOfferV2") or {}).get("nodes") or []

    def link_curto(self, url: str, sub_ids: list[str]) -> str:
        gql = """
        mutation Link($url: String!, $subs: [String]) {
          generateShortLink(input: {originUrl: $url, subIds: $subs}) { shortLink }
        }"""
        data = self.query(gql, {"url": url, "subs": sub_ids})
        return data["generateShortLink"]["shortLink"]

    def conversoes(self, inicio: int, fim: int, limite: int = 500) -> list[dict]:
        """Relatório de conversões (vendas) entre dois timestamps Unix."""
        gql = """
        query Conv($start: Int64, $end: Int64, $limit: Int, $scroll: String) {
          conversionReport(purchaseTimeStart: $start, purchaseTimeEnd: $end,
                           limit: $limit, scrollId: $scroll) {
            nodes {
              purchaseTime clickTime conversionId totalCommission utmContent
              orders { orderStatus items { itemId itemName itemPrice itemTotalCommission } }
            }
            pageInfo { hasNextPage scrollId }
          }
        }"""
        todos, scroll = [], None
        while True:
            data = self.query(gql, {"start": inicio, "end": fim, "limit": limite, "scroll": scroll})
            rep = data.get("conversionReport") or {}
            todos += rep.get("nodes") or []
            info = rep.get("pageInfo") or {}
            if not info.get("hasNextPage"):
                return todos
            scroll = info.get("scrollId")
