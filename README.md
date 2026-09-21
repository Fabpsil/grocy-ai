# Grocy Vision AI - Home Assistant Add-on

Cadastre produtos automaticamente na sua instância do Grocy utilizando modelos de IA (Google Gemini). A partir da foto de uma embalagem, este add-on extrai nome, código de barras, validade, lote e informações nutricionais, e realiza o cadastro via API.

## 🚀 Instalação

1. No Home Assistant, acesse **Configurações** > **Add-ons**.
2. Clique no botão **Loja de complementos** no canto inferior direito.
3. No canto superior direito da tela, clique no ícone de três pontos e selecione **Repositórios**.
4. Cole a URL deste repositório: `https://github.com/Fabpsil/grocy-ai` e clique em **Adicionar**.
5. Feche a janela de repositórios e recarregue a página (ou pesquise por "Grocy Vision AI").
6. Clique no add-on **Grocy Vision AI** e selecione **Instalar**.

## ⚙️ Configuração

Antes de iniciar o serviço, vá até a aba **Configuração** do add-on e preencha os parâmetros obrigatórios:

* **Grocy URL**: A URL local ou externa de acesso ao seu Grocy (ex: `http://homeassistant.local:9192` ou `http://IP_DO_HA:9192`).
* **Grocy API Key**: Sua chave de autenticação do Grocy (Gerada no Grocy em: *Ferramentas (Engrenagem) > Gerenciar Chaves de API*).
* **Gemini API Key**: Sua chave de API gerada no Google AI Studio para processamento das imagens.

Após preencher, clique em **Salvar**. Vá para a aba **Info** e clique em **Iniciar**. Recomendamos ativar também as opções "Iniciar durante a inicialização" e "Watchdog".

## 📸 Como usar

O add-on expõe um servidor interno no Home Assistant (por padrão na porta `8080`) que escuta as requisições para processamento de imagens.

Você pode enviar as fotos chamando o endpoint via Automações ou Node-RED.

**Exemplo de integração nativa (REST Command):**
Adicione o código abaixo no seu `configuration.yaml` para criar um serviço capaz de enviar caminhos de imagens para o add-on:

```yaml
rest_command:
  grocy_ai_scan:
    url: "http://localhost:8080/api/scan" # Ajuste o endpoint conforme as rotas do seu grocyai.py
    method: post
    payload: '{"image_url": "{{ image_url }}"}'
    headers:
      Content-Type: "application/json"
