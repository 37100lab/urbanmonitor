import argparse
import cv2
import json
import logging
import sys
from pathlib import Path

RED = (0, 0, 255)
BLUE = (255, 0, 0)

p0 = (0,0)
p1 = (0,0)

def mouse(event, x, y, flags, param):
    global p0, p1
   

    if event == cv2.EVENT_LBUTTONDOWN:
        p0 = x, y
        p1 = x, y

    elif event == cv2.EVENT_MOUSEMOVE and flags == 1:
        p1 = x, y
        frame[:] = frameLine
        cv2.line(frame, p0, p1, BLUE, 2)

    elif event == cv2.EVENT_LBUTTONUP:
        frame[:] = frameLine

        start = {'x': p0[0],'y': p0[1]}
        end = {'x': p1[0],'y': p1[1]}

        gate = "Gate numero {0}".format(len(lines))

        lines.append({'start':start,'end':end,'name':gate})
        cv2.line(frame, p0, p1, RED, 4)
        frameLine[:] = frame
    
    cv2.imshow('gates', frame)
    #cv2.displayOverlay('gates', f'p0={p0}, p1={p1}')


logging.basicConfig(format='[ %(levelname)s ] %(message)s', level=logging.INFO, stream=sys.stdout)
log = logging.getLogger()

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, help='video path',required=True)
parser.add_argument('--output', type=str, help='json gate file',required=True)
args = parser.parse_args()


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


ret, frame = capture.read()
frameLine = frame.copy()

lines = []

cv2.imshow("gates", frame)
cv2.setMouseCallback('gates', mouse)

cv2.waitKey(0)
cv2.destroyAllWindows()

with open(args.output, "w") as write_file:
    json.dump(lines, write_file)