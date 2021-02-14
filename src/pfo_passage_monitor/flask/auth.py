import logging
logger = logging.getLogger('pfo_passage_monitor')
from pfo_passage_monitor import util

def api_auth(apikey, required_scopes):

    if not apikey in util.config["http"]["api_keys"].keys():
        return None

    return {"sub": util.config["http"]["api_keys"][apikey]}