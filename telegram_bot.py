from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import os
import threading
from main import operar_futuros_cruzamento  # Importa a função de negociação do main.py

# Função para iniciar a operação em uma nova thread
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Bot de negociação iniciado. Enviando ordens de acordo com cruzamento de médias móveis.")
    
    # Inicia a operação de negociação em uma nova thread
    threading.Thread(target=operar_futuros_cruzamento).start()

# Comando para parar a operação (não implementado neste exemplo)
def stop(update: Update, context: CallbackContext):
    update.message.reply_text("Operação parada.")
    # Lógica para parar a execução do bot de negociação pode ser implementada aqui.

# Função principal do bot do Telegram
def main():
    # Carregar o token do Telegram do arquivo .env
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Carrega o token do .env

    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Comandos do Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))

    updater.start_polling()
    updater.idle()
