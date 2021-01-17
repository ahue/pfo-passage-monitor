from typing import Dict, List
from pfo_passage_monitor.models import Passage


class DirectionStrategy(object):

    def get_direction(passage: Passage):
        return {
            "direction": None,
            "strategy": None
        }

class SimpleDirectionStrategy(DirectionStrategy): 
    """
    docstring
    """

    def get_direction(passage: Passage):
        return { 
            "direction": "out" if passage.pattern[0] == 1 else "in",
            "strategy": "simple" 
          }

def calibrate(config):
    """
    Calibrates the model of the selected strategy
    """
    pass