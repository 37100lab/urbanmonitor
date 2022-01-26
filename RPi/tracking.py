import argparse
import os
import re
import time
import multiprocessing
import datetime
import atexit

import cv2
import numpy as np
import configparser

from centroidtracker import CentroidTracker
from demoImageUploader import DemoRequests, upload_image
from utils import detect_objects, load_labels, make_interpreter,parse_lines

from objectEventLogger import ObjectEventLogger, CsvObjectEventLogger, KafkaEventLogger


#https://stackoverflow.com/questions/54093424/why-is-tensorflow-lite-slower-than-tensorflow-on-desktop


default_model_dir = './models'
default_model = 'ssd_mobilenet_v2_coco_quant_postprocess.tflite'
default_labels = 'coco_labels.txt'
default_debugOut_dir = './debugOut'

outFont = cv2.FONT_HERSHEY_PLAIN
outFontScale = 1.0
outFontThickness = 1

config = None

def initEventLoggers():
  eventLogger = ObjectEventLogger()

  csvLogger = CsvObjectEventLogger()
  eventLogger.appendLogger(csvLogger)

  try:
    if config != None and int(config["kafka"]["enabled"]) != 0:
        host = config["kafka"]["host"]
        port = int(config["kafka"]["port"])
        topic = config["kafka"]["topic"]

        kafkaLogger = KafkaEventLogger(host, port, topic)
        eventLogger.appendLogger(kafkaLogger)
  except Exception as exc:
    print("Kafka error: " + str(exc))

  return eventLogger

def initDemoRequest():
  try:
    if config != None and int(config["kafka"]["enabled"]) != 0:
      host = config["kafka"]["host"]
      port = int(config["kafka"]["port"])
      topic = config["kafka"]["topicReq"]
      d = DemoRequests(host, port, topic)
      d.connect()
      return d
  except Exception as exc:
    print("Kafka error: " + str(exc))
    return None

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--model', help='.tflite model path', default=os.path.join(default_model_dir,default_model))
  parser.add_argument('--labels', help='label file path', default=os.path.join(default_model_dir, default_labels)),
  parser.add_argument('--threshold', type=float, default=0.4, help='classifier score threshold')
  parser.add_argument('--input', type=str, help='video path', default='0')
  parser.add_argument('--gates', type=str, help='gates', default='./gates/gates.json')
  parser.add_argument('-q', '--quiet',action='store_true',dest='quiet',help='Suppress Output')
  parser.add_argument('-u', '--showui',action='store_true',dest='showUi',help='Show UI')
  parser.add_argument('--threads', type=int, default=0, help='number of threads')
  parser.add_argument('--fps', type=int, default=0, help='number of frame per seconds')
  parser.add_argument('--debug', action='store_true',dest='debug',help='Show UI')

  args = parser.parse_args()

  try:
    config = configparser.ConfigParser()
    config.read("./config.ini")
  except Exception as exc:
    print("Config.ini error: " + str(exc))
    config = None

  print('Loading {} with {} labels.'.format(args.model, args.labels))
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

  if not os.path.isdir(default_debugOut_dir):
    os.mkdir(default_debugOut_dir)

  labels = load_labels(args.labels)
  gates = parse_lines(args.gates)

  if args.threads == 0:
    numThreads = max((multiprocessing.cpu_count() -1), 1)
  else:
    numThreads = max(args.threads, 1)

  print('Using TFLite with {} threads'.format(numThreads))
  interpreter = make_interpreter(model_file = args.model, num_threads = numThreads)
  interpreter.allocate_tensors()

  ct = CentroidTracker(gates, 4)

  eventLogger = initEventLoggers()
  demoReq = initDemoRequest()

  @atexit.register
  def atQuit():
    print("Closing...")
    eventLogger.close()
    capture.release()
    cv2.destroyAllWindows()

  

  frameTimeS = 0
  if args.fps > 0:
    frameTimeS = 1.0 / args.fps

  refreshWindowImageToggle = True
  while True:
      loop_time = time.monotonic()

      ret, frame = capture.read()
      if frame is None:
          break

      start_time_inference = time.monotonic()

      results = detect_objects(interpreter, frame, args.threshold)

      end_time_inference = time.monotonic()
      elapsed_ms_inference = (end_time_inference - start_time_inference) * 1000

      start_time_tracker = time.monotonic()

      objects = ct.update(results, eventLogger)

      end_time_tracker = time.monotonic()
      elapsed_ms_tracker = (end_time_tracker - start_time_tracker) * 1000

      if demoReq != None:
        try:
          drs = demoReq.getRequests()
          if "image_request" in drs:
            for (objectID, object) in objects[0].items():
              if objectID in objects[1]:
                objColor = (255, 0, 0)
              else:
                objColor = (0, 255, 0)

              # text = "ID {0} class {1} confidence {2}%".format(objectID,labels.get(object[2],'ND'),object[3])
              text = "{0} {1} {2}%".format(objectID,labels.get(object[2],'ND'),object[3])
              cv2.putText(frame, text, (object[1] - 10, object[0] - 10), outFont, outFontScale, objColor, outFontThickness, cv2.LINE_AA)
              cv2.circle(frame, (object[1], object[0]), 4, objColor, -1)

            for gate in gates:
              cv2.line(frame, gate[0], gate[1], (0, 0, 255), 2)
              cv2.putText(frame, gate[2], (gate[0][0] + 10, gate[0][1] - 10), outFont, outFontScale, (0, 0, 255), outFontThickness, cv2.LINE_AA)
              cv2.circle(frame, gate[0], 4, (0, 0, 255), -1)
              cv2.circle(frame, gate[1], 4, (0, 0, 255), -1)

            dateNow = datetime.datetime.now()
            fileName = "img_" + dateNow.strftime("%Y-%m-%d_%H-%m-%S-%f") + ".jpg"
            path = default_debugOut_dir + '/' + fileName
            cv2.imwrite(path, frame)
            upload_image(path, config["rest"]["host"], config["rest"]["port"])
        except Exception as e:
          print(str(e))

      if args.showUi or args.debug:
        if refreshWindowImageToggle or args.debug:
          for (objectID, object) in objects[0].items():
            if objectID in objects[1]:
              objColor = (255, 0, 0)
            else:
              objColor = (0, 255, 0)

            # text = "ID {0} class {1} confidence {2}%".format(objectID,labels.get(object[2],'ND'),object[3])
            text = "{0} {1} {2}%".format(objectID,labels.get(object[2],'ND'),object[3])
            cv2.putText(frame, text, (object[1] - 10, object[0] - 10), outFont, outFontScale, objColor, outFontThickness, cv2.LINE_AA)
            cv2.circle(frame, (object[1], object[0]), 4, objColor, -1)

          for gate in gates:
            cv2.line(frame, gate[0], gate[1], (0, 0, 255), 2)
            cv2.putText(frame, gate[2], (gate[0][0] + 10, gate[0][1] - 10), outFont, outFontScale, (0, 0, 255), outFontThickness, cv2.LINE_AA)
            cv2.circle(frame, gate[0], 4, (0, 0, 255), -1)
            cv2.circle(frame, gate[1], 4, (0, 0, 255), -1)

        if refreshWindowImageToggle:
          cv2.imshow("tracker output", frame)

        if demoReq != None:
          drs = demoReq.getRequests()
          if "image_request" in drs:
            dateNow = datetime.datetime.now()
            fileName = "img_" + dateNow.strftime("%Y-%m-%d_%H-%m-%S-%f") + ".jpg"
            path = default_debugOut_dir + '/' + fileName
            cv2.imwrite(path, frame)
            upload_image(path, config["rest"]["host"], config["rest"]["port"])

        if args.debug:
          dateNow = datetime.datetime.now()
          fileName = "img_" + dateNow.strftime("%Y-%m-%d_%H-%m-%S-%f") + ".jpg"
          cv2.imwrite(default_debugOut_dir + '/' + fileName, frame)

      if args.showUi:
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
          break
        elif key == ord(" "):
          refreshWindowImageToggle = not refreshWindowImageToggle

      elapsed_ms_loop = (time.monotonic() - loop_time)
      waitTime = max(frameTimeS - elapsed_ms_loop, 0)
      elapsed_ms_loop *= 1000

      if not args.quiet:
        print("Inference time: {0:.2f} ms, Traker time: {1:.2f} ms, Loop time: {2:.2f}".format(elapsed_ms_inference, elapsed_ms_tracker, elapsed_ms_loop))
    
      time.sleep(waitTime)

  eventLogger.close()
  # capture.release()
  # cv2.destroyAllWindows()

