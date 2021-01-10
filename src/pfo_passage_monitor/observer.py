import logging

logger = logging.getLogger('pfo_passage_monitor')

class Observable(object):

  def __init__(self):
    self.__observers = []

  def registerObserver(self, observer):
    self.__observers.append(observer)
    
  def notifyObservers(self, *args, **kwargs):
    for observer in self.__observers:
      try:
        observer.notify(self, *args, **kwargs)
      except Exception as e:
        logger.error("Observer {0} failed notify: {1}".format(observer, str(e)))

class Observer(object):
  
  def __init__(self, observable):
    if(observable!=None):
      observable.registerObserver(self)

  def notify(self, observable, *args, **kwargs):
    logger.debug(f'Got {args} {kwargs} From, {observable}')
