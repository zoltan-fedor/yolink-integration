## YoLink Integration - to trigger custom local action

This project is just a quick repo I threw together in 3 hours
to integrate with some YoLink sensors 
to trigger some custom local activity in your home based on the event of that
sensor.
It uses Python and the YoLink API http://doc.yosmart.com/docs/account/Manage to retrieve
the Access Token and then use the MQTT API of YoLink to subscribe for the sensor's events
and trigger whatever needs to be triggered when a certain event has arrived.

Add your logic for the custom event filtering and handling to 
`mqtt_client.py` file's `MQTTClient.on_message()` method.

### How to get your YoLink API User Access Credentials?

1. Open the YoLink mobile app (I did it on Android) and open the left sidebar nav.
2. Open Settings > Account > Advanced Settings > User Access Credentials
3. Hit the + sign button in the bottom right and confirm to request access credentials.
4. You should now see a UAID (User Access Id) and Secret Key.
5. You will need to save these into the  `.envs/creds.env` file - see later

You can use the UAID and the Secret Key to request an Access Key (normal Bearer token):
```
$ curl -X POST -d "grant_type=client_credentials&client_id=${UAID}&client_secret=${Secret Key of PAC}" \
https://api.yosmart.com/open/yolink/token
```

This will return the access token with a 2h expiration and also the refresh token

To test your Access Token, you can query your list of devices:
```
$ curl --location --request POST 'https://api.yosmart.com/open/yolink/v2/api' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer ${access_token}' \
  --data-raw '{
      "method":"Home.getDeviceList"
  }'
```

### Store your UAID and Secret Key in the `.envs/creds.env` file

Use the `.envs/creds.env.template` file to create a `.envs/creds.env` file and
store your UAID (User Access Id) and Secret Key there. This is from where
Python will be picking up your credentials.

### How to setup the project

Use `pipenv` to setup your Python virtual env within this directory
after cloning it from git:
```
$ pipenv --python 3.10
$ pipenv shell
$ pipenv install
```

### To run the integration script

```
# make sure you activate your Python virtual env
$ pipenv shell
(yolink-integration) $ python main.py
```

You will probably want to run this as a service, so it is always running,
which is probably easiest to do with something like `supervisord`.

### Debugging

You can use the following to subscribe to the MQTT channel of all devices of your
home, if you want to see the events manually:
```
$ mosquitto_sub -u [access_token] -p 8003 -h api.yosmart.com \
  -t yl-home/[Your Home ID - retrieved by a Home.getGeneralInfo call]/+/report
```