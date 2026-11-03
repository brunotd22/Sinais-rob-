
import os
import requests

API_KEY = os.getenv("TWELVE_DATA_API_KEY")

def obter_cotacao():
    if not API_KEY:
        print("ERRO: Chave da Twelve Data não configurada.")
        return

    url = "https://api.twelvedata.com/price"
    parametros = {
        "symbol": "EUR/USD",
        "apikey": API_KEY
    }

    try:
        resposta = requests.get(url, params=parametros, timeout=20)
        resposta.raise_for_status()
        dados = resposta.json()

        if "price" in dados:
            print("EUR/USD:", dados["price"])
        else:
            print("ERRO DA API:", dados)

    except requests.RequestException as erro:
        print("ERRO DE CONEXÃO:", erro)

if __name__ == "__main__":
    obter_cotacao()
