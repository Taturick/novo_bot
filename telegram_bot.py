from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import os
import threading
from main import operar_futuros_cruzamento  # Importa a função de negociação do main.py

# Função para iniciar a operação em uma nova thread
async def start(update: Update, context: CallbackContext):
    # Aguarda o envio da mensagem
    await update.message.reply_text("Bot de negociação iniciado. Enviando ordens de acordo com cruzamento de médias móveis.")
    
    # Inicia a operação de negociação em uma nova thread
    threading.Thread(target=operar_futuros_cruzamento).start()

# Comando para parar a operação (não implementado neste exemplo)
async def stop(update: Update, context: CallbackContext):
    await update.message.reply_text("Operação parada.")
    # Lógica para parar a execução do bot de negociação pode ser implementada aqui.

# Função principal do bot do Telegram
def main():
    # Carregar o token do Telegram do arquivo .env
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Carrega o token do .env

    # Atualização para versão >= 20
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Comandos do Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))

    # Começa a escutar as mensagens
    application.run_polling()

if __name__ == "__main__":
    main()
