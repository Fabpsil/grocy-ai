import os
import json
import io
import requests
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from PIL import Image

app = Flask(__name__)

# Lê as configurações do painel do Home Assistant Add-on
CONFIG_PATH = '/data/options.json'
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH) as f:
        config = json.load(f)
else:
    # Fallback para testes locais
    config = {"grocy_url": "", "grocy_api_key": "", "gemini_api_key": ""}

GROCY_URL = config.get("grocy_url", "").rstrip('/')
GROCY_API = f"{GROCY_URL}/api"
HEADERS = {
    "GROCY-API-KEY": config.get("grocy_api_key", ""),
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Configura o Gemini
genai.configure(api_key=config.get("gemini_api_key", ""))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_images():
    if 'images' not in request.files:
        return jsonify({"error": "Nenhuma imagem enviada."}), 400
    
    files = request.files.getlist('images')
    if len(files) > 5:
        return jsonify({"error": "Máximo de 5 imagens permitido."}), 400

    pil_images = []
    for file in files:
        img = Image.open(file.stream)
        pil_images.append(img)

    # 1. Processar com Gemini
    prompt = """
    Analise as imagens desta embalagem de produto. 
    Extraia as seguintes informações e retorne ESTRITAMENTE em formato JSON puro (sem marcação markdown):
    {
        "nome": "Nome claro do produto",
        "codigo_barras": "Apenas números",
        "validade": "Data no formato YYYY-MM-DD (se não achar, use 2099-12-31)",
        "lote": "Número do lote",
        "info_nutricional": "Resumo das informações nutricionais e ingredientes",
        "unidade_medida": "Apenas a sigla (ex: ml, L, kg, g, pacote, unidade)"
    }
    """
    
    try:
        response = model.generate_content([prompt] + pil_images)
        texto_limpo = response.text.replace('```json', '').replace('```', '').strip()
        dados_ia = json.loads(texto_limpo)
    except Exception as e:
        return jsonify({"error": f"Erro na IA: {str(e)}"}), 500

    # 2. Verificar/Criar Unidade de Medida no Grocy
    try:
        medida_nome = dados_ia.get("unidade_medida", "unidade")
        unidades_req = requests.get(f"{GROCY_API}/objects/quantity_units", headers=HEADERS)
        unidades = unidades_req.json()
        
        qu_id = None
        for u in unidades:
            if u['name'].lower() == medida_nome.lower() or u['name_plural'].lower() == medida_nome.lower():
                qu_id = u['id']
                break
        
        if not qu_id:
            # Cria a unidade de medida
            nova_unidade = {"name": medida_nome, "name_plural": medida_nome}
            cria_qu = requests.post(f"{GROCY_API}/objects/quantity_units", headers=HEADERS, json=nova_unidade)
            qu_id = cria_qu.json().get("created_object_id")
    except Exception as e:
        return jsonify({"error": f"Erro ao gerenciar medidas: {str(e)}"}), 500

    # 3. Formatar Descrição (Lote + Nutrição)
    descricao_html = f"""
    <strong>Lote:</strong> {dados_ia.get('lote', 'N/A')}<br><br>
    <strong>Informações Nutricionais / Ingredientes:</strong><br>
    {dados_ia.get('info_nutricional', 'Não identificado.')}
    """

    # 4. Criar o Produto
    novo_produto = {
        "name": dados_ia.get("nome", "Produto Desconhecido"),
        "barcode": dados_ia.get("codigo_barras", ""),
        "description": descricao_html,
        "qu_id_purchase": qu_id,
        "qu_id_stock": qu_id,
        "qu_factor_purchase_to_stock": 1,
        "location_id": 1 # Localização padrão
    }
    
    try:
        cria_prod = requests.post(f"{GROCY_API}/objects/products", headers=HEADERS, json=novo_produto)
        if cria_prod.status_code != 200:
            return jsonify({"error": "Falha ao criar produto no Grocy."}), 500
        
        produto_id = cria_prod.json().get("created_object_id")
    except Exception as e:
        return jsonify({"error": f"Erro ao criar produto: {str(e)}"}), 500

    # 5. Adicionar ao Estoque
    estoque_payload = {
        "amount": 1,
        "best_before_date": dados_ia.get("validade", "2099-12-31"),
        "transaction_type": "purchase"
    }
    requests.post(f"{GROCY_API}/stock/products/{produto_id}/add", headers=HEADERS, json=estoque_payload)

    return jsonify({"success": True, "message": "Produto cadastrado com sucesso!", "data": dados_ia})

if __name__ == '__main__':
    # O Home Assistant Ingress usa a porta 8080 (conforme seu config.json)
    app.run(host='0.0.0.0', port=8080)
