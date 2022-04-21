import paho.mqtt.client as mqtt
from time import time


class MQTTClient:
    """Creating an MQTT Client to work with the MQTT API

    See https://pypi.org/project/paho-mqtt
    """

    def __init__(self, access_token: str, client_id: str, home_id: str, transport: str = 'tcp'):
        """

        :param access_token:
        :param client_id:
        :param home_id: HomeId retrieved via the HTTP API
        :param transport: 'tcp' or 'websockets'
        """

        # this is required to subscribe to events coming from the devices of the given home
        self.home_id = home_id

        # create an MQTT Client
        self.client = mqtt.Client(client_id=client_id,
                                  clean_session=True,
                                  userdata=None,
                                  protocol=mqtt.MQTTv311,
                                  transport=transport  # websocket or tcp
                                  )
        self.client.username_pw_set(username=access_token)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_log = self.on_log
        self.client.connect(host="api.yosmart.com",
                            port=8003 if transport == 'tcp' else 8004,
                            keepalive=60)

    def on_connect(self, client, userdata, flags, rc):
        """The callback for when the client receives a CONNACK response from the server."""
        print("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(f"yl-home/{self.home_id}/+/report")

    def on_message(self, client, userdata, msg):
        """The callback for when a PUBLISH message is received from the server."""
        print(msg.topic + " " + str(msg.payload))

        # TODO - this is where you would add your code which would filter the events
        # and trigger whatever needs to be triggered for specific events

    @classmethod
    def on_log(cls, client, userdata, level, buff):
        print(f"Log from MQTT: {buff}")

    def loop_forever(self):
        """Blocking call that processes network traffic, dispatches callbacks and
        handles reconnecting.
        Other loop*() functions are available that give a threaded interface and a
        manual interface.
        """
        self.client.loop_forever()
