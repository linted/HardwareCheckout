#!/usr/bin/env python3
import sys
from argparse import ArgumentParser

from HardwareCheckout.models import DeviceType
from HardwareCheckout.config import db_path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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
    if input("ARE YOU SURE YOU KNOW WHAT YOU ARE DOING? DEVICES COULD BE LOST LIKE THIS! [y/N] ").lower() != 'y':
        print("Good, think about what you almost did!")
        exit(0)

    args = parser.parse_args()
    removeDeviceType(args.type)


if __name__ == "__main__":
    main()
