import json
import os
import platform
import re

import cv2
import numpy as np
from tflite_runtime.interpreter import Interpreter, load_delegate

EDGETPU_SHARED_LIB = {
  'Linux': 'libedgetpu.so.1',
  'Darwin': 'libedgetpu.1.dylib',
  'Windows': 'edgetpu.dll'
}[platform.system()]

def load_labels(path):
  """Loads the labels file. Supports files with or without index numbers."""
  with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    labels = {}
    for row_number, content in enumerate(lines):
      pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
      if len(pair) == 2 and pair[0].strip().isdigit():
        labels[int(pair[0])] = pair[1].strip()
      else:
        labels[row_number] = pair[0].strip()
  return labels


def set_input_tensor(interpreter, image):
  """Sets the input tensor."""
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image


def get_output_tensor(interpreter, index):
  """Returns the output tensor at the given index."""
  output_details = interpreter.get_output_details()[index]
  tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
  return tensor

def detect_objects(interpreter, image, threshold):

  height, width, channels = image.shape

  _, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']
  cv2_im_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
  cv2_im_rgb = cv2.resize(cv2_im_rgb, (input_width, input_height))

  """Returns a list of detection results, each a dictionary of object info."""
  set_input_tensor(interpreter, cv2_im_rgb)
  interpreter.invoke()

  # Get all output details
  boxes = get_output_tensor(interpreter, 0)
  classes = get_output_tensor(interpreter, 1)
  scores = get_output_tensor(interpreter, 2)
  count = int(get_output_tensor(interpreter, 3))

  
  keep_idx = np.less(scores[np.greater(scores, threshold)], 1)
  boxes  = boxes[:keep_idx.shape[0]][keep_idx]
  classes = classes[:keep_idx.shape[0]][keep_idx]
  scores = scores[:keep_idx.shape[0]][keep_idx]

  results = np.array([])

  # denormalize bounding box dimensions
  if len(boxes) > 0:
    boxes[:,0] = boxes[:,0] * height
    boxes[:,1] = boxes[:,1] * width
    boxes[:,2] = boxes[:,2] * height
    boxes[:,3] = boxes[:,3] * width

    results = np.append(boxes, np.expand_dims(classes, axis=1), axis=1)
    results = np.append(results, np.expand_dims(scores * 100, axis=1), axis=1)

    # mask = results[:,4] < 8
    # results = results[mask, :]

  return results

def make_interpreter(model_file, num_threads = 1):
    tpu = "edgetpu" in model_file

    if tpu:
        interpreter = Interpreter(model_path=model_file, num_threads = num_threads,
        experimental_delegates=[load_delegate(EDGETPU_SHARED_LIB,{})])
    else:
        interpreter = Interpreter(model_path= model_file, num_threads = num_threads,)

    return interpreter


def parse_lines(path):
    gates = []

    with open(path) as f:
        data = json.load(f)
    
    for gate in data:
        startx = gate['start']['x']
        starty = gate['start']['y']
        
        endx = gate['end']['x']
        endy = gate['end']['y']
        
        name = gate['name']
        
        gates.append([(startx,starty),(endx,endy),name])
    
    return gates

