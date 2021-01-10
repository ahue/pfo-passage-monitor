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


from PIL import Image, ImageDraw

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

class Pattern:

    @staticmethod
    def compress(pattern_long):
        pattern_comp = []
        for i in pattern_long:
            if len(pattern_comp)==0 or pattern_comp[-1][0]!=i:
                pattern_comp.append([i,0])
            pattern_comp[-1][1]+=1
        pattern_comp_flat = [element for tupl in pattern_comp for element in tupl]
        return(pattern_comp_flat)
    
    @staticmethod
    def decompress(pattern_comp):
        pattern_decomp = list()
        for direction, ctr in zip(pattern_comp[0::2], pattern_comp[1::2]):
            for j in range(0,ctr):
                pattern_decomp.append(direction)
        
        return(pattern_decomp)
    
    @staticmethod
    def is_compressed(pattern):
        """
        There is a small chance that a pattern like
        1212121212121212 would be identified as compressed while not being
        """
        pot_dirs = np.array(pattern[::2])
        pot_cnts = np.array(pattern[1::2])

        if (len(set(pot_dirs) - set([0,1,2])) == 0 and
            len(pattern) % 2 == 0 and 
            np.all(pot_cnts > 0) and
            np.all(np.abs(np.diff(pot_dirs)) > 0)):
            return True
        
        if len(set(pattern) - set([0,1,2])) == 0:
            return False

        raise ValueError("Invalid pattern")

    @staticmethod
    def draw_image(pattern, size: Tuple[int, int]):
        
        def scale(x, min_x, max_x,  a, b):
            return (b-a) * (x-min_x) / (max_x-min_x) + a

        pat = pattern

        if not Pattern.is_compressed(pat):
            pat = Pattern.compress(pat)
        
        pat_len = np.sum(pat[1::2])
        
        with Image.new('RGB', (size[0], size[1])) as im:
            draw = ImageDraw.Draw(im)
            offset = 0

            for i in range(0, int(len(pat)/2)):

                seg_len = pat[i*2+1]
                sensor = pat[i*2]
                width_px = scale(seg_len, 0, pat_len, 0, size[0])
                
                xl = offset
                xr = xl + width_px if i < int(len(pat)/2-1) else size[0] # for the last segment, fill everything

                if sensor == 0:
                    fill = (255,255,255)
                else:
                    if sensor == 1: # sensor = out
                        fill = (255,102,99)
                    else: # sensor = in
                        fill = (11,57,84)
                
                draw.rectangle([xl,0,xr,im.size[1]], fill=fill)
                
                offset = xr

            return im
    
    @staticmethod
    def scale(pattern, length):
        """
        Expects a compressed pattern
        Streches the segments of a pattern to accumulate to a total given length
        """

        if not Pattern.is_compressed(pattern):
            raise ValueError("Expecting a compressed pattern")
        
        patarr = np.array(pattern) 
        logger.debug(patarr)
        psize = np.sum(pattern[1::2])

        normed = scale_to_interval(patarr[1::2], 0, psize, 0, length)
        normedi = np.round(normed).astype(int) # needed to later make it decompressable
        normedi[-1] += norm - sum(normedi) # correct rounding errors
        logger.debug(normedi)

        if sum(normedi) != norm:
            raise Exception("Normalized pattern does not match expected length")
        
        patarr[np.arange(1,len(patarr),2)] = normedi
        logger.debug(patarr)
        return(list(patarr))

