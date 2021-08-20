#!/usr/bin/env python3

from HardwareCheckout import new_models
from sqlalchemy_schemadisplay import create_uml_graph
from sqlalchemy.orm import class_mapper

#TODO: change this to find the classes dynamically
mappers = [class_mapper(i) for i in [new_models.TwitchStream, new_models.DeviceSession, new_models.Device, new_models.DeviceType, new_models.UserQueue, new_models.UserRoles, new_models.User, new_models.Roles]]

graph = create_uml_graph(mappers)
graph.write_png('schema.png')
