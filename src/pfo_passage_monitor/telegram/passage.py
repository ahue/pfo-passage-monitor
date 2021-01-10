
import logging

import json
from telegram import Update
from telegram.ext import CallbackContext

from pfo_passage_monitor import passage
from pfo_passage_monitor import util

from pfo_passage_monitor.telegram import util as tg_util

logger = logging.getLogger('pfo_passage_monitor')


def set_label(update: Update, context: CallbackContext):

    logger.debug(update)
    logger.debug(context)

    data = json.loads(update.callback_query.data)

    label = "out" if data["l"] == 1 else "in"

    passage.set_passage_label(data["p"], {"key": "manual", "label": label})

    def button_handler(btn, label):
        check = "✔️"
        if json.loads(btn.callback_data)["l"] == label:
            btn.text += " "+check
        else:
            btn.text = btn.text.replace(check,"").strip()

        return btn

    update.effective_message.reply_markup.inline_keyboard = tg_util.update_inline_keybord(
        update.effective_message.reply_markup.inline_keyboard, 
        button_handler, label=data["l"])

    context.bot.edit_message_reply_markup(chat_id=update.effective_chat.id,
        message_id=update.effective_message.message_id,
        reply_markup=update.effective_message.reply_markup
        )

    return update, context