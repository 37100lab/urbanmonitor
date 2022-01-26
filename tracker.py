from collections import defaultdict
import cv2
import enum
import numpy as np
from norfair import Detection, Tracker,Color
from utils import cross

# Distance function
def centroid_distance(detection, tracked_object):
    return np.linalg.norm(detection.points - tracked_object.estimate)

class VehicleTracker():
    def __init__(self,gates,gate_callback = None,crash_callback = None,point_transience=4,distance_threshold=30,num_point_to_track=10,maxDisappeared=30):
        self.gates = gates
        self.tracker = Tracker(distance_function=centroid_distance, distance_threshold=distance_threshold,point_transience=point_transience)
        self.disappeared = defaultdict(int)
        self.tracks = defaultdict(list)
        self.num_point_to_track = num_point_to_track
        self.gate_callback = gate_callback
        self.crash_callback = crash_callback

        self.maxDisappeared = maxDisappeared

        self.vel = defaultdict(list)
        self.acc = defaultdict(list)

    def update(self,detections):
        objects = [Detection(np.array([p.centroid()]),scores=np.array([p.score]),data = {'label' : p.label,'box' : p}) for p in detections]
        self.tracked_objects = self.tracker.update(detections=objects)
        
        live_id = []

        for obj in self.tracked_objects:
            if not obj.live_points.any():
                continue
            
            point = obj.estimate[0]
            id = obj.id

            live_id.append(id)
            
            track = self.tracks[id]
            if len(track) >= self.num_point_to_track:
                track.pop()
            track.insert(0,(int(point[0]),int(point[1])))

            if len(track) > 1 and self.gate_callback is not None:
                score = obj.last_detection.scores
                label = obj.last_detection.data['label']
                for gate in self.gates:
                    start, end, name = gate
                    if cross((start, end),(track[0],track[1])):
                        self.gate_callback(id,name,label,score)
            
            if len(track) > 1 and self.crash_callback is not None:
                self.calc_vel(id,track)
                self.calc_acc(id)
                
                self.detectCollision()

        
        for track in list(self.tracks.keys()):
            if track not in live_id:
                self.disappeared[track] += 1
                if self.disappeared[track] > self.maxDisappeared:
                    del self.tracks[track]
                    del self.disappeared[track]

    def calc_vel(self,id,track):
        delta_x = 0
        delta_y = 0
        if len(track) > 1:
            for index,actual in enumerate(track[:-1]):
                actual = track[index]
                previuos = track[index + 1]

                delta_x += actual[0] - previuos[0]
                delta_y += actual[1] - previuos[1]
            
            delta_x = (10 * delta_x) / float(len(track))
            delta_y = (10 * delta_y) / float(len(track))

            velocity = self.vel[id]

            if len(velocity) >= self.num_point_to_track:
                velocity.pop()
            
            velocity.insert(0,(delta_x,delta_y))
            self.vel[id] = velocity

    def calc_acc(self,id):
        delta_x = 0
        delta_y = 0

        velocity = self.vel[id]

        if len(velocity) > 1:
            for index,actual in enumerate(velocity[:-1]):
                actual = velocity[index]
                previuos = velocity[index + 1]

                delta_x += actual[0] - previuos[0]
                delta_y += actual[1] - previuos[1]

            delta_x = (10 * delta_x) / float(len(velocity))
            delta_y = (10 * delta_y) / float(len(velocity))
        
            acceleration = self.acc[id]
            if len(acceleration) >= self.num_point_to_track:
                acceleration.pop()
            
            acceleration.insert(0,(delta_x,delta_y))
            self.acc[id] = acceleration

    def detectCollision(self):
        live_track = {}

        for obj in self.tracked_objects:
            if not obj.live_points.any():
                continue

            id = obj.id
            live_track[id] = obj

        for id in live_track:
            acceleration = self.acc[id]
            velocity = self.vel[id]
            if len(acceleration) > 0 and len(velocity) > 0 :
                same_sign_x = (acceleration[0][0] * velocity[0][0]) > 0
                same_sign_y = (acceleration[0][1] * velocity[0][1]) > 0

                sign_x = same_sign_x and 1 or -1
                sign_y = same_sign_y and 1 or -1

                acc_x = 0
                acc_y = 0
                if len(self.acc[id]) > 0:
                    for index,actual in enumerate(self.acc[id][:-1]):
                        actual = velocity[index]
                        previuos = velocity[index + 1]

                        acc_x += actual[0] - previuos[0]
                        acc_y += actual[1] - previuos[1]
                
                    acc_x = acc_x / float(len(self.acc[id]))
                    acc_y = acc_y / float(len(self.acc[id]))
                
                threshold_x = sign_x * abs(self.acc[id][0][0] - acc_x)
                threshold_y = sign_y * abs(self.acc[id][0][1] - acc_y)

                if threshold_x >= 40 or threshold_y >= 40:
                    #rilevata accelerazione forte

                    box = obj.last_detection.data['box']

                    for id_crash in live_track:
                        if id_crash == id:
                            continue
                        objOther = live_track[id_crash]
                        other = objOther.last_detection.data['box']

                        if box.overlap(other) > 0:
                            self.crash_callback(id,id_crash,box,other,threshold_x,threshold_y)
                    
    
    def draw_tracks(self,image):
        for track in list(self.tracks.keys()):
            color = Color.random(track)
            position = self.tracks[track][0]
            image = cv2.putText(image, str(track), position, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
            for index,point in enumerate(self.tracks[track][:-1]):
                next_point = self.tracks[track][index + 1]
                cv2.line(image,point,next_point,color,2)
    
    def draw_velocity(self,image):
        for track in list(self.tracks.keys()):
            color = Color.random(track)
            position = self.tracks[track][0]
            image = cv2.putText(image, str(track), position, cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1) 

            
            if len(self.vel[track]) > 0:
                velocity = self.vel[track][0]
                end = position[0] + (int(velocity[0])) , position[1] + (int(velocity[1]))
                image = cv2.arrowedLine(image, position, end, color, 2)
            
            
            if len(self.acc[track]) > 0:
                acc = self.acc[track][0]
                end = position[0] + (int(acc[0]) * 2) , position[1] + (int(acc[1]) * 2)
                image = cv2.arrowedLine(image, position, end, color, 2)
            