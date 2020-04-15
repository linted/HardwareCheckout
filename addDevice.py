#!/usr/bin/env python3
from HardwareCheckout import db, create_app
from HardwareCheckout.models import DeviceQueue, Role, DeviceType
from HardwareCheckout.config import db_path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from argparse import ArgumentParser
import os
import configparser


parser = ArgumentParser()
parser.add_argument('-u', '--username', dest='username', required=False)
parser.add_argument('-p','--password', dest='password', required=False)
parser.add_argument('-t', '--type', dest='devtype', required=False)
parser.add_argument('-i', '--init', help='Init file containing list of users', dest='initfile', required=False)
#parser.add_argument('-l', '--list', help='File containing list of users', dest='userlist', required=False)
args = parser.parse_args()
# parser.add_argument("Roles", nargs='+')

session = sessionmaker(bind=create_engine(db_path))
s = session()


def deviceAdd(username, password, devtype):
    device = s.query(Role).filter_by(name="Device").first()
    typeID = s.query(DeviceType).filter_by(name=devtype).first()

    if not typeID:
        print("Invalid type")
        exit(1)
    
    s.add(
    DeviceQueue(
        name=username, 
        password=generate_password_hash(
            password, 
            method="pbkdf2:sha256:45000"
        ),
        state="want-provision",
        type=typeID.id
    )
    )
    s.commit()


def iniParse(confPath, devType):
    config = configparser.ConfigParser()
    config.read(confPath)
    result = []
    
    
    for item in config.sections():
        innerList = []
        innerList.append(config[item]["username"])
        innerList.append(config[item]["password"])
        innerList.append(devType)
        result.append(innerList)
    
    return result
    
def csvParse(csvPath):
    with open(csvPath, 'r') as ulist:
        try:
            users = list(filter(bool, ulist.read().split('\n')))
            result = []
            for user in users:
                components = user.split(",")
                if len(components) < 2:
                    print("Parameter missing in line {}".format(user))
                    exit(1)
                else:
                    result.append(components)
        except:
            print("Couldn't read {}, {}".format(args.initfile))
            exit(1)
            
    return result

def printHelp():
    print("Adding multiple devices:")
    print("python3 addDevice.py -i <path/to/initfile> -t <devicetype>")
    print()
    print("Add a single device:")
    print("python3 addDevice.py -u <devicename> -p <password> -t <devicetype>")
    exit(1)
    
def main():
    if args.initfile and (args.username or args.password) and not args.devtype:
        print ("You cannot define username, password, but must define device type when you define a init file!!")
    elif args.username and args.password and args.devtype:
        deviceAdd(args.username,args.password,args.devtype)
    else:
        if not args.initfile or not args.devtype:
            printHelp()
        if not os.path.isfile(args.initfile):
            print ("Init file {} doesn't exist!".format(args.initfile))
            exit(1)
        # for parsing csv files replace this with
        # csvParse(csvPath) --> Note that csvParse expects device type in the file
        users = iniParse(args.initfile, args.devtype) 
        
        for user in users:
            print(user)
            #deviceAdd(user[0],user[1],user[2])

if __name__ == '__main__':    
    main()
