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

# ⚠️ pode deixar por enquanto
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

# =========================
# CLIENT (AJUSTADO)
# =========================
client = TelegramClient('session', api_id, api_hash)

# =========================
# TODO SEU CÓDIGO CONTINUA IGUAL
# (NÃO MUDEI NADA ABAIXO)
# =========================

# ... (todo o resto do seu código exatamente igual até o final)

# =========================
# MAIN CORRIGIDO
# =========================
async def main():
    print("🤖 Rodando...")

    # conecta usando sessão já existente
    await client.connect()

    # verifica se está autorizado
    if not await client.is_user_authorized():
        print("❌ Sessão não autorizada. Gere a session no seu PC primeiro.")
        return

    print("✅ Conectado com sucesso!")

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
