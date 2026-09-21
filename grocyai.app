import json

with open('/data/options.json') as f:
    config = json.load(f)

GROCY_URL = config.get("grocy_url")
GROCY_API_KEY = config.get("grocy_api_key")
GEMINI_API_KEY = config.get("gemini_api_key")
