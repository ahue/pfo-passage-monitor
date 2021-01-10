import logging
from pathlib import Path
from typing import Any, Dict, Union, Tuple

import pkg_resources
import yaml
import numpy as np
import json
import re

import psycopg2
import paho.mqtt.client as mqtt
import paho.mqtt.publish as mqtt_publish
from contextlib import contextmanager


import sqlalchemy as sa
from sqlalchemy.orm import scoped_session, sessionmaker


logger = logging.getLogger('pfo_passage_monitor')

config = {}

def get_config():
    return config

def get_resource_string(path: str, decode=True) -> Union[str, bytes]:
    """
    Load a package resource (i.e. a file from within this package)

    :param path: the path, starting at the root of the current module (e.g. 'res/default.conf').
           must be a string, not a Path object!
    :param decode: if true, decode the file contents as string (otherwise return bytes)
    :return: the contents of the resource file (as string or bytes)
    """
    s = pkg_resources.resource_string(__name__.split('.')[0], path)
    return s.decode(errors='ignore') if decode else s

def split_list(data, chunk_size, try_harmonic=False):
    """
    Splits a list [1,2,3,4,5,6] into multiple sub-lists of size chunk_size
    example: chunk_size = 4 --> [[1,2,3,4],[5,6]]
    if harmonig=True, it tries to find the largest 0 < size < chunk_size that results in equally sized chunks
    """
    def primes(n):
        primfac = []
        d = 2
        while d*d <= n:
            while (n % d) == 0:
                primfac.append(d)  # supposing you want multiple factors repeated
                n //= d
            d += 1
        if n > 1:
            primfac.append(n)
        return primfac
    if try_harmonic and len(data) % chunk_size != 0:
        primes_arr = np.array(primes(len(data)))
        mask =  (primes_arr <= chunk_size) & (primes_arr > 1)
        if np.any(mask):
            chunk_size = max(primes_arr[mask])        
    chunks = [data[x:x+chunk_size] for x in range(0, len(data), chunk_size)]
    return chunks

def load_config(config_file: Union[str, Path]) -> Dict[str, Any]:
    """
    Load the config from the specified yaml file

    :param config_file: path of the config file to load
    :return: the parsed config as dictionary
    """
    global config
    with open(config_file, 'r') as fp:
        config = yaml.safe_load(fp)

def get_postgres_con(cfg):

    con = psycopg2.connect(host=cfg["postgres"]["host"],
                    database=cfg["postgres"]["database"], 
                    user=cfg["postgres"]["user"], 
                    password=cfg["postgres"]["password"], 
                    port=cfg["postgres"]["port"])

    return con

@contextmanager
def get_mqtt_client(cfg):

    client = mqtt.Client()
    # client.tls_set("/home/pi/mosquitto/ca.crt")
    if "user" in cfg["mqtt"].keys():
        client.username_pw_set(cfg["mqtt"]["user"], cfg["mqtt"]["password"])

    client.connect(cfg["mqtt"]["host"], cfg["mqtt"]["port"], 60)
    try:
        yield client
    finally:
        client.disconnect()
    # return client

def mqtt_publish_multi(cfg, msgs):

    return mqtt_publish.multiple(msgs, hostname=cfg["mqtt"]["host"], 
        port=cfg["mqtt"]["port"], 
        auth={
            "username": cfg["mqtt"]["user"], 
            "password":cfg["mqtt"]["password"]
        })

def json_dumps_compressed(dct: Dict):
    """
    returns json dumps without spaces (needed for telegram callback data)
    """

    return json.dumps(dct, separators=(',', ':'))



def logging_setup(config: Dict):
    """
    setup logging based on the configuration


    :param config: the parsed config tree
    """
    log_conf = config['logging']
    fmt = log_conf['format']
    if log_conf['enabled']:
        level = logging._nameToLevel[log_conf['level'].upper()]
    else:
        level = logging.NOTSET
    logging.basicConfig(format=fmt, level=logging.WARNING)
    logger.setLevel(level)

def scale(x, max_x, norm): 
    """
    Scales a values of x from interval [0, psize] to [0, norm]
    """
    return scale_to_interval(x, 0, max_x, 0, norm)
    # scaled = ((norm - 0) * (x - 0)) / (psize - 0) + 0
    # return scaled

def scale_to_interval(x, min_x, max_x,  a, b):
    """
    Scales a value of x from interval [min_x,max_x] to a target interval [a,b]
    """
    return (b-a) * (x-min_x) / (max_x-min_x) + a

@contextmanager
def get_sa_session(config):

    pgc = config["postgres"]
    engine = sa.create_engine(f'postgresql://{pgc["user"]}:{pgc["password"]}@{pgc["host"]}:{pgc["port"]}/{pgc["database"]}')
    session = scoped_session(sessionmaker(bind=engine))

    try:
        yield session
    finally:
        session.close()