
import os
import requests

API_KEY = os.getenv("TWELVE_DATA_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def obter_cotacao():
    if not API_KEY:
        print("ERRO: Chave da Twelve Data não configurada.")
        return None

    url = "https://api.twelvedata.com/price"

    parametros = {
        "symbol": "EUR/USD",
        "apikey": API_KEY
    }

    try:
        resposta = requests.get(
            url, params=parametros, timeout=20
        )
        resposta.raise_for_status()
        dados = resposta.json()

        if "price" in dados:
            preco = dados["price"]
            print("EUR/USD:", preco)
            return preco

        print("ERRO DA API:", dados)
        return None

    except requests.RequestException as erro:
        print("ERRO DE CONEXÃO:", erro)
        return None


def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERRO: Telegram não configurado.")
        return

    url = (
        "https://api.telegram.org/bot"
        + TELEGRAM_TOKEN
        + "/sendMessage"
    )

    dados = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem
    }

    try:
        resposta = requests.post(
            url, json=dados, timeout=20
        )
        resposta.raise_for_status()

        resultado = resposta.json()

        if resultado.get("ok"):
            print("Mensagem enviada ao Telegram!")
        else:
            print("ERRO TELEGRAM:", resultado)

    except requests.RequestException as erro:
        print("ERRO TELEGRAM:", erro)


if __name__ == "__main__":
    preco = obter_cotacao()

    if preco:
        mensagem = (
            "ROBO DE SINAIS\n"
            "Conexao funcionando!\n"
            "EUR/USD: " + str(preco)
        )

        enviar_telegram(mensagem)
