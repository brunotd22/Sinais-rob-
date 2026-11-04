
import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

API_KEY = os.getenv("TWELVE_DATA_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL_CANDLES = "https://api.twelvedata.com/time_series"


def obter_candles():
    parametros = {
        "symbol": "EUR/USD",
        "interval": "5min",
        "outputsize": 50,
        "apikey": API_KEY
    }

    resposta = requests.get(
        URL_CANDLES,
        params=parametros,
        timeout=30
    )

    resposta.raise_for_status()
    dados = resposta.json()

    if "values" not in dados:
        raise Exception(f"Erro Twelve Data: {dados}")

    candles = dados["values"]

    if len(candles) < 22:
        raise Exception("Candles insuficientes para análise.")

    return candles


def calcular_ema(valores, periodo):
    multiplicador = 2 / (periodo + 1)
    ema = sum(valores[:periodo]) / periodo

    for valor in valores[periodo:]:
        ema = (valor * multiplicador) + (
            ema * (1 - multiplicador)
        )

    return ema


def analisar_sinal(candles):
    candles = list(reversed(candles))

    fechamentos = [
        float(candle["close"])
        for candle in candles
    ]

    ema9 = calcular_ema(fechamentos, 9)
    ema21 = calcular_ema(fechamentos, 21)

    ultimo = candles[-1]
    anterior = candles[-2]

    abertura = float(ultimo["open"])
    fechamento = float(ultimo["close"])
    fechamento_anterior = float(anterior["close"])

    if (
        ema9 > ema21
        and fechamento > abertura
        and fechamento > fechamento_anterior
    ):
        return "CALL", ema9, ema21

    if (
        ema9 < ema21
        and fechamento < abertura
        and fechamento < fechamento_anterior
    ):
        return "PUT", ema9, ema21

    return "AGUARDAR", ema9, ema21


def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERRO: Telegram não configurado.")
        return

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    resposta = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem
        },
        timeout=30
    )

    resposta.raise_for_status()

    print("Mensagem enviada ao Telegram!")


def executar_robo():
    if not API_KEY:
        print("ERRO: Twelve Data não configurada.")
        return

    candles = obter_candles()

    sinal, ema9, ema21 = analisar_sinal(candles)

    horario = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).strftime("%d/%m/%Y %H:%M:%S")

    mensagem = (
        "🤖 ROBO DE SINAIS\n"
        "━━━━━━━━━━━━━━\n"
        "Ativo: EUR/USD\n"
        "Tempo gráfico: 5 minutos\n"
        f"Sinal: {sinal}\n"
        f"EMA 9: {ema9:.5f}\n"
        f"EMA 21: {ema21:.5f}\n"
        f"Horário: {horario}\n"
        "━━━━━━━━━━━━━━\n"
        "⚠️ Sinal experimental."
    )

    print(mensagem)

    enviar_telegram(mensagem)


if __name__ == "__main__":
    try:
        executar_robo()
    except Exception as erro:
        print("ERRO NO ROBO:", erro)
