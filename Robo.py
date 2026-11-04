
import os
import json
import requests
import subprocess
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_KEY = os.getenv("TWELVE_DATA_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

URL = "https://api.twelvedata.com/time_series"
ARQUIVO = "historico.json"


def obter_candles(intervalo, quantidade=100):
    resposta = requests.get(
        URL,
        params={
            "symbol": "EUR/USD",
            "interval": intervalo,
            "outputsize": quantidade,
            "apikey": API_KEY
        },
        timeout=30
    )

    resposta.raise_for_status()
    dados = resposta.json()

    if "values" not in dados:
        raise Exception(f"Erro Twelve Data: {dados}")

    return list(reversed(dados["values"]))


def calcular_ema(valores, periodo):
    ema = sum(valores[:periodo]) / periodo
    fator = 2 / (periodo + 1)

    for valor in valores[periodo:]:
        ema = valor * fator + ema * (1 - fator)

    return ema


def tendencia(candles):
    fechamentos = [
        float(c["close"])
        for c in candles[:-1]
    ]

    if len(fechamentos) < 22:
        return "NEUTRO"

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


def enviar_telegram(texto):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram não configurado.")
        return

    resposta = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": texto
        },
        timeout=30
    )

    resposta.raise_for_status()
    print("Mensagem enviada ao Telegram!")


def carregar_historico():
    if not os.path.exists(ARQUIVO):
        return {"sinais": []}

    with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_historico(historico):
    with open(ARQUIVO, "w", encoding="utf-8") as arquivo:
        json.dump(
            historico,
            arquivo,
            indent=2,
            ensure_ascii=False
        )


def avaliar_pendentes(historico, candles1):
    alterou = False

    for sinal in historico["sinais"]:
        if sinal["resultado"] != "PENDENTE":
            continue

        entrada_hora = datetime.strptime(
            sinal["horario_candle"],
            "%Y-%m-%d %H:%M:%S"
        )

        hora_saida = entrada_hora + timedelta(minutes=5)

        candle_saida = None

        for candle in candles1:
            hora_candle = datetime.strptime(
                candle["datetime"],
                "%Y-%m-%d %H:%M:%S"
            )

            if hora_candle >= hora_saida:
                candle_saida = candle
                break

        if candle_saida is None:
            continue

        entrada = float(sinal["entrada"])
        saida = float(candle_saida["close"])

        if sinal["direcao"] == "CALL":
            resultado = "ACERTO" if saida > entrada else "ERRO"
        else:
            resultado = "ACERTO" if saida < entrada else "ERRO"

        sinal["saida"] = saida
        sinal["resultado"] = resultado
        sinal["horario_saida"] = candle_saida["datetime"]

        print(
            f"Resultado simulado: {resultado} | "
            f"Entrada: {entrada} | Saída: {saida}"
        )

        enviar_telegram(
            "📊 RESULTADO SIMULADO\n"
            f"EUR/USD: {sinal['direcao']}\n"
            f"Entrada: {entrada}\n"
            f"Saída: {saida}\n"
            f"Resultado: {resultado}"
        )

        alterou = True

    return alterou


def gerar_relatorio(historico):
    sinais = historico["sinais"]

    acertos = sum(
        s["resultado"] == "ACERTO" for s in sinais
    )

    erros = sum(
        s["resultado"] == "ERRO" for s in sinais
    )

    total = acertos + erros

    percentual = (
        (acertos / total) * 100
        if total > 0 else 0
    )

    return (
        "📈 DESEMPENHO SIMULADO\n"
        f"Sinais avaliados: {total}\n"
        f"Acertos: {acertos}\n"
        f"Erros: {erros}\n"
        f"Taxa de acerto: {percentual:.1f}%"
    )


def salvar_no_github():
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN não configurado.")
        return

    subprocess.run(
        ["git", "config", "user.name", "Robo de Sinais"],
        check=True
    )

    subprocess.run(
        ["git", "config", "user.email", "bot@github.com"],
        check=True
    )

    subprocess.run(["git", "add", ARQUIVO], check=True)

    resultado = subprocess.run(
        ["git", "diff", "--cached", "--quiet"]
    )

    if resultado.returncode == 0:
        print("Histórico sem alterações.")
        return

    subprocess.run(
        ["git", "commit", "-m", "Atualizar histórico de sinais"],
        check=True
    )

    subprocess.run(["git", "push"], check=True)

    print("Histórico salvo no GitHub!")


def executar():
    candles5 = obter_candles("5min")
    candles1 = obter_candles("1min")

    direcao5 = tendencia(candles5)
    direcao1 = tendencia(candles1)

    print("Tendência 5m:", direcao5)
    print("Tendência 1m:", direcao1)

    historico = carregar_historico()

    avaliar_pendentes(historico, candles1)

    if direcao5 == "ALTA" and direcao1 == "ALTA":
        sinal = "CALL"
    elif direcao5 == "BAIXA" and direcao1 == "BAIXA":
        sinal = "PUT"
    else:
        sinal = "AGUARDAR"

    candle_sinal = candles5[-2]
    horario_candle = candle_sinal["datetime"]
    entrada = float(candle_sinal["close"])

    existe = any(
        s["horario_candle"] == horario_candle
        for s in historico["sinais"]
    )

    if sinal != "AGUARDAR" and not existe:
        historico["sinais"].append({
            "direcao": sinal,
            "horario_candle": horario_candle,
            "entrada": entrada,
            "resultado": "PENDENTE"
        })

        enviar_telegram(
            "🚨 NOVO SINAL EXPERIMENTAL\n"
            f"Ativo: EUR/USD\n"
            f"Direção: {sinal}\n"
            f"Entrada de referência: {entrada}\n"
            f"Candle: {horario_candle}\n"
            "Expiração simulada: 5 minutos"
        )

    salvar_historico(historico)

    print(gerar_relatorio(historico))

    salvar_no_github()


if __name__ == "__main__":
    try:
        executar()
    except Exception as erro:
        print("ERRO NO ROBO:", erro)
