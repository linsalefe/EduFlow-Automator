import asyncio
import os
import base64
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

# --- FUNÇÃO AUXILIAR PARA BASE64 ---
def imagem_para_base64(caminho_arquivo):
    """Lê uma imagem local e converte para string Base64 para embutir no HTML."""
    path = Path(caminho_arquivo)
    if not path.exists():
        print(f"⚠️ AVISO: Logo não encontrada em: {path.absolute()}")
        return None
    
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Retorna formatado para o HTML (Data URI)
    return f"data:image/png;base64,{encoded_string}"

async def gerar_post_teste():
    # --- CONFIGURAÇÕES ---
    pasta_templates = "src/templates"
    nome_template = "post_estacio.html" 
    arquivo_saida = "post_eduflow_vendas_crm.jpg"
    
    # 1. CAMINHO DA LOGO SEM FUNDO
    # Note que o nome do arquivo que você subiu é "lodo_sem_fundo.png" (com 'd')
    caminho_logo_local = Path("assets/brand/lodo_sem_fundo.png")
    
    # 2. CONVERTE PARA BASE64
    logo_base64 = imagem_para_base64(caminho_logo_local)
    
    # --- COPY: VENDAS & CRM ---
    headline_text = "IA INTEGRADA\nAO SEU CRM"
    subheadline_text = "Automatize o follow-up e <strong>recupere leads</strong> parados no funil automaticamente."
    bg_image = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1080&q=80"

    # --- LÓGICA DE TAMANHO ---
    tamanho_texto = len(headline_text)
    if tamanho_texto < 15: classe = "text-xl"
    elif tamanho_texto < 25: classe = "text-lg"
    elif tamanho_texto < 50: classe = "text-md"
    else: classe = "text-sm"

    dados_do_post = {
        "imagem_fundo": bg_image,
        "headline": headline_text,
        "subheadline": subheadline_text,
        "classe_tamanho_texto": classe,
        "logo_path": logo_base64 
    }

    # --- RENDERIZAÇÃO ---
    print("🎨 Renderizando Post com Logo Sem Fundo...")
    
    env = Environment(loader=FileSystemLoader(pasta_templates))
    template = env.get_template(nome_template)
    html_pronto = template.render(**dados_do_post)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1080})
        
        await page.set_content(html_pronto)
        try: await page.wait_for_load_state("networkidle", timeout=5000)
        except: pass
        
        await page.screenshot(path=arquivo_saida, type="jpeg", quality=95)
        await browser.close()

    print(f"✅ SUCESSO! Arte salva em: {os.path.abspath(arquivo_saida)}")

if __name__ == "__main__":
    asyncio.run(gerar_post_teste())
    