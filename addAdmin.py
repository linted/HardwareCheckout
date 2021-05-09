#!/usr/bin/env python3
from argparse import ArgumentParser

from HardwareCheckout.models import User, Role
from HardwareCheckout.config import db_path
from HardwareCheckout.auth import PasswordHasher

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


parser = ArgumentParser()
parser.add_argument("-u", "--username", help="Admin user name", required=True)
parser.add_argument("-p", "--password", help="Admin user password", required=True)
args = parser.parse_args()
# parser.add_argument("Roles", nargs='+')

session = sessionmaker(bind=create_engine(db_path))
s = session()

admin = s.query(Role).filter_by(name="Admin").first()
human = s.query(Role).filter_by(name="Human").first()
device = s.query(Role).filter_by(name="Device").first()

s.add(
    User(
        name=args.username,
        password=PasswordHasher.hash(args.password),
        roles=[admin, human, device],
    )
)
s.commit()