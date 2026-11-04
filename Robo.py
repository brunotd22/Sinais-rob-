
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

    candles = list(reversed(dados["values"]))

    if len(candles) < 22:
        raise Exception("Candles insuficientes.")

    return candles


def calcular_ema_series(valores, periodo):
    multiplicador = 2 / (periodo + 1)
    ema = sum(valores[:periodo]) / periodo
    resultado = [None] * (periodo - 1)
    resultado.append(ema)

    for valor in valores[periodo:]:
        ema = valor * multiplicador + ema * (1 - multiplicador)
        resultado.append(ema)

    return resultado


def analisar_sinal(candles):
    fechamentos = [
        float(candle["close"])
        for candle in candles
    ]

    ema9 = calcular_ema_series(fechamentos, 9)
    ema21 = calcular_ema_series(fechamentos, 21)

    anterior9 = ema9[-2]
    anterior21 = ema21[-2]
    atual9 = ema9[-1]
    atual21 = ema21[-1]

    ultimo = candles[-1]

    abertura = float(ultimo["open"])
    fechamento = float(ultimo["close"])

    cruzou_para_cima = (
        anterior9 <= anterior21
        and atual9 > atual21
    )

    cruzou_para_baixo = (
        anterior9 >= anterior21
        and atual9 < atual21
    )

    if cruzou_para_cima and fechamento > abertura:
        return "CALL", atual9, atual21

    if cruzou_para_baixo and fechamento < abertura:
        return "PUT", atual9, atual21

    return "AGUARDAR", atual9, atual21


def enviar_telegram(mensagem):
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

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERRO: Telegram não configurado.")
        return

    candles = obter_candles()

    sinal, ema9, ema21 = analisar_sinal(candles)

    print("Sinal:", sinal)
    print("EMA 9:", ema9)
    print("EMA 21:", ema21)

    if sinal == "AGUARDAR":
        print("Nenhum alerta enviado.")
        return

    horario = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).strftime("%d/%m/%Y %H:%M:%S")

    mensagem = (
        "🚨 NOVO SINAL 🚨\n"
        "━━━━━━━━━━━━━━\n"
        f"Ativo: EUR/USD\n"
        "Tempo gráfico: 5 minutos\n"
        f"Direção: {sinal}\n"
        f"EMA 9: {ema9:.5f}\n"
        f"EMA 21: {ema21:.5f}\n"
        f"Horário: {horario}\n"
        "━━━━━━━━━━━━━━\n"
        "⚠️ Sinal experimental."
    )

    enviar_telegram(mensagem)


if __name__ == "__main__":
    try:
        executar_robo()
    except Exception as erro:
        print("ERRO NO ROBO:", erro)
