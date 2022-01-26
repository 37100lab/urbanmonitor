import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

import cv2

from detector import VehicleDetector
from tracker import VehicleTracker
from utils import draw_gates, load_labels, parse_gates

default_labels = 'labels.txt'

#Se non carica i video
#https://community.intel.com/t5/Intel-Distribution-of-OpenVINO/OpenCV-4-1-2-openvino-Unsupported-Extension-Error-Solved/td-p/1129111#comment-1959910
#https://opencv.org/how-to-speed-up-deep-learning-inference-using-openvino-toolkit-2/

logging.basicConfig(format='[ %(levelname)s ] %(message)s', level=logging.INFO, stream=sys.stdout)
log = logging.getLogger()

def printGate(objId,gateName,objClass,objConf):
  log.info("Rilevato passagio dell'oggetto {0} classe {1} al gate {2}".format(objId,gateName,objClass))

def printCrash(id,id_crash,box,other,threshold_x,threshold_y):
  log.warning("Rilevato crash tra oggetto {0} e oggeto {1}".format(id,id_crash))


parser = ArgumentParser()

parser.add_argument('--model', help='Required. Path to an .xml file with a trained model.',
  required=True, type=Path)
parser.add_argument('--device', default='CPU', type=str,
  help='Optional. Specify the target device to infer on; CPU, GPU, MYRIAD, HDDL or HETERO: '
  'is acceptable. The sample will look for a suitable plugin for device specified. '
  'Default value is CPU.')
parser.add_argument('--config', type=str, default=None,
help='Optional. Required by GPU or VPU Plugins for the custom operation kernel. '
'Absolute path to operation description file (.xml).')
parser.add_argument('--labels', help='label file path',
  default=default_labels),
parser.add_argument('--threshold', type=float, default=0.4,
  help='classifier score threshold')
parser.add_argument('--input', type=str, help='video path',required=True)
parser.add_argument('--gates', type=Path, help='gates',required=True)

args = parser.parse_args()

log.info('Loading labels {0}.'.format(args.labels))
labels = load_labels(args.labels)
log.info('Found {0} labels.'.format(len(labels)))


log.info('Loading gates {0}.'.format(args.gates))
gates = parse_gates(args.gates)
log.info('Found {0} gates.'.format(len(gates)))

input = args.input
capture = None

if(input.isnumeric()):
  log.info('Using opencv camera capture {}.'.format(input))
  capture = cv2.VideoCapture(int(args.input))
else:
  log.info('Loading file {}.'.format(input))
  file = Path(input)
  if file.exists() and file.is_file():
    capture = cv2.VideoCapture(args.input)
  else:
    raise FileNotFoundError("File {0} doesn't exits !!".format(input))

if not capture.isOpened():
  log.error('Unable to open: {0}'.format(args.input))
  exit(0)


width  = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))   
height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))  

log.info('Frame dimensons: {0}x{1}'.format(width,height))

next_frame_id = 0

# Inizializzazione
vehicleDetector = VehicleDetector(args.model,labels,args.device,config=args.config)
vehicleTracker = VehicleTracker(gates,gate_callback=printGate,crash_callback=printCrash)

print("To close the application, press 'CTRL+C' here or switch to the output window and press ESC key")

while True:
    t_start = cv2.getTickCount()
    ret, original_image = capture.read()

    if original_image is None:
      break

    detections = vehicleDetector.infer(original_image)
    vehicleTracker.update(detections)


    #for detection in detections:
    #  detection.draw_box(original_image)

    #vehicleTracker.draw_velocity(original_image)
    vehicleTracker.draw_tracks(original_image)

    draw_gates(original_image,gates)
    fps = cv2.getTickFrequency()  / (cv2.getTickCount() - t_start)
    cv2.putText(original_image, 'summary: {:.1f} FPS'.format(fps), (5, 15), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 200))

    cv2.imshow("capture", original_image)

    next_frame_id += 1

    if cv2.waitKey(3) & 0xFF == 27:
        break
  
capture.release()
cv2.destroyAllWindows()
    
