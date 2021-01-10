import logging

import pfo_passage_monitor.util as util 

logger = logging.getLogger('pfo_passage_monitor')


def set_label(id, label):
    # with util.get_postgres_con(util.config) as con:

    sql = f"UPDATE passage SET doc = doc || '{{\"label.{label['key']}\":\"{label['label']}\"}}' WHERE id = %s"
    with util.get_postgres_con(util.config) as con:
        cur = con.cursor()
        cur.execute(sql, (id,))
        con.commit()

def predict_label(id):
  pass