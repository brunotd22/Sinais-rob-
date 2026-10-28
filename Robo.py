import os
import requests

API_KEY = os.getenv("TWELVE_DATA_API_KEY")

def obter_cotacao():
if not API_KEY:
print("Configure a chave TWELVE_DATA_API_KEY.")
return

```
url = "https://api.twelvedata.com/price"
parametros = {
    "symbol": "EUR/USD",
    "apikey": API_KEY
}

try:
    resposta = requests.get(url, params=parametros, timeout=15)
    dados = resposta.json()

    if "price" in dados:
        print("EUR/USD:", dados["price"])
    else:
        print("Resposta da API:", dados)

except requests.RequestException as erro:
    print("Erro de conexão:", erro)
```

if **name** == "**main**":
obter_cotacao()
