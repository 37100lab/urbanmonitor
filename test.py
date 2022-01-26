import cv2
import sys
from argparse import ArgumentParser
import logging
from pathlib import Path

logging.basicConfig(format='[ %(levelname)s ] %(message)s', level=logging.INFO, stream=sys.stdout)
log = logging.getLogger()

parser = ArgumentParser()
parser.add_argument('--input', type=str, help='video path',required=True)
parser.add_argument('--tracker', type=str, help='track method',default="kcf")

args = parser.parse_args()

print(cv2.__version__)

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

OPENCV_OBJECT_TRACKERS = {
    "csrt": cv2.legacy.TrackerCSRT_create,
    "kcf": cv2.TrackerKCF_create,
    "boosting": cv2.TrackerBoosting_create,
    "mil": cv2.TrackerMIL_create,
    "tld": cv2.TrackerTLD_create,
    "medianflow": cv2.TrackerMedianFlow_create,
    "mosse": cv2.TrackerMOSSE_create
}

trackers = cv2.MultiTracker_create()

print("To close the application, press 'CTRL+C' here or switch to the output window and press ESC key")

while True:
    t_start = cv2.getTickCount()
    ret, original_image = capture.read()

    fps = cv2.getTickFrequency()  / (cv2.getTickCount() - t_start)
    cv2.putText(original_image, 'summary: {:.1f} FPS'.format(fps), (5, 15), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 200))

    cv2.imshow("capture", original_image)

    next_frame_id += 1

    if cv2.waitKey(3) & 0xFF == 27:
        break
  
capture.release()
cv2.destroyAllWindows()