import logging
import base64

from pfo_passage_monitor.observer import Observer

from copy import deepcopy
from datetime import datetime, timezone
from dateutil import tz
import re
import os
import json
import time


from pfo_passage_monitor.util import Pattern
from pfo_passage_monitor import util

from pfo_passage_monitor.observer import Observer 

logger = logging.getLogger('pfo_passage_monitor')

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

class TelegramMotionObserver(Observer):

    def __init__(self, observable, bot):

        super(TelegramMotionObserver, self).__init__(observable)

        self.bot = bot

    def notify(self, observable, gif_path, meta, *args, **kwargs):

        cfg = util.config

        logger.info("Trying to publish via Telegram")

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

class MqttMotionObserver(Observer):

    def __init__(self, observable):

        super(MqttMotionObserver, self).__init__(observable)

    def notify(self, observable, *args, **kwargs):

        cfg = util.config

        logger.info("Trying to publish gif via MQTT")

        if (kwargs is not None and 
            kwargs.get('gif_path',None) is not None and
            kwargs.get('meta',None) is not None
            ):
            try:
                gif_path = kwargs['gif_path']
                meta = kwargs['meta']

                meta = {
                    "start": time.mktime(meta["start"].timetuple()),
                    "end": time.mktime(meta["end"].timetuple()),
                    "duration": str(meta["duration"]),
                    "event_id": meta["event_id"],
                    "id": meta["id"]
                }
                
                with open(gif_path, "rb") as gif:
                    imagestring = gif.read()
                    byteArray = bytearray(imagestring)

                mqtt_cfg = util.config["motion"]["observer"]["mqtt"]

                msgs = [
                    {
                        "topic": mqtt_cfg["topic_meta"],
                        "payload": json.dumps(meta),
                        "qos": mqtt_cfg['qos'],
                        "retain": mqtt_cfg['retain']
                    },
                    {
                        "topic": mqtt_cfg["topic_gif"],
                        "payload": byteArray,
                        "qos": mqtt_cfg['qos'],
                        "retain": mqtt_cfg['retain']
                    }

                ]

                util.mqtt_publish_multi(cfg, msgs)
                
            except Exception as e:
                logger.exception(f"Could not publish the gif via MQTT: \n{e}")
        else:
            logger.error(f"No gif was supplied to {self.__name__}")



