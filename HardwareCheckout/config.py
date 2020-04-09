#!/usr/bin/env python3
#import os
#db_path = 'sqlite://' + os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../database/db.sqlite')
xpath = "/opt/database/db.sqlite"
db_path = 'sqlite:///{}'.format(xpath)
