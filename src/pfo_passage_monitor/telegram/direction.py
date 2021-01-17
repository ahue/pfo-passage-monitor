import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from pfo_passage_monitor import util
from pfo_passage_monitor.direction import nnet

logger = logging.getLogger('pfo_passage_monitor')


def fit_model(update: Update, context: CallbackContext):

    logger.debug(update)
    logger.debug(context)

    nnet.update({})