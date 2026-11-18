# Máquina de ofertas — Achei pra Casa

Busca ofertas de casa, cozinha e organização na API oficial de afiliados da Shopee, posta as melhores no canal do Telegram 4x por dia (9h, 12h, 18h, 21h) e mantém um site de vitrine atualizado. Toda segunda gera um relatório de vendas que o Claude usa para ajustar o `config.yaml`.

## Peças
| Arquivo | O que faz |
|---|---|
| `config.yaml` | Nicho, buscas, filtros e pesos do ranking |
| `bot/shopee.py` | Conversa com a API da Shopee (assinatura SHA256) |
| `bot/selecao.py` | Filtra e ranqueia ofertas, evita repetir |
| `bot/telegram.py` | Monta o post e publica no canal |
| `bot/site.py` | Gera `docs/index.html` (GitHub Pages) |
| `bot/relatorio.py` | Relatório semanal de vendas por produto, horário e canal |
| `.github/workflows/` | Agendamento automático |

## Segredos (Settings → Secrets and variables → Actions)
| Nome | De onde vem |
|---|---|
| `SHOPEE_APP_ID` | Painel de afiliados Shopee → Open API |
| `SHOPEE_SECRET` | Mesmo lugar (App Secret) |
| `TELEGRAM_TOKEN` | @BotFather, ao criar o bot |
| `TELEGRAM_CHAT_ID` | `@nome_do_canal` (canal público) |

Nunca coloque essas chaves no código ou no chat.

## Testes locais
```
pip install -r requirements.txt pytest
pytest -q
```
