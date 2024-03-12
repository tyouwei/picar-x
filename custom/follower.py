from picarx import Picarx
from time import sleep
from vilib import Vilib
from motor import Motor

class Follower(object):
    def __init__(self, px, motor):
        self.px = px
        self.motor = motor
        self.x_angle = 0
        self.y_angle = 0
    
    def clamp_number(self, num, a, b):
        return max(min(num, max(a, b)), min(a, b))
    
    def follow(self, joints):
        self.make_eye_contact(joints)
        self.stalk_person(joints)
            
    def make_eye_contact(self, joints):
        # change the pan-tilt angle for track the object
        coordinate_x = ((joints[11][0] + joints[12][0]) / 2)*640
        coordinate_y = ((joints[11][1] + joints[12][1]) / 2)*480
        self.x_ange(self.x_angle / 2)

        self.y_angle -=(coordinate_y*10/480)-5
        self.y_angle = self.clamp_number(self.y_angle,0,80)
        self.px.set_cam_tilt_angle(self.y_angle)
        sleep(0.075)
        
        
       #if coordinate_x >= 640*(3/4) or coordinate_x <= 640*(1/4):
       #     self.motor.forward()
        
    def stalk_person(self, joints):
        # proximity check
        filtered_list = list(filter(lambda x : x is not None, joints))
        x_list = list(map(lambda x : x[0], filtered_list))
        y_list = list(map(lambda x : x[1], filtered_list))
                
        max_y = max(y_list) * 480
        max_x = max(x_list) * 640
        min_y = min(y_list) * 480
        min_x = min(x_list) * 640
        human_area = (max_x - min_x) * (max_y - min_y)
        coverage_ratio = human_area / (640 * 480)
                
        if coverage_ratio <= 0.25:
            self.motor.forward()
