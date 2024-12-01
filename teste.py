import asyncio
from telegram import Bot

async def main():
    bot = Bot(token="7378271512:AAGZ-jBVzw6dzQHOm6HaIqS89hwoW8BuKVk")
    chat_id = 1948928184  # Substitua com o seu chat_id pessoal
    await bot.send_message(chat_id=chat_id, text="Teste de comunicação com o bot!")

asyncio.run(main())
