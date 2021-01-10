import pfo_passage_monitor.telegram.motion
import pfo_passage_monitor.telegram.passage
from pfo_passage_monitor import util
import logging


logger = logging.getLogger('pfo_passage_monitor')

def initialize():
  pass  

def catch_all(update, context):

  logger.debug(update)
  logger.debug(context)



  #motion.set_event_label(event_id, label)

  return update, context