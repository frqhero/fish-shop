import os
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
)


def start(update: Update, context: CallbackContext) -> None:
    """Sends a message with three inline buttons attached."""
    # response = requests.get(url, headers=headers)

    url = context.dispatcher.request_data['url']
    url = urljoin(url, '/api/')
    url = urljoin(url, '/product/')

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

    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    query.edit_message_text(text=f'Selected option: {query.data}')


def main():
    load_dotenv()

    request_data = {}
    strapi_token = os.getenv('STRAPI_TOKEN')
    request_data['host'] = 'http://localhost:1337'
    request_data['headers'] = {'Authorization': f'Bearer {strapi_token}'}

    token = os.getenv('TELEGRAM_TOKEN')
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.request_data = request_data
    dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
