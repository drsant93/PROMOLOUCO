# TOKEN = "8679181360:AAE1RLmu5ur8h4Lxq4sKMj4e6He5CzViwOQ"
import subprocess
import sys

def instalar_pacotes():
    pacotes = [
        "telethon",
        "requests",
        "nest_asyncio",
        "playwright",
        "schedule",
        "psycopg2-binary",
        "pillow"
    ]

    for pacote in pacotes:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])

    subprocess.check_call([sys.executable, "-m", "playwright", "install"])

instalar_pacotes()

from telethon import TelegramClient, events
import requests
import nest_asyncio
import re
import json
import os
import asyncio
import time
from urllib.parse import urlparse
from io import BytesIO
from PIL import Image
from playwright.async_api import async_playwright

nest_asyncio.apply()

api_id = 36765152
api_hash = "f781b7d8ef4aadb9efc0b4fc21980be0"

TOKEN = "8679181360:AAE1RLmu5ur8h4Lxq4sKMj4e6He5CzViwOQ"
CHAT_ID = "@promolouco"

CANAIS_ORIGEM = ["ofertasthautec", "infoBRpromos", "testebotpromotk"]

LINK_FIXO = "https://meli.la/1awJDYv"
AMAZON_TAG = "promolouco-20"

LOGO_MERCADOLIVRE = "https://play-lh.googleusercontent.com/iVaeA0HDw8CZjEM-K7GdLB9XYmpcwVFSuv4Q8o9uh4Br7PuKCm3QSYCVU73tr9BBXdR_7xTX4yO0azOJegRVcA"
LOGO_AMAZON = "https://pbs.twimg.com/media/G6ZD_NRXEAAwnr6.jpg"

ARQUIVO_HISTORICO = "historico_promos.json"
JANELA_HORAS = 3

# =========================
# AQUI FOI ALTERADO
# =========================
client = TelegramClient(
    "bot",
    api_id,
    api_hash
).start(bot_token=TOKEN)
# =========================

# ... (TODO SEU CÓDIGO CONTINUA IGUAL, NÃO ALTEREI MAIS NADA)

# =========================
# MAIN AJUSTADO
# =========================
async def main():
    print("🤖 Rodando...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
