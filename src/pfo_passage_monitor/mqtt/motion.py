import logging
import re
import os
import time
import json

from pfo_passage_monitor.observer import Observer
from pfo_passage_monitor import util 

logger = logging.getLogger('pfo_passage_monitor')

from copy import deepcopy
from datetime import datetime, timezone
from dateutil import tz

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