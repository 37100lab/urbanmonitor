import cv2
from openvino.inference_engine import IECore

from utils import resize_input

palette = [(0,0,250),(0,250,0),(250,0,0),(100,100,100),(255,255,255)]


class VehicleDetection():
    def __init__(self, xmin, ymin, xmax, ymax, score, class_id, label):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.score = score
        self.class_id = int(class_id)
        self.label = label

    def bottom_left_point(self):
        return self.xmin, self.ymin

    def top_right_point(self):
        return self.xmax, self.ymax

    def centroid(self):
        cX = int((self.xmin + self.xmax) / 2.0)
        cY = int((self.ymin + self.ymax) / 2.0)
        return (cX,cY)

    def overlap(self,box):
        x1 = max(self.xmin, box.xmin)
        y1 = max(self.ymin, box.ymin)
        x2 = min(self.xmax, box.xmax)
        y2 = min(self.ymax, box.ymax)
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        return intersection


    def draw_box(self,image):
        color = palette[self.class_id]
        text_color = palette[-1]

        text = "{0}:{1:.2f}".format(self.label,float(self.score))

        image = cv2.rectangle(image, (self.xmax, self.ymax), (self.xmin, self.ymin), palette[self.class_id], 2)

        (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        img = cv2.rectangle(image, (self.xmin, self.ymin - 20), (self.xmin + w, self.ymin), color, -1)
        image = cv2.putText(image, text, (self.xmin, self.ymin - int(h / 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 1)
       

class VehicleDetector():

    def __init__(self, model, labels = None, device = 'CPU', confidence_threshold=0.5, config = None,extension = None):
        ie = IECore()

        if extension and device == 'CPU':
            ie.add_extension(extension, device)

        if config and device in ('GPU', 'MYRIAD', 'HDDL'):
            ie.set_config({'CONFIG_FILE': config}, device)
        
        self.net = ie.read_network(model=model)

        if len(self.net.input_info) != 1:
            raise RuntimeError('The sample supports only single input topologies')

        if len(self.net.outputs) != 1 and not ('boxes' in self.net.outputs or 'labels' in self.net.outputs):
            raise RuntimeError('The sample supports models with 1 output or with 2 with the names "boxes" and "labels"')
        
        self.input_blob = next(iter(self.net.input_info))

        self.net.input_info[self.input_blob].precision = 'U8'

        if len(self.net.outputs) == 1:
            self.output_blob = next(iter(self.net.outputs))
            self.net.outputs[self.output_blob].precision = 'FP32'
        else:
            self.net.outputs['boxes'].precision = 'FP32'
            self.net.outputs['labels'].precision = 'U16'
        
        self.exec_net = ie.load_network(network=self.net, device_name=device)

        assert 0.0 <= confidence_threshold <= 1.0, 'Confidence threshold is expected to be in range [0; 1]'
        self.confidence_threshold = confidence_threshold

        self.labels = labels
        self.input_shape = self.net.input_info[self.input_blob].input_data.shape
    
    def preprocess(self, frame):
        self.input_size = frame.shape
        return resize_input(frame, self.input_shape)

    
    def postprocess(self,result):

        if len(self.net.outputs) == 1:
            res = result[self.output_blob]
            detections = res.reshape(-1, 7)
        else:
            detections = result['boxes']
            labels = result['labels']

        h, w, _ = self.input_size
        boxes = []

        for i, detection in enumerate(detections):
            if len(self.net.outputs) == 1:
                _, class_id, confidence, xmin, ymin, xmax, ymax = detection
            else:
                class_id = labels[i]
                xmin, ymin, xmax, ymax, confidence = detection
            
            if confidence >= self.confidence_threshold:
                label = self.labels[class_id] if self.labels else int(class_id)
                xmin = int(xmin * w)
                ymin = int(ymin * h)
                xmax = int(xmax * w)
                ymax = int(ymax * h)

                detect = VehicleDetection(xmin,ymin,xmax,ymax,confidence,class_id,label)
                boxes.append(detect)
        
        return boxes

    def infer(self,frame):
        image = self.preprocess(frame)
        result = self.exec_net.infer(inputs={self.input_blob: image})
        return self.postprocess(result)
