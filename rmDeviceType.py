#!/usr/bin/env python3
from HardwareCheckout import create_app
from HardwareCheckout.models import DeviceQueue, Role, DeviceType
from HardwareCheckout.config import db_path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from argparse import ArgumentParser
import sys
import os

parser = ArgumentParser()
parser.add_argument("-t", "--type", help="Device type to add", required=True)


session = sessionmaker(bind=create_engine(db_path))
s = session()




def removeDeviceType(deviceType):
    device = s.query(DeviceType).filter_by(name=deviceType).first()
    if not device:
        print("no device type found - {}!".format(deviceType))
        sys.exit(0)

    s.delete(device)
    s.commit()


def main():
    args = parser.parse_args()
    removeDeviceType(args.type)


if __name__ == "__main__":
    main()
