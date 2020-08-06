#!/usr/bin/env python3
from HardwareCheckout.models import User 
from HardwareCheckout.config import db_path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-u","--username", help="User name", required=True)
parser.add_argument("-p","--password", help="User password", required=True)
args = parser.parse_args()

session = sessionmaker(bind=create_engine(db_path))
s = session()

username = s.query(User).filter_by(name=args.username).first()
if not username:
    print("no user found")
    exit(0)

username.password = generate_password_hash(
                args.password, 
                method="pbkdf2:sha256:45000"
            )

s.commit()