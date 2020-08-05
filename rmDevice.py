#!/usr/bin/env python3
from HardwareCheckout import create_app
from HardwareCheckout.models import DeviceQueue, Role, DeviceType
from HardwareCheckout.config import db_path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from argparse import ArgumentParser
import sys
import os
import configparser

parser = ArgumentParser()
parser.add_argument("-d","--devicename", help="Device name", required=False)
parser.add_argument('-i', '--ini', help='Ini file containing list of devices', required=False)
args = parser.parse_args()

ession = sessionmaker(bind=create_engine(db_path))
s = session()

def iniParse(confPath):
    config = configparser.ConfigParser()
    config.read(confPath)
    result = []
    
    
    for item in config.sections():
        result.append(config[item]["username"])
    
    return result

def removeDevice(devicename):
    device = s.query(DeviceQueue).filter_by(name=devicename).first()
    if not device:
        print("no device found - {}!".format(devicename))
        sys.exit(0)
    
    s.delete(device)
    s.commit()


def printHelp():
    print("Deleting multiple devices:")
    print("python3 rmDevice.py -i <path/to/inifile>")
    print()
    print("Remove a single device:")
    print("python3 rmDevice.py -d <devicename>")
    sys.exit(1)

def main():
    if args.ini and args.devicename:
        print ("You cannot define a device name and a ini file at the same time!!")
    elif args.devicename:
        removeDevice(args.devicename)
    else:
        if not args.ini or not args.devicename:
            parser.print_help(sys.stderr)
            print ("")
            printHelp()
        if not os.path.isfile(args.ini):
            print ("Ini file {} doesn't exist!".format(args.ini))
            parser.print_help(sys.stderr)
            sys.exit(1)
        # for parsing csv files replace this with
        # csvParse(csvPath) --> Note that csvParse expects device type in the file
        devices = iniParse(args.ini) 
        
        for devicename in devices:
            removeDevice(devicename)

if __name__ == '__main__':
    main()
    