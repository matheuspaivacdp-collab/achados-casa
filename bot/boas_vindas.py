"""Publica e fixa a mensagem de boas-vindas do canal (rodar uma vez, ou quando mudar o texto)."""
import os

import requests
import yaml

TEXTO = """👋 <b>Bem-vindo ao {nome}!</b>

Aqui você recebe, todo dia, achadinhos úteis para casa, cozinha e organização, com preço bom e boa avaliação.

✅ Só produtos com nota alta e muitas vendas
✅ Ofertas novas de manhã, no almoço e à noite
🔔 Ative as notificações (toque no nome do canal → Notificações) para não perder os preços relâmpago

⚠️ Os links são de afiliado: se você comprar por eles, eu ganho uma pequena comissão, sem custo extra para você. Preços e estoque podem mudar a qualquer momento.

📤 Conhece alguém que ama um achadinho? Compartilha o canal: {link}"""


def main():
    cfg = yaml.safe_load(open("config.yaml"))
    token, chat = os.environ["TELEGRAM_TOKEN"], os.environ["TELEGRAM_CHAT_ID"]
    canal = cfg["marca"]["canal_telegram"].lstrip("@")
    texto = TEXTO.format(nome=cfg["marca"]["nome"], link=f"https://t.me/{canal}")
    base = f"https://api.telegram.org/bot{token}"
    r = requests.post(f"{base}/sendMessage", data={"chat_id": chat, "text": texto, "parse_mode": "HTML",
                                                   "disable_web_page_preview": True}, timeout=30)
    r.raise_for_status()
    msg_id = r.json()["result"]["message_id"]
    requests.post(f"{base}/pinChatMessage", data={"chat_id": chat, "message_id": msg_id,
                                                  "disable_notification": True}, timeout=30).raise_for_status()
    print("Mensagem de boas-vindas publicada e fixada:", msg_id)


if __name__ == "__main__":
    main()
