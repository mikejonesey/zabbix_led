# zabbix_led

zabbix 7.0 led monitoring, allows for mapping zabbix host groups to blinkstick LED.

I was using a little bash script to do this, but zabbix upgraded the api in v7, so made a little python script, easier to maintain.

## Example Image

![zabbix-blinkstick](https://github.com/mikejonesey/zabbix_led/assets/8503626/27b55887-0c52-45d7-933b-03e7597c9516)


## Config file

The config file, mapping host group to led is auto generated when it doesn't exist, but if it exists is not overwritten, so led can be re-mapped.

default config path:

- ~/.led.config

example config file:

```
[LED_0]
group_id = 4
group_name = Zabbix servers

[LED_1]
group_id = 8
group_name = Hypervisor

[LED_2]
group_id = 14
group_name = Virtual Machines

[LED_3]
group_id = 12
group_name = Raspberry Pi

[LED_6]
group_id = 22
group_name = Kubernetes

[LED_7]
group_id = 2
group_name = Linux Servers

```
