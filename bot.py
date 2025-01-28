import logging
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Функция для получения списка песен, упорядоченного по ID
def get_song_all():
    conn = sqlite3.connect('ado.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, Namejp, Namerom FROM ado ORDER BY id")
    songs = cursor.fetchall()
    conn.close()
    return songs

# Функция для получения информации о песне (по названию или ID)
def get_song_info(song_title_or_id):
    conn = sqlite3.connect('ado.db')
    cursor = conn.cursor()

    # Проверка, является ли запрос числом (ID)
    if song_title_or_id.isdigit():
        query = "SELECT id, Namejp, Namerom, Data, Audio, Video, TranslationName, Other, LinkA, Album, LinkB FROM ado WHERE id = ?"
        cursor.execute(query, (song_title_or_id,))
    else:
        query = """SELECT id, Namejp, Namerom, Data, Audio, Video, TranslationName, Other, LinkA, Album, LinkB 
                   FROM ado 
                   WHERE Namerom LIKE ? OR Namejp LIKE ?"""
        cursor.execute(query, ('%' + song_title_or_id + '%', '%' + song_title_or_id + '%'))
    
    result = cursor.fetchone()
    conn.close()
    return result

# Асинхронный обработчик команды /start
async def start(update: Update, context: CallbackContext) -> None:
    logger.info('Received /start command')
    songs = get_song_all()
    # Формируем текст приветствия и список песен
    message = "Здравствуйте! Напишите номер или название песни Ado, и я предоставлю вам информацию о ней.\nСписок песен:\n"
    # Цикл для добавления песен в сообщение
    for song_id, namejp, namerom in songs:
        # Проверка на "-"
        if namerom == "-":
            message += f"{song_id}. {namejp}\n"
        else:
            message += f"{song_id}. {namejp} ({namerom})\n"
    await update.message.reply_text(message)

# Асинхронный обработчик текстовых сообщений
async def song_info(update: Update, context: CallbackContext) -> None:
    song_title_or_id = update.message.text.strip()
    logger.info(f'Received song request: {song_title_or_id}')
    song = get_song_info(song_title_or_id)
    if song:
        # Формируем основную информацию о песне
        response = f"Название: {song[1]}"
        if song[2] != "-":
            response += f" ({song[2]})"
        response += f"\nДата выхода: {song[3]}\nПеревод названия: {song[6]}"

        # Добавляем альбом, если он есть
        if song[9] != "-":
            response += f"\nАльбом: {song[9]}"

        # Добавляем дополнительные ссылки или текстовые блоки
        if song[7] != "-":
            response += f"\n\n{song[7]}"
        
        response += f"\n\nСсылки (YouTube)"

        # Добавляем ссылку, если она есть
        if song[8] != "-":
            response += f"\nMV: {song[8]}"
        
        if song[10] != "-":
            response += f"\nАудио: {song[10]}"

        await update.message.reply_text(response)

        # Отправка видео
        video_path = f"media/{song[5]}.mp4"
        try:
            logger.info(f'Sending video: {video_path}')
            await context.bot.send_video(chat_id=update.effective_chat.id, video=open(video_path, 'rb'))
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(video_path, 'rb'))
        except FileNotFoundError:
            logger.error(f'Video file not found: {video_path}')
            await update.message.reply_text("Видео не найдено.")
        
        # Отправка аудио
        audio_path = f"media/{song[4]}.mp3"
        try:
            logger.info(f'Sending audio: {audio_path}')
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(audio_path, 'rb'))
        except FileNotFoundError:
            logger.error(f'Audio file not found: {audio_path}')
            await update.message.reply_text("Аудио не найдено.")
    else:
        response = "Информация о песне не найдена."
        logger.info(f'Response: {response}')
        await update.message.reply_text(response)

def main() -> None:
    # Введите ваш токен API Telegram
    token = '7740603325:AAEZ6c2n9z26Nc9mO8fwWSQH2WXLP1F_Tmo'

    # Создание объекта Application и передача ему токена
    application = Application.builder().token(token).build()

    # Регистрация обработчиков команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, song_info))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()