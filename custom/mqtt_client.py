import paho.mqtt.client as mqtt
import json

class MQTTClient:
    def __init__(self):
        self.connect()
        self.x1 = 0.0
        self.x2 = 1.0
        self.y1 = 0.0
        self.y2 = 1.0
    def on_publish(self, client, userdata, mid):
        print(f"Message published: {mid}")

    def publish(self, json_object):
        self.client.publish(self.topic, json.dumps(json_object))
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            #added subscribe
            self.client.subscribe("/1234/Robot001/cmd")
            print("Subscribed to /1234/Robot001/cmd")

        else: 
            print("Failed to connect to MQTT broker")
            
    def on_message(self, client, userdata, msg):
        #process JSON to add coordinates, plz check code
        message_data = json.loads(msg.payload.decode())
        self.x1 = message_data["x1"]
        self.y1 = message_data["y1"]
        self.x2 = message_data["x2"]
        self.y2 = message_data["y2"]
        
    def connect(self):
        broker = "35.198.213.246"
        port = 1883
        self.topic = "/1234/Robot001/attrs"

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

        self.client.on_publish = self.on_publish
        self.client.on_connect = self.on_connect
        
        #added subscribe
        self.client.on_message = self.on_message
        
        self.client.connect(broker, port, 60)


