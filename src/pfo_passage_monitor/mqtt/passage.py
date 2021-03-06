import paho.mqtt.client as mqtt
import time
import datetime
import logging
from pfo_passage_monitor.observer import Observer
from pfo_passage_monitor import util 
import copy
import json

from pfo_passage_monitor.models import Passage


ha_sensor_cfg = {
    "timestamp": {
        "unit_of_measurement": "ms",
        "value_template": "{{ value_json.timestamp }}",
        "state_topic": "duseltron/mika/catflap/passage",
        "name": "catflap_passage_timestamp",
        "device": {
            "name": "catflap",
            "model": "Petflap",
            "manufacturer": "Sureflap"
        },
    },
    "direction": {
        "value_template": "{% if value_json.pattern[0] == 2 %} Mika ist raus {% else %} Mika ist rein {% endif %}"
    }
}

logger = logging.getLogger('pfo_passage_monitor')

class MqttPassageObserver(Observer):

    def __init__(self, observable, mqtt_config):

        super(MqttPassageObserver, self).__init__(observable)

        self.mqtt_config = mqtt_config

    def notify(self, observable, passage: Passage, *args, **kwargs):

        logger.info("Trying to publish via MQTT")

        if passage is not None and passage.doc is not None:
            try:
                doc = copy.deepcopy(passage.doc)
                #doc["pattern"] = catflap_pattern.compress(doc["pattern"])
                res = self.publish_doc(doc)
                logger.debug("MQTT response: {}, {}".format(res[0], res[1]))
                logger.info("Passage published via MQTT")
            except Exception as e:
                logger.exception(f"Could not publish the doc: \n{e}")
        else:
            logger.error(f"No document was supplied to {MqttObserver.__name__}")

    def publish_doc(self, doc):

        cfg = util.config

        with util.get_mqtt_client(cfg) as client:
            mqtt_cfg = cfg["observer"]["mqtt"]
            res = client.publish(mqtt_cfg["topic"], payload=json.dumps(doc), 
                qos=mqtt_cfg['qos'], retain=mqtt_cfg['retain'])
        
        return res