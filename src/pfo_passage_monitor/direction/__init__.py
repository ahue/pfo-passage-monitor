from typing import Dict, List


class DirectionStrategy(object):

  @staticmethod
  def get_direction(cpattern: List):
    return {
      "direction": None,
      "strategy": None
    }

class SimpleDirectionStrategy(DirectionStrategy): 
  """
  docstring
  """

  @staticmethod
  def get_direction(cpattern: List):
    return { 
      "direction": "out" if cpattern[0] == 1 else "in",
      "strategy": "simple" 
      }