#!/usr/bin/env python3
import configparser
import argparse
from os import mkdir,urandom

parser = argparse.ArgumentParser()
parser.add_argument("prefix", help="device name prefix")
parser.add_argument("count", type=int)
args = parser.parse_args()

try:
    mkdir("/tmp/devices/")
except Exception:
    pass

config = configparser.ConfigParser()
for i in range(args.count):
    name = "device{}".format(i)
    data_dir = "/tmp/devices/{}".format(name)
    try:
        mkdir(data_dir)
    except Exception:
        pass
    config[name] = {
        "username": "{}-{}".format(args.prefix, name),
        "password":  urandom(32).hex(),
        "data_dir": data_dir,
    }

config["controller"] = {
    "username": "{}-controller".format(args.prefix),
    "password":  urandom(32).hex(),
}

with open("/opt/hc-client/.config.ini", "w") as confout:
    config.write(confout)

