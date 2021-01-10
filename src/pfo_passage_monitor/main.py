import logging

from typing import Dict

import threading
import time

import typer

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

from watchdog.observers import Observer as FsObserver


from copy import deepcopy

from pfo_passage_monitor import __title__
from pfo_passage_monitor import __version__
from pfo_passage_monitor import util
from pfo_passage_monitor.petflap import PetflapMonitor
from pfo_passage_monitor.observer.mqtt_observer import MqttObserver
from pfo_passage_monitor.observer.pg_observer import PostgresObserver
from pfo_passage_monitor.observer.telegram_observer import TelegramObserver
from pfo_passage_monitor.direction import SimpleDirectionStrategy

from pfo_passage_monitor.motion import GifEventHandler
from pfo_passage_monitor.observer.motion import  TelegramMotionObserver
from pfo_passage_monitor.observer.motion import  MqttMotionObserver

import pfo_passage_monitor.telegram as pfo_telegram 

logger = logging.getLogger('pfo_passage_monitor')


app = typer.Typer(
    name='pfo_passage_monitor',
    help="Monitors the GPIO pins to detect passages")


def version_callback(version: bool):
    if version:
        typer.echo(f"{__title__} {__version__}")
        raise typer.Exit()


ConfigOption = typer.Option(
    ..., '-c', '--config', metavar='PATH', help="path to the program configuration")
VersionOption = typer.Option(
    None, '-v', '--version', callback=version_callback, is_eager=True,
    help="print the program version and exit")


@app.command()
def main(config_file: str = ConfigOption, version: bool = VersionOption):
    """
    This is the entry point of your command line application. The values of the CLI params that
    are passed to this application will show up als parameters to this function.

    This docstring is where you describe what your command line application does.
    Try running `python -m pfo_passage_monitor --help` to see how this shows up in the command line.
    """
    util.load_config(config_file)
    config = util.config
    util.logging_setup(config)
    logger.info("Looks like you're all set up. Let's get going!")

    direction_strat = None
    if config["direction"]["strategy"] == "simple":
        direction_strat = SimpleDirectionStrategy

    cfg = config["petflap"]

    monitor = PetflapMonitor(
        cfg["pins"],
        cfg["checks_per_sec"], 
        cfg["collect_time"],
        direction_strat,
        cfg["logging"]["waiting_state"]
        )

    # PostgresObserver(petflap)

    observer_args = {}
    if "telegram" in config.keys():
        updater = telegram_setup(deepcopy(config["telegram"]))
        observer_args["telegram"] = { "bot": updater.bot }
        config["observer"]["telegram"]["chats"] = config["telegram"]["chats"]

    observer_setup(deepcopy(config), monitor, observer_args)

    # monitor.run()

    run_event = threading.Event()
    run_event.set()

    t1 = threading.Thread(target = monitor.run, args = (run_event,))
    t1.start()
    logger.debug("Started GPIO Monitor")

    # Motion
    handler = GifEventHandler()
    tgmo = TelegramMotionObserver(handler, updater.bot)
    mqmo = MqttMotionObserver(handler)

    fs_observer = FsObserver()
    fs_observer.schedule(handler, 
        path=config["motion"]["event"]["gif_created"])
    fs_observer.start()
    logger.debug("Started Filesystem Watchdog")

    updater.start_polling()
    logger.debug("Started Telegram Updater")

    try:
        while 1:
            time.sleep(.1)
    except KeyboardInterrupt:
        logger.info("attempting to close threads.")
        run_event.clear()
        t1.join()
        fs_observer.stop()
        fs_observer.join()
        updater.stop()
        logger.info("threads successfully closed")


def telegram_setup(cfg: Dict):

    updater = Updater(cfg["token"])

    updater.dispatcher.add_handler(CallbackQueryHandler(callback=pfo_telegram.passage.set_label, pattern=r".+\"a\":\"ps_lbl\".+"))
    updater.dispatcher.add_handler(CallbackQueryHandler(callback=pfo_telegram.motion.set_label, pattern=r".+\"a\":\"mt_lbl\".+"))
    updater.dispatcher.add_handler(CallbackQueryHandler(callback=pfo_telegram.catch_all))

    return updater

def observer_setup(config: Dict, petflap: PetflapMonitor, args):

    observer_class_map = {"mqtt": MqttObserver,  
        "telegram": TelegramObserver}

    for k in config["observer"].keys():

        kwargs = {}
        if k in args:
            kwargs = args[k]

        obs = observer_class_map[k](petflap, config["observer"][k], **kwargs)



if __name__ == "__main__":
    app()
