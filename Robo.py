
import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

API_KEY = os.getenv("TWELVE_DATA_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://api.twelvedata.com/time_series"


def obter_candles(intervalo):
    parametros = {
        "symbol": "EUR/USD",
        "interval": intervalo,
        "outputsize": 50,
        "apikey": API_KEY
    }

    resposta = requests.get(
        URL,
        params=parametros,
        timeout=30
    )

    resposta.raise_for_status()
    dados = resposta.json()

    if "values" not in dados:
        raise Exception(f"Erro Twelve Data: {dados}")

    return list(reversed(dados["values"]))


def calcular_ema(valores, periodo):
    ema = sum(valores[:periodo]) / periodo
    multiplicador = 2 / (periodo + 1)

    for valor in valores[periodo:]:
        ema = (
            valor * multiplicador
            + ema * (1 - multiplicador)
        )

    return ema


def analisar_tendencia(candles):
    if len(candles) < 23:
        return "NEUTRO"

    # Usa o último candle fechado, não o candle em formação
    fechamentos = [
        float(c["close"])
        for c in candles[:-1]
    ]

    ema9 = calcular_ema(fechamentos, 9)
    ema21 = calcular_ema(fechamentos, 21)

    ultimo = candles[-2]

    abertura = float(ultimo["open"])
    fechamento = float(ultimo["close"])

    if ema9 > ema21 and fechamento > abertura:
        return "ALTA"

    if ema9 < ema21 and fechamento < abertura:
        return "BAIXA"

    return "NEUTRO"


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

    candles5 = obter_candles("5min")
    candles1 = obter_candles("1min")

    tendencia5 = analisar_tendencia(candles5)
    tendencia1 = analisar_tendencia(candles1)

    print("Tendência 5 minutos:", tendencia5)
    print("Tendência 1 minuto:", tendencia1)

    if tendencia5 == "ALTA" and tendencia1 == "ALTA":
        sinal = "CALL"

    elif tendencia5 == "BAIXA" and tendencia1 == "BAIXA":
        sinal = "PUT"

    else:
        sinal = "AGUARDAR"

    print("Sinal:", sinal)

    if sinal == "AGUARDAR":
        print("Sem confirmação. Telegram não enviado.")
        return

    horario = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).strftime("%d/%m/%Y %H:%M:%S")

    mensagem = (
        "🚨 SINAL CONFIRMADO 🚨\n"
        "━━━━━━━━━━━━━━\n"
        "Ativo: EUR/USD\n"
        "Tendência: 5 minutos\n"
        "Confirmação: 1 minuto\n"
        f"Direção: {sinal}\n"
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
