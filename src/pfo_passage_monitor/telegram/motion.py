import logging

import json
from telegram import Update
from telegram.ext import CallbackContext

from pfo_passage_monitor import motion
from pfo_passage_monitor import util




logger = logging.getLogger('pfo_passage_monitor')


def set_label(update: Update, context: CallbackContext):

    logger.debug(update)
    logger.debug(context)

    data = json.loads(update.callback_query.data)

    label = util.config["pets"][data["l"]] if data["l"] > -1 else "invalid"
    # TODO: make sure the id is used instead of event_id
    motion.set_event_label(data["m"], {"key": "manual", "label": label})

    reply_markup = update.effective_message.reply_markup

    kb = reply_markup.inline_keyboard

    check = "✔️"
    for i, row in enumerate(kb):
        for j, _ in enumerate(row):
            if json.loads(kb[i][j].callback_data)["l"] == data["l"]:
                kb[i][j].text += " "+check
            else:
                kb[i][j].text = kb[i][j].text.replace(check,"").strip()

    reply_markup.inline_keyboard = kb

    context.bot.edit_message_reply_markup(chat_id=update.effective_chat.id,
        message_id=update.effective_message.message_id,
        reply_markup=update.effective_message.reply_markup
        )

    return update, context