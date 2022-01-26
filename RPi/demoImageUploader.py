import requests
from kafka import KafkaConsumer, TopicPartition
import os

def upload_image(imgPath, ip, port):
    url = "http://{}:{}/demo/api/preview_upload/".format(ip, port)

    imgName = os.path.basename('E:\project-python\string\list.py')
    payload={}
    files=[
        ('img_preview', (imgName, open(imgPath,'rb'), 'application/octet-stream'))
    ]
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

class DemoRequests:
    def __init__(self, address, port, topic):
        super(DemoRequests, self).__init__()

        self.consumer = None
        self.address = address
        self.port = port
        self.topic = topic
        self.timeout = 1
        self.maxEventPerSend = 100

    def connect(self):
        connStr = '{}:{}'.format(self.address, self.port)
        c = KafkaConsumer(bootstrap_servers=connStr, consumer_timeout_ms=5)
        topicPartition = TopicPartition(self.topic, 0)
        c.assign([topicPartition])
        self.consumer = c

    def getRequests(self):
        r = []

        for msg in self.consumer:
            req = msg.value.decode(encoding='UTF-8',errors='strict')
            r.append(req)

        # if self.consumer != None:
        #     msgs = self.consumer.poll()
        #     for msg in msgs:
        #         req = msg.value.decode(encoding='UTF-8',errors='strict')
        #         r.append(req)
        
        return r
