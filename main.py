# TOKEN = "8679181360:AAE1RLmu5ur8h4Lxq4sKMj4e6He5CzViwOQ"
import subprocess
import sys

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
# LOGOS
# =========================
LOGO_MERCADOLIVRE = "https://play-lh.googleusercontent.com/iVaeA0HDw8CZjEM-K7GdLB9XYmpcwVFSuv4Q8o9uh4Br7PuKCm3QSYCVU73tr9BBXdR_7xTX4yO0azOJegRVcA"
LOGO_AMAZON = "https://pbs.twimg.com/media/G6ZD_NRXEAAwnr6.jpg"

ARQUIVO_HISTORICO = "historico_promos.json"
JANELA_HORAS = 3  # Janela de 3 horas para duplicatas

# =========================
# CACHE DE PROMOÇÕES
# =========================
def carregar_historico():
    """Carrega histórico de promoções enviadas"""
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_historico(historico):
    """Salva histórico de promoções"""
    try:
        with open(ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erro ao salvar histórico: {e}")

def limpar_url_parametros(url):
    """Remove parâmetros da URL para comparação"""
    if not url:
        return url
    # Remove tudo após ? ou #
    url_limpa = re.split(r'[?#]', url)[0]
    # Remove trailing slash
    url_limpa = url_limpa.rstrip('/')
    return url_limpa.lower()

def extrair_cupom(texto):
    """Extrai cupom do texto (ex: 'CUPOM COELHO' → 'COELHO')"""
    if not texto:
        return None
    
    # Procura por padrão "CUPOM XXXXX" ou "CÓDIGO XXXXX" etc
    match = re.search(r'(?:CUPOM|CÓDIGO|DESCONTO|CUPÓN)\s+([A-Z0-9]+)', texto, re.IGNORECASE)
    if match:
        cupom = match.group(1).upper().strip()
        print(f"🎫 Cupom extraído: {cupom}")
        return cupom
    return None

def foi_enviado_recentemente(identificador, tipo="url"):
    """Verifica se uma promoção foi enviada nos últimas JANELA_HORAS"""
    agora = time.time()
    historico = carregar_historico()
    
    # Remove entradas expiradas
    historico = [h for h in historico if agora - h.get('timestamp', 0) < JANELA_HORAS * 3600]
    salvar_historico(historico)
    
    for item in historico:
        if item.get('tipo') == tipo and item.get('id') == identificador:
            tempo_passado = (agora - item['timestamp']) / 60
            print(f"⚠️ {tipo.upper()} já foi enviado há {tempo_passado:.1f} minutos")
            return True
    
    return False

def marcar_como_enviado(identificador, tipo="url", detalhes=""):
    """Marca uma promoção como enviada"""
    historico = carregar_historico()
    
    novo_item = {
        "id": identificador,
        "tipo": tipo,
        "timestamp": time.time(),
        "detalhes": detalhes
    }
    
    historico.append(novo_item)
    salvar_historico(historico)
    print(f"✅ Registrado no histórico: {tipo} - {identificador[:50]}")

def is_valid_image_url(url):
    if not isinstance(url, str) or not url.startswith("http"):
        return False
    if url.startswith("data:"):
        return False

    bad_patterns = ["sprite", "nav-sprite", "privacy", "gno/spritees", "favicon", "logo", "icon", "badge"]
    if any(pattern in url.lower() for pattern in bad_patterns):
        return False

    good_extensions = [".jpg", ".jpeg", ".png", ".webp"]
    if not any(url.lower().endswith(ext) for ext in good_extensions):
        # URLs without a standard image extension are likely not direct product images
        return False

    return True


def normalizar_url_imagem_amazon(url):
    if not isinstance(url, str):
        return url

    if "m.media-amazon.com/images" in url:
        return re.sub(r"_AC_(?:SX|UY|SY|UX)\d+_", "_AC_SX679_", url)

    return url

client = TelegramClient('session', api_id, api_hash)

def extrair_links(texto):
    return re.findall(r'(https?://\S+)', texto)

async def expandir_link(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        final_url = resp.url
        print("🔗 URL expandida (requests):", final_url)

        html = resp.text.lower()
        if final_url == url and resp.status_code == 200 and (
            "window.location" in html or
            "location.href" in html or
            "document.location" in html or
            "<meta http-equiv=\"refresh\"" in html or
            "redirecionando" in html
        ):
            print("🔎 Detectado redirecionamento JS, usando Playwright")
            return await expandir_link_playwright(url)

        return final_url
    except Exception as e:
        print("⚠️ expandir_link requests falhou:", e)
        return await expandir_link_playwright(url)


async def expandir_link_playwright(url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(url, wait_until="load", timeout=30000)
            await page.wait_for_timeout(3000)
            final_url = page.url
            print("🔗 URL expandida (Playwright):", final_url)
            await browser.close()
            return final_url
    except Exception as e:
        print("❌ expandir_link_playwright falhou:", e)
        return url


def classificar_link(url):
    if not isinstance(url, str):
        return None

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    hostname = hostname.lower()

    if "mercadolivre" in hostname or "meli.la" in hostname:
        return "ml"
    if "amazon" in hostname or "amzn.to" in hostname:
        return "amazon"

    # Suporte adicional para URLs de encurtadores que redirecionam
    if "bit.ly" in hostname or "tinyurl.com" in hostname or "t.co" in hostname:
        return None

    return None

# =========================
# LIMPAR URL AMAZON
# =========================
def limpar_url_amazon(url):
    try:
        print("🧠 Limpando URL Amazon...")

        match = re.search(r"(https?://www\.amazon\.com\.br/.*/dp/[A-Z0-9]+)", url)

        if not match:
            match = re.search(r"(https?://www\.amazon\.com\.br/dp/[A-Z0-9]+)", url)

        if match:
            limpa = match.group(1)
        else:
            limpa = url.split("?")[0]

        final = limpa + f"?tag={AMAZON_TAG}"

        print("🎯 URL limpa com tag:", final)
        return final

    except Exception as e:
        print("❌ erro limpar:", e)
        return url

# =========================
# RESOLVER LINK + EXTRAIR IMAGEM (ML)
# =========================
async def resolver_link_e_imagem_ml(page, url):
    """Navega para página de produto e extrai link + imagem"""
    try:
        print("🌐 Abrindo URL:", url)
        await page.goto(url, wait_until="load")
        await page.wait_for_timeout(3000)

        # Procura o botão para ir à página de produto
        await page.wait_for_timeout(1000)
        botao = page.locator("a.poly-component__link--action-link")

        if await botao.count() > 0:
            link_botao = await botao.first.get_attribute("href")
            print("✅ Link do botão encontrado:", link_botao)

            if link_botao:
                # Vai direto para a URL do produto, sem clicar no botão do social
                await page.goto(link_botao, wait_until="load")
                await page.wait_for_timeout(3000)

                # 🔥 Agora já está na página de PRODUTO, extrai a imagem
                imagem_url = await extrair_imagem_da_pagina_produto(page)

                # Pega o link final da página de produto
                link_final = page.url
                print("✅ Página de produto carregada:", link_final)

                return link_final.split("?")[0], imagem_url
            else:
                print("⚠️ Botão encontrado sem href")
                return None, None

        print("⚠️ Botão de compra não encontrado")
        return None, None

    except Exception as e:
        print("❌ Erro resolver:", e)
        return None, None

# =========================
# EXTRAIR IMAGEM DA PÁGINA DO PRODUTO
# =========================
async def extrair_imagem_da_pagina_produto(page):
    """Extrai a primeira imagem do carrossel da página de produto do ML"""
    try:
        imagem_url = None

        async def tentar_atributos(element):
            for attr in ["src", "data-zoom", "data-src", "data-lazy-src"]:
                if not element:
                    continue
                candidate = await element.get_attribute(attr)
                if is_valid_image_url(candidate):
                    return candidate
            return None

        # Tenta o seletor da galeria principal da página de produto
        imagem_elemento = page.locator("img.ui-pdp-gallery__figure__image")
        if await imagem_elemento.count() > 0:
            imagem_url = await tentar_atributos(imagem_elemento.first)
            print("🖼️ Imagem encontrada (galeria):", imagem_url)

        if not imagem_url:
            # Fallback: tenta qualquer imagem com alt
            imagens = page.locator("img[alt]")
            for i in range(await imagens.count()):
                imagem_url = await tentar_atributos(imagens.nth(i))
                if imagem_url:
                    print("🖼️ Imagem encontrada (fallback):", imagem_url)
                    break

        if not is_valid_image_url(imagem_url):
            print("⚠️ Imagem ML inválida ou placeholder, ignorando...")
            imagem_url = None

        return imagem_url
    except Exception as e:
        print("⚠️ Erro ao extrair imagem:", e)
        return None

# =========================
# ML
# =========================
async def gerar_link_afiliado_ml(link_original):
    try:
        async with async_playwright() as p:

            context = await p.chromium.launch_persistent_context(
                user_data_dir="./perfil-playwright",
                headless=False
            )

            page = await context.new_page()

            # 🔥 Navega para produto E extrai imagem
            link_final, imagem_url = await resolver_link_e_imagem_ml(page, link_original)

            if not link_final:
                print("🔁 Usando fallback")
                await context.close()
                # Se não conseguir extrair, usa logo do ML
                return {"link": LINK_FIXO, "imagem": LOGO_MERCADOLIVRE}

            print("🎯 Indo gerar afiliado com:", link_final)

            try:
                await page.goto("https://www.mercadolivre.com.br/afiliados")
                await page.wait_for_load_state("networkidle")

                if await page.locator("#AFFILIATES_LINK_BUILDER").count() == 0:
                    print("⚠️ Botão AFFILIATES_LINK_BUILDER não encontrado")
                    raise Exception("Affiliate builder não disponível")

                await page.click("#AFFILIATES_LINK_BUILDER")
                await page.wait_for_selector("#url-0", timeout=15000)

                await page.click("#url-0")
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Backspace")
                await page.type("#url-0", link_final, delay=30)

                await page.wait_for_timeout(2000)

                await page.locator("button:has-text('Gerar')").click()

                await page.wait_for_selector("#textfield-copyLink-1", timeout=15000)
                link_afiliado = await page.input_value("#textfield-copyLink-1")

                print("🎯 LINK FINAL:", link_afiliado)

                await context.close()

                imagem_final = imagem_url if imagem_url else LOGO_MERCADOLIVRE
                return {"link": link_afiliado or link_final, "imagem": imagem_final}
            except Exception as e:
                print("⚠️ Falha ao gerar link afiliado ML:", e)
                await context.close()
                return {"link": link_final, "imagem": imagem_url if imagem_url else LOGO_MERCADOLIVRE}
    except Exception as e:
        print("❌ erro ML:", e)
        return {"link": LINK_FIXO, "imagem": LOGO_MERCADOLIVRE}

# =========================
# AMAZON CORRIGIDO
# =========================
async def gerar_link_afiliado_amazon(link_original):
    try:
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir="./perfil-playwright",
                headless=False
            )

            page = await context.new_page()

            print("🌐 Abrindo Amazon:", link_original)
            await page.goto(link_original, wait_until="load")

            await page.wait_for_timeout(5000)

            # 🔥 pega URL REAL da página
            url_final = page.url
            print("🔎 URL final carregada:", url_final)

            # 🔥 limpa + adiciona tag
            url_com_tag = limpar_url_amazon(url_final)

            # 🔥 extrai imagem do produto usando imgTagWrapperId
            imagem_url = None
            try:
                imagem_elemento = page.locator("#imgTagWrapperId img")
                if await imagem_elemento.count() > 0:
                    candidate = await imagem_elemento.first.get_attribute("src")
                    if is_valid_image_url(candidate):
                        imagem_url = normalizar_url_imagem_amazon(candidate)
                        print("🖼️ Imagem encontrada (#imgTagWrapperId img):", imagem_url)
                    else:
                        print("⚠️ Amazon imgTagWrapperId inválida, descartando:", candidate)
                else:
                    print("⚠️ id imgTagWrapperId não encontrado, usando logo padrão Amazon")
            except Exception as e:
                print("⚠️ Erro ao extrair imagem:", e)

            if not is_valid_image_url(imagem_url):
                imagem_url = None

            # 🔥 clica no botão para gerar link curto
            await page.click("#amzn-ss-get-link-button")
            await page.wait_for_selector("#amzn-ss-text-shortlink-textarea", timeout=15000)

            # aguarda o SiteStripe preencher o textarea
            await page.wait_for_timeout(3000)

            # pega o texto do textarea (não input_value, que é pra <input>)
            link_curto = await page.text_content("#amzn-ss-text-shortlink-textarea")
            
            # remove espaços em branco
            if link_curto:
                link_curto = link_curto.strip()

            print("🎯 LINK AMAZON FINAL:", link_curto)

            if not link_curto or "amzn.to" not in link_curto:
                print("⚠️ Falhou ao gerar link curto, abortando...")
                await context.close()
                # Se falhar, retorna sem encurtar (não tem amzn.to)
                return {"link": link_original, "imagem": LOGO_AMAZON}

            await context.close()
            
            # Se não conseguir extrair imagem da página, usa logo da Amazon
            imagem_final = imagem_url if imagem_url else LOGO_AMAZON
            
            return {"link": link_curto, "imagem": imagem_final}

    except Exception as e:
        print("❌ erro Amazon:", e)
        # Em caso de erro, retorna com logo da Amazon
        return {"link": link_original, "imagem": LOGO_AMAZON}

# =========================
# TRANSFORMAR
# =========================
async def transformar(texto):
    print("\n📩 ORIGINAL:")
    print(texto)

    links = extrair_links(texto)
    imagens = []  # armazena imagens de todos os produtos
    sucesso = True  # flag para indicar se todos os links foram processados com sucesso
    duplicata = False  # flag para indicar se é uma promoção duplicada
    identificadores = []  # para registrar no histórico depois

    for link in links:
        link_expandido = await expandir_link(link)
        tipo_link = classificar_link(link_expandido)

        print("🔎 Link final:", link_expandido, "Tipo:", tipo_link)

        if tipo_link == "ml":
            resultado = await gerar_link_afiliado_ml(link_expandido)
            novo_link = resultado["link"]
            imagem = resultado["imagem"]

            # Valida se é um link de afiliado encurtado (meli.la/xxxx)
            # Se não for, usa o link fixo do usuário
            if not novo_link.startswith("https://meli.la/") and not novo_link.startswith("http://meli.la/"):
                print(f"⚠️ Link ML não é de afiliado encurtado ({novo_link}), usando LINK_FIXO")
                novo_link = LINK_FIXO
                
                # Se usar LINK_FIXO, extrai cupom do texto para validação
                cupom = extrair_cupom(texto)
                if cupom and foi_enviado_recentemente(cupom, tipo="cupom"):
                    print(f"❌ Cupom {cupom} já foi usado no histórico recente")
                    duplicata = True
                else:
                    if cupom:
                        identificadores.append((cupom, "cupom", cupom))

            if imagem:
                imagens.append(imagem)

            print("🔁 FINAL ML:", novo_link)
            texto = texto.replace(link, f"🛒 Compre aqui: {novo_link}")

        elif tipo_link == "amazon":
            resultado = await gerar_link_afiliado_amazon(link_expandido)
            novo_link = resultado["link"]
            imagem = resultado["imagem"]

            # Se o link não foi encurtado (não tem amzn.to), significa que falhou
            if "amzn.to" not in novo_link:
                print("❌ Falha ao gerar link Amazon, não processando esta mensagem")
                sucesso = False
            else:
                # Link foi encurtado, valida se já foi enviado
                url_expandida = await expandir_link(novo_link)
                url_limpa = limpar_url_parametros(url_expandida)
                
                if foi_enviado_recentemente(url_limpa, tipo="produto_amazon"):
                    print(f"❌ Produto Amazon já foi enviado recentemente: {url_limpa}")
                    duplicata = True
                else:
                    identificadores.append((url_limpa, "produto_amazon", novo_link))

            if imagem:
                imagens.append(imagem)

            print("🔁 FINAL AMAZON:", novo_link)
            texto = texto.replace(link, novo_link)

        else:
            print("⚠️ Tipo do link não identificado, mantendo original:", link_expandido)

    print("\n📤 FINAL:")
    print(texto)

    return {
        "texto": texto, 
        "imagens": imagens, 
        "sucesso": sucesso,
        "duplicata": duplicata,
        "identificadores": identificadores
    }

# =========================
# IA DE TEXTO
# =========================

def limpar_texto_promocional(texto):
    if not texto:
        return texto

    # Remove linhas inteiras que contenham "publi" ou "anuncio"
    linhas = texto.split('\n')
    linhas_filtradas = []
    for linha in linhas:
        if not re.search(r'(\bpubli\b|\banuncio\b)', linha, flags=re.IGNORECASE):
            linhas_filtradas.append(linha)
    
    texto = '\n'.join(linhas_filtradas)
    
    # Remove outras palavras promocionais
    patterns = [
        r"\bpatrocinado\b",
        r"\bpatrocínio\b",
        r"\bpropaganda\b",
        r"\bparceria\b"
    ]
    texto = re.sub("|" .join(patterns), "", texto, flags=re.IGNORECASE)
    texto = re.sub(r" {2,}", " ", texto)  # Remove apenas múltiplos espaços, NÃO quebras de linha
    texto = re.sub(r"\n[ \t]+\n", "\n\n", texto)  # Remove espaços extras nas linhas em branco
    texto = re.sub(r"\n\n+", "\n\n", texto)  # Remove quebras de linha em excesso
    return texto.strip()


def fallback_ajustar_texto(texto):
    texto = limpar_texto_promocional(texto)
    if "contribua" not in texto.lower() and "grupo" not in texto.lower():
        texto = texto.strip() + "\n\n💬 Contribua com o grupo sempre ativando as promoções aqui!"
    return texto


async def validar_e_ajustar_texto(texto):
    return fallback_ajustar_texto(texto)

# =========================
# IMAGEM COM PADDING
# =========================
async def adicionar_padding_branco(url_imagem, padding=80):
    """Baixa imagem, adiciona padding branco e retorna o caminho local"""
    try:
        print(f"🎨 Adicionando padding {padding}px à imagem...")
        
        # Baixa a imagem
        resp = requests.get(url_imagem, timeout=15)
        img = Image.open(BytesIO(resp.content))
        
        # Converte para RGB se necessário
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Cria nova imagem com padding branco centralizado
        nova_largura = img.width + padding * 2
        nova_altura = img.height + padding * 2
        nova_img = Image.new('RGB', (nova_largura, nova_altura), 'white')
        nova_img.paste(img, (padding, padding))
        
        # Salva temporariamente
        arquivo_temp = f"temp_img_{int(time.time() * 1000)}.jpg"
        nova_img.save(arquivo_temp, quality=95)
        
        print(f"✅ Imagem salva: {arquivo_temp}")
        return arquivo_temp
        
    except Exception as e:
        print(f"⚠️ Erro ao adicionar padding: {e}")
        return url_imagem  # Fallback: usa a URL original

# =========================
# TELEGRAM
# =========================
def enviar(msg, imagem_url=None):
    """Envia mensagem de texto. Se imagem_url for fornecida, envia com foto centralizada"""
    arquivo_temp = None
    try:
        if imagem_url:
            # Adiciona padding à imagem
            arquivo_temp = asyncio.run(adicionar_padding_branco(imagem_url, padding=80))
            
            # Envia como foto com legenda
            with open(arquivo_temp, 'rb') as f:
                requests.post(
                    f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
                    data={"chat_id": CHAT_ID, "caption": msg},
                    files={"photo": f}
                )
        else:
            # Envia como texto simples
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg}
            )
    except Exception as e:
        print(f"❌ Erro ao enviar: {e}")
    finally:
        # Limpa arquivo temporário
        if arquivo_temp and os.path.exists(arquivo_temp):
            try:
                os.remove(arquivo_temp)
                print(f"🗑️ Removido: {arquivo_temp}")
            except:
                pass

# =========================
# HANDLER
# =========================
@client.on(events.NewMessage)
async def handler(event):
    chat = await event.get_chat()
    username = getattr(chat, 'username', None)

    if username in CANAIS_ORIGEM:
        print("\n📥 Recebido:", username)

        texto = event.message.message
        if not texto:
            return

        resultado = await transformar(texto)
        texto_final = resultado["texto"]
        imagens = resultado["imagens"]
        sucesso = resultado["sucesso"]
        duplicata = resultado.get("duplicata", False)
        identificadores = resultado.get("identificadores", [])

        # Se houve falha ao processar os links, não envia nada
        if not sucesso:
            print("⛔ Não enviando esta mensagem (falha ao processar links)")
            return

        # Se é uma promoção duplicada, não envia nada
        if duplicata:
            print("♻️ Não enviando esta mensagem (promoção duplicada nas últimas 3 horas)")
            return

        texto_final = await validar_e_ajustar_texto(texto_final)
        print("📝 Texto ajustado:", texto_final)
        
        # se tiver imagem (do produto ou logo da plataforma), envia com foto
        if imagens and len(imagens) > 0:
            enviar(texto_final, imagens[0])  # envia primeira imagem
        else:
            enviar(texto_final)
        
        # Registra no histórico após enviar com sucesso
        for ident, tipo, detalhes in identificadores:
            marcar_como_enviado(ident, tipo, detalhes)

async def main():
    print("🤖 Rodando...")

    await client.connect()

    if not await client.is_user_authorized():
        print("⚠️ Não autorizado, iniciando login...")
        await client.start()  # ← aqui ele vai pedir código SMS
    else:
        print("✅ Já autorizado")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
