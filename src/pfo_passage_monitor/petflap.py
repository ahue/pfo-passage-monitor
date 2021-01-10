import sys, os
import time
from datetime import datetime
# from pytz import timezone
import RPi.GPIO as io
import logging
#import couchdb
import numpy as np
import json
import psycopg2.extras


from pfo_passage_monitor.observer import Observable
from pfo_passage_monitor.util import Pattern
from pfo_passage_monitor import util
from pfo_passage_monitor.direction import DirectionStrategy

logger = logging.getLogger('pfo_passage_monitor')

class PetflapMonitor(Observable):

    STATE_WAITING = 1
    STATE_COLLECTING = 2
    STATE_COOLDOWN = 3

    def __init__(self, pins, checks_per_sec, collect_time, direction_strat: DirectionStrategy, report_time = 60):

        super(PetflapMonitor, self).__init__()

        # number of checks per second
        self.checks_per_sec = checks_per_sec 
        # number of seconds the programm shall remain in collectin state
        # if no sensor is triggered
        self.collect_time = collect_time # in seconds
        # how often shall the programm report the waiting state
        self.report_time = report_time # in seconds

        self.pin_in = pins["in"]
        self.pin_out = pins["out"]

        self.direction_strat = direction_strat

        # # Set up logging
        # log_file = "./door_sensor.log"
        # # clear the log
        # #with open(log_file, 'w'):
        # #    pass
        # formatter = logging.Formatter(fmt="%(asctime)s|%(levelname)s|%(filename)s:%(lineno)d|%(message)s",
        #     datefmt="%y%m%d %H:%M:%S")

        # logging.basicConfig(filename=log_file,
        #     level=logging.DEBUG,
        #     format="%(asctime)s|%(levelname)s|%(filename)s:%(lineno)d|%(message)s",
        #     datefmt="%y%m%d %H:%M:%S")
        # console_logger = logging.StreamHandler()
        # console_logger.setFormatter(formatter)

        # logging.getLogger('').addHandler(console_logger)

        # logging.info("Starting up Katzenklappen-logger")

    def run(self, run_event):

        io.setmode(io.BCM)

        # ExtB -> GPIO
        # P0 = 17
        # P1 = 18
        # P2 = 27
        # P3 = 22
        # P4 = 23
        # P5 = 24
        # P6 = 25
        # P7 = 4

        door1_pin = self.pin_out #24 # outer sensor
        door2_pin = self.pin_in #4 # inner sensor

        io.setup(door1_pin, io.IN, pull_up_down=io.PUD_UP)  # active input with pullup
        io.setup(door2_pin, io.IN, pull_up_down=io.PUD_UP)  # active input with pullup

        # the amount of time two wait between two iterations
        sleep_time = 1/float(self.checks_per_sec) 
        # the timestamp when entereing (or renewing) the collection state
        collect_time_start = 0
        last_sensor_reading = 0
        # the timestamp of the last report
        report_last_time = 0

        # Set the initial state
        state = self.STATE_WAITING
        # coll = list() # collector for the raw pattern (could lead to memory excess)
        # coll2 = [] # collector for an already compressed pattern (saves memory)
        coll3 = []
        prev_state = [2,2]
        #try:
        while run_event.is_set():

            # Compute everything in UTC
            ts = time.time() 
            io_state1 = io.input(door1_pin) # outer sensor
            io_state2 = io.input(door2_pin) # inner sensor

            # Debugging - logger sensor state changes
            if sum([abs(a-b) for a,b in zip(prev_state, [io_state1, io_state2])])>0:
                logger.debug("sensors %s, %s", io_state1, io_state2)    

            prev_state = [io_state1, io_state2]

            # The waiting state repeatedly checks the
            # sensors and activates collecting state whenever
            # any of the sensors fires
            if state == self.STATE_WAITING:
                if ts - report_last_time > self.report_time:
                    report_last_time = ts

                    # Timestamp experiment
                    # test_dtn = datetime.now()
                    # test_time = time.time()
                    # test_utcnow = datetime.utcnow()
                    # test_utcman = datetime.now(timezone("UTC"))

                    logger.debug("waiting")
                    # logger.info("use ts: " + str(int(ts)) + " | " + datetime.fromtimestamp(ts).replace(tzinfo=timezone("UTC")).astimezone(timezone('Europe/Berlin')).isoformat()) 
                    # logger.info("us2 ts: " + str(int(ts)) + " | " + datetime.fromtimestamp(ts).replace(tzinfo=timezone('Europe/Berlin')).isoformat()) 
                    # logger.info("dtn ts: " + str(int(time.mktime(test_dtn.timetuple()))) + " | " + test_dtn.isoformat())
                    # logger.info("tim ts: " + str(int(test_time)) + " | " + datetime.fromtimestamp(test_time).replace(tzinfo=timezone("UTC")).astimezone(timezone('Europe/Berlin')).isoformat())
                    # logger.info("utcnow: " + str(int(time.mktime(test_utcnow.timetuple()))) + " | " + test_utcnow.replace(tzinfo=timezone("UTC")).astimezone(timezone('Europe/Berlin')).isoformat())
                    # logger.info("utcman: " + str(int(time.mktime(test_utcman.timetuple()))) + " | " + test_utcman.astimezone(timezone('Europe/Berlin')).isoformat())

                if not io_state1 or not io_state2:
                    state = self.STATE_COLLECTING
                    collect_time_start = ts
                    last_sensor_reading = ts
                    
            # The collection state listens for more sensor activity
            # for some time. if a sensor is triggered the time period
            # is extended
            if state == self.STATE_COLLECTING:
                if ts == collect_time_start:
                    logger.info("collecting")

                # React to input
                if not io_state1:
                    last_sensor_reading = ts # reset the collect time to the current timestamp, to continue collecting
                    # coll.append(1)
                    sensor = 1
                elif not io_state2:
                    last_sensor_reading = ts # reset the collect time to the current timestamp, to continue collecting
                    # coll.append(2)
                    sensor = 2
                else:
                    # coll.append(0)
                    sensor = 0

                if len(coll3)==0 or coll3[-2] != sensor:
                        coll3 += [sensor, 0] # adds [sensor key, initial count]
                coll3[-1] += 1 # increases count by 1

                # Exit the collecting state of nothing happens
                if ts - last_sensor_reading > self.collect_time:
                    state = self.STATE_COOLDOWN

            # The cooldown state cleans the pattern and
            # saves notifies observers for further processing
            elif state == self.STATE_COOLDOWN:
                logger.info("cooldown")
                # remove zeros at the end of the pattern
                # coll = np.asarray(coll)
                # last_idx = (coll>0).nonzero()[-1][-1]
                # coll = coll[0:last_idx+1]
                # pattern = coll.tolist()

                coll3 = np.asarray(coll3)
                last_idx = ((coll3[::2]>0).nonzero()[-1][-1]+1)*2-1 # find the last non-zero sensor reading
                coll3 = coll3[0:last_idx+1] # and cut everything after it
                pattern = coll3.tolist()

                logger.info(f"Discovered pattern: {pattern}")

                # create the document
                doc = {"start":int(collect_time_start),
                    "end": int(last_sensor_reading),
                    "checks_per_sec": self.checks_per_sec,
                    "pattern": pattern,
                    "pattern_len": sum(pattern[1::2]),
                    "timezone": {
                        "tz": "UTC"
                    }
                    }
                doc["duration_s"] = round(last_sensor_reading - collect_time_start,2) 
                doc["direction"] = self.direction_strat.get_direction(doc["pattern"])

                def get_duration_str(dur_s):
                    if dur_s >= 3600: #hrs
                        hrs = int(dur_s / 3600)
                        mins = int((dur_s - 3600 * hrs) / 60)
                        return "{}:{} Stunden".format(hrs, mins)
                    if dur_s >= 60: #mins
                        mins =  int((dur_s / 60))
                        seks = int(dur_s - mins * 60)
                        return "{}:{} Minuten".format(mins, seks)
                    return "{} Sekunden".format(dur_s)

                doc["duration_str"] = get_duration_str(doc["duration_s"])

                #doc["_id"] = uuid4().hex
                # compress the pattern
                # doc["pattern"] = Pattern.compress(doc["pattern"])
                #doc["timestamp_iso"] = datetime.datetime.fromtimestamp(
                #    doc["timestamp"]
                #).isoformat()
                doc["type"] = "pattern_v2"

                with util.get_postgres_con(util.config) as con:
                    sql = "INSERT INTO passage (doc, start) VALUES (%s, %s) RETURNING id"
                    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
                    inserted = cur.execute(sql, (json.dumps(doc), doc["start"]))
                    con.commit()
                    doc["id"] = cur.fetchone()["id"]
                    logger.info("Passage stored in Postgres")

                # logger.info("Stored pattern in database: {0}".format(doc_id))
                try:
                    self.notifyObservers(doc=doc)
                except Exception as e:
                    logger.error("At least one observer failed: {}".format(e))

                # reset the pattern
                # coll = list()
                # coll2 = []
                coll3 = []
                # return to waiting state
                state = self.STATE_WAITING

            # Wait some time
            time.sleep(sleep_time)
