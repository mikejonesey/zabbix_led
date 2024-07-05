"""
Show Zabbix host group health using blinkstick
written for zabbix v7, after v7 brought api changes
Author: Michael Jones
Date: Fri  5 Jul 15:46:44 BST 2024
License: GPLv3
"""
import os
import configparser
from pathlib import Path
import requests
from blinkstick import blinkstick

ZABBIX_URL = os.environ["ZABBIX_URL"] or "https://zabbix.example.com/api_jsonrpc.php"
USERNAME = os.environ["ZABBIX_USERNAME"] or "zabbix"
PASSWORD = os.environ["ZABBIX_PASSWORD"] or "password123"
CONFIG_FILE = ".led.config"
# BLINKSTICK_SERIAL = "00000000"
BLINKSTICK_MAX_BRIGHTNESS = "15"


def build_config_file(auth_token):
    """
    Function Build a dummy config file that can be edited later to match led to group
    :param auth_token: from main stage, auth token
    :return: nothing
    """
    payload = {
        "method": "trigger.get",
        "params": {
            "monitored": True,
            "output": ["event_name", "priority"],
            "selectHostGroups": ["groupid", "name"],
            "sortfield": "priority",
            "sortorder": "DESC"
        },
        "auth": auth_token,
        "jsonrpc": "2.0",
        "id": 1,
    }
    response = requests.post(ZABBIX_URL, json=payload, timeout=1.5).json()
    try:
        assert response["id"] == 1, "Wrong"
        assert response["result"], "No result in response."
    except KeyError as result_error:
        print("Error: " + str(result_error))
        assert response["error"], "No error in response."
        print(response["error"])
        raise
    print("Received health stats from Zabbix.")

    my_hostgroups = {}
    for trigger in response['result']:
        group_id = trigger['hostgroups'][0]['groupid']
        group_name = trigger['hostgroups'][0]['name']
        my_hostgroups[group_id] = group_name

    config = configparser.ConfigParser()
    config.read(Path.home() / CONFIG_FILE)
    led_loop = 0
    for hostgroup in my_hostgroups.items():
        config['LED_' + str(led_loop)] = {}
        config['LED_' + str(led_loop)]['group_id'] = hostgroup
        config['LED_' + str(led_loop)]['group_name'] = my_hostgroups[hostgroup]
        led_loop += 1

    with open(Path.home() / CONFIG_FILE, 'w', encoding='UTF-8') as configfile:
        config.write(configfile)

    print("Config File Written")


def update_led(my_hostgroups_health):
    """
    Function to update LED on Blinkstick
    :param my_hostgroups_health: mapping of host groups to problems
    :return:
    """
    if 'BLINKSTICK_SERIAL' in globals():
        bstick = blinkstick.find_by_serial("BS000001-1.0")
    else:
        bsticks_found = blinkstick.find_all()
        bstick = bsticks_found[0]

    print("Updating LED...")
    config = configparser.ConfigParser()
    config.read(Path.home() / CONFIG_FILE)
    for led in config:
        if led.startswith("LED_"):
            led_id = led.replace("LED_", "")
            led_id_int = int(led_id)
            led_group_id = config[led]['group_id']
            bstick.set_max_rgb_value(int(BLINKSTICK_MAX_BRIGHTNESS))
            if led_group_id not in my_hostgroups_health.keys():
                print("LED " + led_id + " zabbix group " + led_group_id
                      + " is healthy / clear")
                bstick.set_color(0, led_id_int, 0, 0, 0, "green", "")
            else:
                print("LED " + led_id + " zabbix group " + led_group_id
                      + " is bad : " + my_hostgroups_health[led_group_id])
                if my_hostgroups_health[led_group_id] == "5":
                    # DISASTER
                    bstick.set_color(0, led_id_int, 0, 0, 0, "red", "")
                elif my_hostgroups_health[led_group_id] == "4":
                    # High
                    bstick.set_color(0, led_id_int, 0, 0, 0, "red", "")
                elif my_hostgroups_health[led_group_id] == "3":
                    # Average
                    bstick.set_color(0, led_id_int, 0, 0, 0, "", "EE6404")
                elif my_hostgroups_health[led_group_id] == "2":
                    # Warning
                    bstick.set_color(0, led_id_int, 0, 0, 0, "yellow", "")
                elif my_hostgroups_health[led_group_id] == "1":
                    # Info
                    bstick.set_color(0, led_id_int, 0, 0, 0, "blue", "")
                else:
                    # Not-Classified
                    bstick.set_color(0, led_id_int, 0, 0, 0, "gray", "")
    print("Finished...")


def get_health(auth_token):
    """
    Get current problems from zabbix
    :param auth_token: api auth token from main
    :return:
    """
    # Get Health Payload
    # -------------------------------------------------
    # Trigger Filters
    # -------------------------------------------------
    # active = Return only enabled triggers that belong to monitored hosts.
    # only_true =  Return only triggers that have recently been in a problem state.
    # skipDependent =  Skip triggers in a problem state that are dependent on other triggers.
    #   Note that the other triggers are ignored if disabled,
    #   have disabled items or disabled item hosts.
    # monitored =  Return only enabled triggers
    #   that belong to monitored hosts and contain only enabled items.
    #
    # -------------------------------------------------
    # Trigger Output
    # -------------------------------------------------
    # selectHostGroups =  Return the host groups that the trigger belongs to in the groups property.
    # expandDescription =  Expand macros in the name of the trigger.
    # "filter": {"value": 1}, = only active triggers
    # "output": ["description","priority"], = only output the required data + description
    #
    # SORT BY PRIORITY ASC (highest priority applied last to map)
    payload = {
        "method": "trigger.get",
        "params": {
            "active": 1,
            "only_true": "1",
            "skipDependent": "1",
            "monitored": 1,
            "selectHostGroups": ["groupid", "name"],
            "expandDescription": "1",
            "output": ["description", "priority"],
            "filter": {"value": 1},
            "sortfield": "priority",
            "sortorder": "ASC"
        },
        "auth": auth_token,
        "jsonrpc": "2.0",
        "id": 1,
    }
    response = requests.post(ZABBIX_URL, json=payload, timeout=1.5).json()
    try:
        assert response["result"]
    except AssertionError:
        assert response["error"]
        print(response["error"])

    my_hostgroups_health = {}
    for trigger in response['result']:
        group_id = trigger['hostgroups'][0]['groupid']
        trigger_priority = trigger['priority']
        my_hostgroups_health[group_id] = trigger_priority

    print(my_hostgroups_health)
    update_led(my_hostgroups_health)


def main():
    """
    Authenticate, fetch problems, update led
    :return:
    """
    # Auth Payload
    payload = {
        "method": "user.login",
        "params": {
            "username": USERNAME,
            "password": PASSWORD
        },
        "jsonrpc": "2.0",
        "id": 0,
    }
    response = requests.post(ZABBIX_URL, json=payload, timeout=1.5).json()
    assert response["result"]
    assert response["id"] == 0
    auth_token = response["result"]
    print("Logged into Zabbix!")

    my_file = Path(Path.home() / CONFIG_FILE)
    if not my_file.is_file():
        build_config_file(auth_token)

    get_health(auth_token)


if __name__ == "__main__":
    main()
