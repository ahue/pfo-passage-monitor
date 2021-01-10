import logging
import os
import traceback 
import psycopg2.extras

import pfo_passage_monitor.util as util 
from watchdog.events import FileSystemEventHandler
from pfo_passage_monitor.observer import Observable


logger = logging.getLogger('pfo_passage_monitor')


class GifEventHandler(FileSystemEventHandler, Observable):

    def __init__(self):

        FileSystemEventHandler.__init__(self)
        Observable.__init__(self)

    def on_modified(self, event):

        cfg = util.config
        try:
            with open(event.src_path, "r") as gif_created:
                ts = gif_created.read().strip()
        
            if ts == "":
                return

            fn = os.path.join(cfg["motion"]["gif_dir"], f"{ts}.gif")

            with util.get_postgres_con(util.config) as con:
                sql = "SELECT * FROM motion_start_end WHERE event_id = %s"
                cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cur.execute(sql, (ts,))
                row = cur.fetchone()
                
            # with open(fn, "rb") as gif:

            self.notifyObservers(gif_path=fn, meta = {
                "start": row["ts_start"],
                "end": row["ts_end"],
                "duration": row["duration"],
                "event_id": ts,
                "id": row["id"]
            })
    
        except Exception as e:
            logger.error(traceback.print_exc())

        # logger.debug(f"{event.src_path}")

def set_event_label(id, label):
    # with util.get_postgres_con(util.config) as con:

    sql = f"UPDATE motion SET doc = doc || '{{\"label.{label['key']}\":\"{label['label']}\"}}' WHERE id = %s"
    with util.get_postgres_con(util.config) as con:
        cur = con.cursor()
        cur.execute(sql, (id,))
        con.commit()
