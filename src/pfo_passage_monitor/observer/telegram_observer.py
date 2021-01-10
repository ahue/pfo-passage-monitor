import logging

from pfo_passage_monitor.observer import Observer

from copy import deepcopy
from datetime import datetime, timezone
from dateutil import tz
import re
import os

from pfo_passage_monitor.util import Pattern
from pfo_passage_monitor import util

from pfo_passage_monitor.observer import Observer 

from telegram import InlineKeyboardMarkup, InlineKeyboardButton


logger = logging.getLogger('pfo_passage_monitor')


class TelegramObserver(Observer):

    def __init__(self, observable, config, bot):

        super(TelegramObserver, self).__init__(observable)

        self.config = config
        self.bot = bot

    def notify(self, observable, *args, **kwargs):

        cfg = self.config

        logger.info("Trying to publish via Telegram")

        if kwargs is not None and kwargs.get('doc',None) is not None:
            try:
                doc = deepcopy(kwargs['doc'])
                
                img = Pattern.draw_image(doc["pattern"], 
                    size=(cfg["image"]["width"], cfg["image"]["height"]))

                im_dir = cfg["image"]["directory"]
                im_fn = f"{doc['start']}.png"
                os.makedirs(im_dir, exist_ok=True)
                im_path = os.path.join(im_dir, im_fn)
                img.save(im_path, "PNG")

                pet_name = "Mika"
                if doc["direction"]["direction"] == "in":
                    msg = cfg["message"]["text_in"].format(pet_name = pet_name)
                else:
                    msg = cfg["message"]["text_out"].format(pet_name = pet_name)

                if cfg["message"]["show_time"]:
                    to_zone = tz.gettz() #tz.gettz(cfg["timezone"])
                    start = datetime.fromtimestamp(doc["start"], timezone.utc).astimezone(to_zone)
                    msg += "\n"
                    msg += "Es ist {} Uhr.".format(start.strftime("%a, %-d.%-m, %-H:%M"))  

                reply_markup = InlineKeyboardMarkup(inline_keyboard  = [[
                    InlineKeyboardButton(text="rein",
                        callback_data=util.json_dumps_compressed({"a": "ps_lbl", # action
                        "p": int(doc["id"]), 
                        "l": 2})),
                    InlineKeyboardButton(text="raus",
                        callback_data=util.json_dumps_compressed({"a": "ps_lbl", # action
                        "p": int(doc["id"]), 
                        "l": 1})),
                    InlineKeyboardButton(text=u"Fehlalarm",
                        callback_data=util.json_dumps_compressed({"a": "ps_lbl",
                        "p": int(doc["id"]),
                        "l": -1})),
                    ]])


                for chat in self.config["chats"]:
                    if re.match(r"^[a-zA-Z].+", str(chat)):
                        chat = "@" + chat

                    self.bot.send_photo(chat_id = chat,
                        photo=open(im_path, "rb"),
                        caption=msg,
                        reply_markup=reply_markup,
                        parse_mode="Markdown")

                    logger.info(f"Sent message to {chat}")
                
            except Exception as e:
                logger.exception(f"Could not publish the doc: \n{e}")
        else:
            logger.error(f"No document was supplied to {TelegramObserver.__name__}")





