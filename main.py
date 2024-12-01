import pandas as pd
import os
import time
from binance.client import Client
from binance.enums import *
import threading

# Configuração da API Binance
api_key = os.getenv("KEY_BINANCE")
secret_key = os.getenv("SECRET_BINANCE")
cliente_binance = Client(api_key, secret_key)

# Função para calcular médias móveis
def calcular_media(dados, periodo):
    if len(dados) < periodo:
        return 0.00
    media = sum(dados[-periodo:]) / periodo
    return round(media, 8)

# Função para ajustar a quantidade com base no stepSize permitido
def ajustar_quantidade(symbol, quantidade):
    info = cliente_binance.futures_exchange_info()
    for s in info['symbols']:
        if s['symbol'] == symbol:
            step_size = float([f['stepSize'] for f in s['filters'] if f['filterType'] == 'LOT_SIZE'][0])
            break
    else:
        raise ValueError(f"Símbolo {symbol} não encontrado.")

    quantidade_ajustada = (quantidade // step_size) * step_size
    return round(quantidade_ajustada, len(str(step_size).split('.')[1]))

# Função para calcular a quantidade com base no saldo
def calcular_quantidade(symbol, percentual_capital):
    saldo = cliente_binance.futures_account_balance()
    saldo_disponivel = 0
    for item in saldo:
        if item['asset'] == 'USDT':
            saldo_disponivel = float(item['balance'])
            break

    if saldo_disponivel <= 0:
        raise Exception("Saldo insuficiente para operar.")
    
    valor_a_usar = saldo_disponivel * percentual_capital
    preco_atual = float(cliente_binance.futures_mark_price(symbol=symbol)['markPrice'])
    quantidade = valor_a_usar / preco_atual
    return ajustar_quantidade(symbol, quantidade)

# Função para operação de cruzamento de médias móveis
def operar_futuros_cruzamento(symbol="NEIROUSDT", leverage=2, percentual_capital=0.5):
    cliente_binance.futures_change_leverage(symbol=symbol, leverage=leverage)
    posicao_atual = None
    
    while True:
        try:
            velas = cliente_binance.futures_klines(symbol=symbol, interval="1m", limit=50)
            fechamentos = [float(vela[4]) for vela in velas]
            media_rapida = calcular_media(fechamentos, 9)
            media_devagar = calcular_media(fechamentos, 25)

            quantidade = calcular_quantidade(symbol, percentual_capital)

            if media_rapida > media_devagar and posicao_atual != "long":
                if posicao_atual == "short":
                    cliente_binance.futures_create_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantidade)
                cliente_binance.futures_create_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantidade)
                posicao_atual = "long"
            elif media_rapida < media_devagar and posicao_atual != "short":
                if posicao_atual == "long":
                    cliente_binance.futures_create_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantidade)
                cliente_binance.futures_create_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantidade)
                posicao_atual = "short"

        except Exception as e:
            print(f"Erro: {e}")

        time.sleep(60)
