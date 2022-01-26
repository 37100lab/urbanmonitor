import json
import random
import re

import cv2


def generate_random_color():
  r = random.randint(0,255)
  g = random.randint(0,255)
  b = random.randint(0,255)

  return (b,g,r)


def resize_image(image, size, keep_aspect_ratio=False):
    if not keep_aspect_ratio:
        resized_frame = cv2.resize(image, size)
    else:
        h, w = image.shape[:2]
        scale = min(size[1] / h, size[0] / w)
        resized_frame = cv2.resize(image, None, fx=scale, fy=scale)
    return resized_frame

def resize_input(image, target_shape):
    _, _, h, w = target_shape
    resized_image = resize_image(image, (w, h))
    resized_image = resized_image.transpose((2, 0, 1)) # HWC->CHW
    resized_image = resized_image.reshape(target_shape)
    return resized_image


def load_labels(path):
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

def parse_gates(path):
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

def draw_gates(image,gates):
  for gate in gates:
    start, end, _ = gate
    cv2.line(image,start,end,(0,0,255),3)

def ccw(a, b, c):
  return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
	
def cross(s1, s2):
  a, b = s1
  c, d = s2
  return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)