#!/usr/bin/env python3
"""A CLI to run our integration."""
from __future__ import absolute_import

import argparse
from dotenv import load_dotenv
import json
import logging
import os
import sys
import time

from api_token import BaseService
from mqtt_client import MQTTClient


logger = logging.getLogger(__name__)

CREDENTIALS_FILE = '.envs/creds.env'


def main():
    """Run the integration
    """
    parser = argparse.ArgumentParser(
        "Runs the YoLink integration with our IP cam."
    )

    # parser.add_argument(
    #     "-n",
    #     "--module-name",
    #     dest="module_name",
    #     type=str,
    #     help="The module name of the pipeline to import.",
    # )
    # parser.add_argument(
    #     "-kwargs",
    #     "--kwargs",
    #     dest="kwargs",
    #     default=None,
    #     help="Dict string of keyword arguments for the pipeline generation (if supported)",
    # )
    args = parser.parse_args()

    # load all credentials and settings from the env file into the env variables
    load_dotenv(CREDENTIALS_FILE, override=True)

    # if args.module_name is None or args.role_arn is None:
    #     parser.print_help()
    #     sys.exit(2)

    try:
        # create a YoLink service object, which will get the access token and can be used to make calls
        yolink_service = BaseService(uaid=os.getenv('UAID'),
                                     secret_key=os.getenv('SECRET_KEY'))

        # example call - get device list
        r = yolink_service.call_service(path='/open/yolink/v2/api',
                                        method='POST',
                                        additional_headers={},
                                        post_data={
                                            'method': 'Home.getDeviceList'
                                        })
        print(f"My device list: {r.json()}")

        # get home id - which we need to subscribe for events of our devices
        home_id = yolink_service.get_home_id()

        mqtt = MQTTClient(
            access_token=yolink_service.access_token.token,
            client_id=str(time.time()),  # which just need a unique client id
            home_id=home_id,
            transport='websockets'
        )

        mqtt.client.subscribe(f"yl-home/{home_id}/+/report", qos=0)

        # loop for 119 minutes and wait for events - after which we will exit,
        # so we don't need to worry about MQTT access token expiration in 2h
        mqtt.client.loop_start()
        time.sleep(2*60*60 - 60)
        mqtt.client.loop_stop()

        # # loop forever and wait for events
        # mqtt.loop_forever()

    except Exception as e:
        print(f"Exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
