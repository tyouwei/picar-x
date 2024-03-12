from picarx import Picarx
from vilib import Vilib
from auto_pilot import AutoPilot
from motor import Motor
from mqtt_client import MQTTClient
from position_estimate import PositionEstimator
import time
from time import sleep
import fcntl
import json
from datetime import datetime


JSON_FILE_PATH = '/home/admin/picar-x/custom/REST/data.json'
POWER = 50
SAFE_DISTANCE = 30   # > 40 safe
DANGER_DISTANCE = 20 # > 20 && < 40 turn around, 
                    # < 20 backward

class App(object):
    def __init__(self):
        self.x_coordinate = 0
        self.y_coordinate = 0
        self.mqtt_client = MQTTClient()
        self.px = Picarx()
        self.motor = Motor()
        self.auto = AutoPilot(self.px, self.motor)
        self.auto.start()
        self.is_avoiding_collision = False
        self.alert_x1 = 0.0
        self.alert_x2 = 1.0
        self.alert_y1 = 0.0
        self.alert_y2 = 1.0    
    
    # TODO: clear json file value after reading it
    def run(self):
        last_msg_time = time.time()
        while True:

            try:
                with open(JSON_FILE_PATH, 'r') as file:
                    fcntl.flock(file, fcntl.LOCK_SH)
                    data = json.load(file)
                    fcntl.flock(file, fcntl.LOCK_UN)
            except json.decoder.JSONDecodeError as json_err:
                continue
            
            insn = data['instruction']
            self.update_bot_coordinates()
            self.update_alert_zone()
            if insn == "auto":
                time_elapsed = time.time() - last_msg_time
                if time_elapsed >3:
                    last_msg_time = time.time()
                    self.send_mqtt_update("Auto")
                    
                distance = round(self.px.ultrasonic.read(), 2)
                if distance >= SAFE_DISTANCE or distance == -1: #sensor gives -1 when it fails to receive ultrasonic feedback
                    if self.is_avoiding_collision:
                        self.motor.stop()
                        self.is_avoiding_collision = False
                    self.auto.event.set() # unpauses auto thread
                elif distance >= DANGER_DISTANCE:
                    self.auto.event.clear() # pauses the auto thread
                    self.is_avoiding_collision = True
                    self.motor.right()
                    self.motor.forward()
                    sleep(1)
                elif distance >= 0: 
                    self.auto.event.clear()
                    self.is_avoiding_collision = True
                    self.motor.left()
                    self.motor.backward()
                    sleep(1)
            else:
                
                time_elapsed = time.time() - last_msg_time
                
                if time_elapsed >3:
                    last_msg_time = time.time()
                    self.send_mqtt_update("Manual")
            
                if insn == "forward":
                    self.auto.event.clear()
                    self.motor.forward()
                elif insn == "left":
                    self.auto.event.clear()
                    self.motor.left()
                elif insn == "right":
                    self.auto.event.clear()
                    self.motor.right()
                elif insn == "backward":
                    self.auto.event.clear()
                    self.motor.backward()
                elif insn == "stop":
                    self.auto.event.clear()
                    self.motor.stop()
                    
    def send_mqtt_update(self, mode):
        print(self.x_coordinate,self.y_coordinate)
        current_timestamp = datetime.now().isoformat() # add timestamp param
        print("\n", current_timestamp)
        
        message = {
            "x" : self.x_coordinate,
            "y" : self.y_coordinate,
            "status" : self.motor.get_status(),
            "mode" : mode,
            "camera-zone": self.get_cam_zone(),
            "timestamp": current_timestamp
        }
        self.mqtt_client.publish(message)

    def update_bot_coordinates(self):
        pos_estimator = PositionEstimator()
        self.x_coordinate, self.y_coordinate = pos_estimator.get_coordinates()
        #self.x_coordinate, self.y_coordinate = pos_estimator.trilaterate()
    
    def update_alert_zone(self):
        #Update Alert zone areas
        self.alert_x1 = self.mqtt_client.x1
        self.alert_x2 = self.mqtt_client.x2
        self.alert_y1 = self.mqtt_client.y1
        self.alert_y2 = self.mqtt_client.y2
        print("Trigger zone coordinates: "self.mqtt_client.x1, self.mqtt_client.x2,self.mqtt_client.y1,self.mqtt_client.y2)
        
    def get_cam_zone(self):
        #arbitrary dummy zone for camera where cam field is x is 1 to 10, y is 1 to 10
        if self.x_coordinate < self.alert_x2 and self.y_coordinate < self.alert_y2 and self.x_coordinate > self.alert_x1 and self.y_coordinate > self.alert_y1:
            return "urn:ngsi-ld:Camera:Camera001"
        else:
            return "NULL"
        

if __name__ == '__main__':
    try:
        app =App()
        app.run()
    except KeyboardInterrupt:
        Motor().stop()
        pass
