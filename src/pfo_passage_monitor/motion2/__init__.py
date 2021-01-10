import logging


from watchdog.events import FileSystemEventHandler

logger = logging.getLogger('pfo_passage_monitor')


class TelegramEventHandler(FileSystemEventHandler):

    def on_created(self, event):
