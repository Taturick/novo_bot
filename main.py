import pandas as pd
import os
import time
from binance.client import Client
from binance.enums import *

# Configuração da API
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
    # Obter informações de filtros do símbolo
    info = cliente_binance.futures_exchange_info()
    for s in info['symbols']:
        if s['symbol'] == symbol:
            step_size = float([f['stepSize'] for f in s['filters'] if f['filterType'] == 'LOT_SIZE'][0])
            break
    else:
        raise ValueError(f"Símbolo {symbol} não encontrado.")

    # Ajustar quantidade para o múltiplo mais próximo do step_size
    quantidade_ajustada = (quantidade // step_size) * step_size
    return round(quantidade_ajustada, len(str(step_size).split('.')[1]))

# Função para calcular a quantidade com base no saldo
def calcular_quantidade(symbol, percentual_capital):
    # Obtém informações de saldo
    saldo = cliente_binance.futures_account_balance()
    saldo_disponivel = 0
    for item in saldo:
        if item['asset'] == 'USDT':  # Verifica o saldo em USDT
            saldo_disponivel = float(item['balance'])
            break

    if saldo_disponivel <= 0:
        raise Exception("Saldo insuficiente para operar.")
    
    # Calcula o valor a ser usado (50% do saldo disponível)
    valor_a_usar = saldo_disponivel * percentual_capital

    # Obtém o preço atual do ativo
    preco_atual = float(cliente_binance.futures_mark_price(symbol=symbol)['markPrice'])

    # Calcula a quantidade a ser operada
    quantidade = valor_a_usar / preco_atual
    return ajustar_quantidade(symbol, quantidade)  # Ajusta a precisão da quantidade

# Função principal para operar com cruzamento de médias
def operar_futuros_cruzamento():
    symbol = "NEIROUSDT"  # Par a ser operado
    leverage = 2          # Configurar alavancagem
    percentual_capital = 0.5  # Percentual do capital a ser utilizado (50%)
    
    # Configurar alavancagem
    cliente_binance.futures_change_leverage(symbol=symbol, leverage=leverage)

    posicao_atual = None  # Nenhuma posição inicialmente
    
    while True:
        try:
            # Buscar dados históricos (velas de 1 minuto)
            velas = cliente_binance.futures_klines(symbol=symbol, interval="1m", limit=50)
            
            # Verifique os dados das velas
            print(f"Respostas das velas: {velas}")  
            
            # Extrair os preços de fechamento
            fechamentos = [float(vela[4]) for vela in velas]  # Preços de fechamento
            
            # Verifique os preços de fechamento
            print(f"Fechamentos: {fechamentos}")  

            # Calcular médias móveis
            media_rapida = calcular_media(fechamentos, 9)   # Média móvel rápida (9 períodos)
            media_devagar = calcular_media(fechamentos, 25) # Média móvel devagar (25 períodos)

            # Exibição das médias
            print(f"Média Rápida: {media_rapida:.8f} | Média Devagar: {media_devagar:.8f}")
            
            # Calcula a quantidade com base no saldo
            quantidade = calcular_quantidade(symbol, percentual_capital)
            print(f"Quantidade calculada: {quantidade}")

            # Lógica de cruzamento de médias móveis
            if media_rapida > media_devagar and posicao_atual != "long":
                # Fechar posição short, se existir
                if posicao_atual == "short":
                    cliente_binance.futures_create_order(
                        symbol=symbol,
                        side="BUY",
                        type="MARKET",
                        quantity=quantidade
                    )
                    print("Fechando posição SHORT.")
                
                # Abrir posição long
                cliente_binance.futures_create_order(
                    symbol=symbol,
                    side="BUY",
                    type="MARKET",
                    quantity=quantidade
                )
                print("Abrindo posição LONG.")
                posicao_atual = "long"
            
            elif media_rapida < media_devagar and posicao_atual != "short":
                # Fechar posição long, se existir
                if posicao_atual == "long":
                    cliente_binance.futures_create_order(
                        symbol=symbol,
                        side="SELL",
                        type="MARKET",
                        quantity=quantidade
                    )
                    print("Fechando posição LONG.")
                
                # Abrir posição short
                cliente_binance.futures_create_order(
                    symbol=symbol,
                    side="SELL",
                    type="MARKET",
                    quantity=quantidade
                )
                print("Abrindo posição SHORT.")
                posicao_atual = "short"
            
            else:
                print("Nenhuma mudança detectada. Mantendo posição atual.")

        except Exception as e:
            print(f"Erro durante a operação: {e}")

        # Aguarda 60 segundos antes da próxima análise
        time.sleep(60)

# Iniciar a operação
if __name__ == "__main__":
    operar_futuros_cruzamento()
