import logging

import psycopg2
from copy import deepcopy
import json

from pfo_passage_monitor.observer import Observer
import pfo_passage_monitor.util as util


logger = logging.getLogger('pfo_passage_monitor')

class PostgresObserver(Observer):

    def __init__(self, observable):

        super(PostgresObserver, self).__init__(observable)

    def notify(self, observable, *args, **kwargs):

        logger.info("Trying store passage in Postgres")

        if kwargs is not None and kwargs.get('doc',None) is not None:
            try:
                doc = deepcopy(kwargs['doc'])
                #doc["pattern"] = catflap_pattern.compress(doc["pattern"])

                with util.get_postgres_con(util.config) as con:
                    sql = "INSERT INTO passage (doc, start) VALUES (%s, %s)"
                    cur = con.cursor()
                    cur.execute(sql, (json.dumps(doc), doc["start"]))
                    con.commit()
                    logger.info("Passage stored in Postgres")

            except Exception as e:
                logger.error(f"Could not store doc: \n{e}")
        else:
            logger.error(f"No document was supplied to {PostgresObserver.__name__}")




