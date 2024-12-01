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

# Variável global para controlar a thread
operacao_ativa = True  # A operação vai ser iniciada automaticamente

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
        return 0  # Retorna 0 se não houver saldo suficiente

    valor_a_usar = saldo_disponivel * percentual_capital
    preco_atual = float(cliente_binance.futures_mark_price(symbol=symbol)['markPrice'])

    if preco_atual <= 0:
        raise ValueError("O preço atual do ativo é inválido (menor ou igual a zero).")

    quantidade = valor_a_usar / preco_atual

    if quantidade <= 0:
        return 0  # Retorna 0 se a quantidade for inválida

    return ajustar_quantidade(symbol, quantidade)

# Função para operação de cruzamento de médias móveis
def operar_futuros_cruzamento(symbol="NEIROUSDT", leverage=2, percentual_capital=0.5):
    global operacao_ativa
    cliente_binance.futures_change_leverage(symbol=symbol, leverage=leverage)
    posicao_atual = None

    while operacao_ativa:
        try:
            # Obtendo as velas e calculando as médias móveis
            velas = cliente_binance.futures_klines(symbol=symbol, interval="1m", limit=50)
            fechamentos = [float(vela[4]) for vela in velas]
            media_rapida = calcular_media(fechamentos, 9)
            media_devagar = calcular_media(fechamentos, 25)
            preco_atual = fechamentos[-1]

            # Exibindo os logs das médias móveis e do preço atual
            print(f"Preço Atual: {preco_atual}")
            print(f"Média Rápida (9): {media_rapida}")
            print(f"Média Devagar (25): {media_devagar}")

            # Calculando a quantidade a ser comprada/vendida
            quantidade = calcular_quantidade(symbol, percentual_capital)

            if quantidade == 0:
                # Se não houver saldo suficiente, aguarda e continua verificando
                print("Saldo insuficiente, aguardando para tentar novamente...")
                time.sleep(60)  # Aguardar antes de tentar novamente
                continue  # Retorna ao início do loop

            # Log das operações
            if media_rapida > media_devagar and posicao_atual != "long":
                if posicao_atual == "short":
                    cliente_binance.futures_create_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantidade)
                    print(f"Fechando posição SHORT e comprando LONG: {quantidade} {symbol}")
                cliente_binance.futures_create_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantidade)
                print(f"Comprando LONG: {quantidade} {symbol}")
                posicao_atual = "long"

            elif media_rapida < media_devagar and posicao_atual != "short":
                if posicao_atual == "long":
                    cliente_binance.futures_create_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantidade)
                    print(f"Fechando posição LONG e vendendo SHORT: {quantidade} {symbol}")
                cliente_binance.futures_create_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantidade)
                print(f"Vendendo SHORT: {quantidade} {symbol}")
                posicao_atual = "short"

        except Exception as e:
            print(f"Erro: {e}")

        time.sleep(60)

# Função principal
def main():
    print("Iniciando o script...")

    # Iniciar a operação em uma nova thread sem depender de comandos do Telegram
    threading.Thread(target=operar_futuros_cruzamento).start()

if __name__ == "__main__":
    main()
