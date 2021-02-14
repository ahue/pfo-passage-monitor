import logging

from typing import Any, Dict, Union, Tuple

from pfo_passage_monitor.models import Passage
import pfo_passage_monitor.util as util 
import numpy as np
from copy import deepcopy

from PIL import Image, ImageDraw

logger = logging.getLogger('pfo_passage_monitor')

class Pattern:

    def __init__(self):

        self.checks_per_sec = None
        self.sequence = None

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
                width_px = util.scale_to_interval(seg_len, 0, pat_len, 0, size[0])
                
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
        Example input: [1,2,2,4], 12 --> [1,4,2,8] (recognize that 4 and 8 sum to 12)
        """

        if not Pattern.is_compressed(pattern):
            raise ValueError("Expecting a compressed pattern")
        
        patarr = np.array(pattern) 
        # logger.debug(patarr)
        psize = np.sum(pattern[1::2])

        normed = util.scale_to_interval(patarr[1::2], 0, psize, 0, length)
        normedi = np.round(normed).astype(int) # needed to later make it decompressable
        normedi[-1] += length - sum(normedi) # correct rounding errors
        # logger.debug(normedi)

        if sum(normedi) != length:
            raise Exception("Normalized pattern does not match expected length")
        
        patarr[np.arange(1,len(patarr),2)] = normedi
        # logger.debug(patarr)
        return(list(patarr))

def set_label(id, label):
    # with util.get_postgres_con(util.config) as con:

    with util.get_sa_session(util.config) as session:
        passage = session.query(Passage).get(id)
        doc = deepcopy(passage.doc)
        doc["direction"][label["key"]] = label["label"]
        passage.doc = doc
        session.commit()

    # sql = f"UPDATE passage SET doc = doc || '{{\"label.{label['key']}\":\"{label['label']}\"}}' WHERE id = %s"
    # with util.get_postgres_con(util.config) as con:
    #     cur = con.cursor()
    #     cur.execute(sql, (id,))
    #     con.commit()

def predict_label(id):
  pass