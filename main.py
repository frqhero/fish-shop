import os
import logging
from urllib.parse import urljoin

import redis
import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from telegram.ext import Filters, Updater, CallbackContext
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

_database = None


def start(update, context):
    """
    Хэндлер для состояния START.

    Бот отвечает пользователю фразой "Привет!" и переводит его в состояние ECHO.
    Теперь в ответ на его команды будет запускаеться хэндлер echo.
    """
    if update.message:
        message = update.message
    else:
        update.callback_query.answer()
        message = update.callback_query.message

    url = context.dispatcher.request_data['host']
    url = urljoin(url, '/api/')
    url = urljoin(url, 'products/')

    data = requests.get(
        url,
        headers=context.dispatcher.request_data['headers'],
    ).json()['data']

    keyboard = [
        [
            InlineKeyboardButton(
                product['attributes']['title'], callback_data=product['id']
            )
        ]
        for product in data
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    message.reply_text('Please choose:', reply_markup=reply_markup)
    return 'HANDLE_MENU'


def handle_menu(update: Update, context: CallbackContext):
    update.callback_query.answer()

    user_reply = update.callback_query.data

    host_url = context.dispatcher.request_data['host']
    headers = context.dispatcher.request_data['headers']

    detail_url = urljoin(host_url, '/api/')
    detail_url = urljoin(detail_url, 'products/')
    detail_url = urljoin(detail_url, user_reply)

    params = {'populate': 'picture'}
    data = requests.get(
        detail_url,
        headers=headers,
        params=params,
    ).json()['data']

    picture_url = data['attributes']['picture']['data']['attributes']['url']
    picture_url = urljoin(host_url, picture_url)

    content = requests.get(picture_url, headers=headers).content

    keyboard = [
        [InlineKeyboardButton('Добавить в корзину', callback_data='AddToCard')],
        [InlineKeyboardButton('Назад', callback_data='Back')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.message.reply_photo(
        content,
        data['attributes']['description'],
        reply_markup=reply_markup,
    )
    update.callback_query.message.delete()

    return 'HANDLE_DESCRIPTION'


def echo(update, context):
    """
    Хэндлер для состояния ECHO.

    Бот отвечает пользователю тем же, что пользователь ему написал.
    Оставляет пользователя в состоянии ECHO.
    """
    users_reply = update.message.text
    update.message.reply_text(users_reply)
    return 'ECHO'


def handle_description(update, context):
    return start(update, context)


def handle_users_reply(update, context):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode('utf-8')

    states_functions = {
        'START': start,
        'ECHO': echo,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
    }
    state_handler = states_functions[user_state]
    # Если вы вдруг не заметите, что python-telegram-bot перехватывает ошибки.
    # Оставляю этот try...except, чтобы код не падал молча.
    # Этот фрагмент можно переписать.
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
    """
    global _database
    if _database is None:
        database_password = os.getenv('DATABASE_PASSWORD')
        database_host = os.getenv('DATABASE_HOST')
        database_port = os.getenv('DATABASE_PORT')
        _database = redis.Redis(
            host=database_host, port=database_port, password=database_password
        )
    return _database


if __name__ == '__main__':
    load_dotenv()

    request_data = {}
    strapi_token = os.getenv('STRAPI_TOKEN')
    request_data['host'] = 'http://localhost:1337'
    request_data['headers'] = {'Authorization': f'Bearer {strapi_token}'}

    token = os.getenv('TELEGRAM_TOKEN')
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.request_data = request_data
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()
    updater.idle()
