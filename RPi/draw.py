import argparse
import cv2
import json

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

        gate = "{0}".format(len(lines))

        lines.append({'start':start,'end':end,'name':gate})
        cv2.line(frame, p0, p1, RED, 2)
        frameLine[:] = frame
    
    cv2.imshow('gates', frame)
    #cv2.displayOverlay('gates', f'p0={p0}, p1={p1}')





parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, help='video path', default='0')
parser.add_argument('--output', type=str, help='json gate file', default='./gates/gates.json')
args = parser.parse_args()

if args.input.isdigit():
  inputParam = int(args.input)
  print('Loading camera {}.'.format(inputParam))
else:
  inputParam = args.input
  print('Loading file {}.'.format(args.input))

capture = cv2.VideoCapture(inputParam)

if not capture.isOpened():
  print('Unable to open: ' + args.input)
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