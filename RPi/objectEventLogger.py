import csv
import datetime
import os
import json
from threading import Thread, Lock, currentThread
import time
from kafka import KafkaProducer
import traceback


class IObjectEventLogger(Thread):
    def __init__(self):
        super(IObjectEventLogger, self).__init__()
        self.data = []
        self.mutex = Lock()
        self.loop = True

    def logObjectEvent(self, dt, objClass, confidence, gateNumber, direction):
        self.mutex.acquire()
        try:
            self.data.append(
                {
                    'timestamp': int(dt.timestamp() * 1000),
                    'objClass': int(objClass),
                    'confidence': int(confidence),
                    'gateNumber': gateNumber,
                    'direction': int(direction)
                })
        except:
            pass
        finally:
            self.mutex.release()

    def stop(self):
        self.loop = False


class ObjectEventLogger:
    def __init__(self):
        self.loggers = []

    def appendLogger(self, logger):
        self.loggers.append(logger)
        logger.start()

    def logObjectEvent(self, objClass, confidence, gateNumber, direction):
        dt = datetime.datetime.now()
        for logger in self.loggers:
            logger.logObjectEvent(dt, objClass, confidence, gateNumber, direction)

    def close(self):
        for logger in self.loggers:
            logger.stop()
            logger.join()


class KafkaEventLogger(IObjectEventLogger):
    def __init__(self, address, port, topic):
        super(KafkaEventLogger, self).__init__()

        self.producer = None
        self.address = address
        self.port = port
        self.topic = topic
        self.timeout = 1
        self.maxEventPerSend = 100

    def connect(self):
        connStr = '{}:{}'.format(self.address, self.port)
        p = KafkaProducer(bootstrap_servers=connStr)
        self.producer = p

    def run(self):
        while self.loop:
            try:
                if self.producer == None:
                    self.connect()
            except Exception as exc:
                print('kafkaLogger: ' + str(exc))
                traceback.print_exc()
                time.sleep(1.0)
                continue

            try:
                self.mutex.acquire()
                if len(self.data) > 0:
                    dataJson = json.dumps(self.data[0:self.maxEventPerSend])
                    self.mutex.release()

                    future = self.producer.send(topic=self.topic, key=b'', partition=0, value=dataJson.encode('utf-8'))
                    result = future.get(timeout=self.timeout)

                    self.mutex.acquire()
                    self.data = self.data[self.maxEventPerSend:]

                self.mutex.release()
            except Exception as exc:
                print('kafkaLogger: ' + str(exc))
                traceback.print_exc()
            
            time.sleep(0.1)

        if self.producer == None:
            self.producer.flush()


class CsvObjectEventLogger(IObjectEventLogger):
    def __init__(self):
        super(CsvObjectEventLogger, self).__init__()

        self.csvFile = None
        self.csvWiter = None
        self.currentDay = None
        self.outDirectory = "./out"

    def run(self):
        while self.loop:
            try:
                if self.isDayChanged() or self.csvFile == None:
                    self.openNewFile()
            except Exception as exc:
                print('csvLoggerFile: ' + str(exc))
                traceback.print_exc()

            try:
                self.mutex.acquire()

                if len(self.data) > 0:
                    d = self.data[0]
                    dt = datetime.datetime.fromtimestamp(d['timestamp'] / 1000)

                    self.csvWiter.writerow((str(dt), d['objClass'], d['confidence'], d['gateNumber'], d['direction']))
                    self.csvFile.flush()
                    self.data.pop(0)

            except Exception as exc:
                print('csvLogger: ' + str(exc))
                traceback.print_exc()
            finally:
                self.mutex.release()
            
            time.sleep(0.1)

        self.closeFile()

    def openNewFile(self):
        if not os.path.isdir(self.outDirectory):
            os.mkdir(self.outDirectory)

        filePath = self.outDirectory + "/" + str(datetime.datetime.now().date()) + ".csv"

        self.closeFile()

        if not os.path.exists(filePath):
            self.csvFile = open(filePath, 'w')
            self.csvWiter = csv.writer(self.csvFile)
            self.csvWiter.writerow(("datetime", "object class", "confidence", "gate name", "direction"))
        else:
            self.csvFile = open(filePath, 'a')
            self.csvWiter = csv.writer(self.csvFile)

        self.currentDay = datetime.datetime.now().day

    def isDayChanged(self):
        return self.currentDay != datetime.datetime.now().day

    def closeFile(self):
        if self.csvFile != None:
            self.csvFile.flush()
            self.csvFile.close()
