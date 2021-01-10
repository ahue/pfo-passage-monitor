from pfo_passage_monitor.debugger import initialize_debugger_if_needed

initialize_debugger_if_needed()

import os
import logging

import connexion

from pfo_passage_monitor import util


util.load_config(os.getenv('PFO_CONF'))

util.logging_setup(util.config)

logger = logging.getLogger('pfo_passage_monitor')

logger.debug(os.getcwd())

# Create the application instance
app = connexion.App(__name__, specification_dir="./")

# Read the swagger.yml file to configure the endpoints
app.add_api('swagger.yml')

app = app.app # get the flasp app

# Create a URL route in our application for "/"
@app.route('/')
def home():
    """
    This function just responds to the browser ULR
    localhost:5000/
    :return:        the rendered template 'home.html'
    """
    return "Hello World!"