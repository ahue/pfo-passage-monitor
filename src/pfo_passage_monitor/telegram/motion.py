import logging

import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from pfo_passage_monitor import motion
from pfo_passage_monitor import util
from pfo_passage_monitor.observer import Observer

from copy import deepcopy
from datetime import datetime, timezone
from dateutil import tz
import re
import os
import time

logger = logging.getLogger('pfo_passage_monitor')

class TelegramMotionObserver(Observer):

    def __init__(self, observable, bot):

        super(TelegramMotionObserver, self).__init__(observable)

        self.bot = bot

    def notify(self, observable, gif_path, meta, *args, **kwargs):

        cfg = util.config

        logger.info("Trying to motion publish via Telegram")

        if (gif_path is not None and 
            meta is not None):
            try:
                # gif_path = gif_path
                # meta = meta

                reply_markup = InlineKeyboardMarkup(inline_keyboard  = util.split_list([
                    InlineKeyboardButton(text=pet,
                        callback_data=util.json_dumps_compressed({"a": "mt_lbl", # action
                        "m": int(meta["id"]), # event_id
                        "l": i})) for i, pet in enumerate(util.config["pets"])] +
                    [InlineKeyboardButton(text=u"Fehlalarm",
                        callback_data=util.json_dumps_compressed({"a": "mt_lbl",
                        "m": int(meta["id"]),
                        "l": -1})),
                    ],2,True))
                
                for chat in cfg["telegram"]["chats"]:

                    self.bot.sendAnimation(chat_id=chat, animation=open(gif_path, "rb"),
                        parse_mode="Markdown",
                        reply_markup = reply_markup, 
                        caption=f"Bewegung wurde am {meta['start'].strftime('%a, %-d.%-m, %-H:%M')} Uhr aufgezeichnet und dauerte {meta['duration']}"
                        # duration_text
                    )
                
            except Exception as e:
                logger.error(f"Could not publish the gif via Telegram: \n{e}")
        else:
            logger.error(f"No gif was supplied to {self}")

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