#!/usr/bin/env python3
import os
import re
from configparser import ConfigParser
from base64 import b64encode

from asyncinotify import Inotify, Mask
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.websocket import websocket_connect
from tornado.escape import json_decode, json_encode
from tornado.httpclient import HTTPRequest
from tornado.process import Subprocess as subprocess
from tornado.gen import sleep

ACTIVE_CLIENTS = {}
device_re = re.compile(r"^.*(device\d+)$")


class Client(object):
    devices = {}
    registered = []

    def __init__(self, url, username, password, profiles, timeout=30):
        self.url = url
        self.username = username
        self.password = password
        self.timeout = timeout
        self.profiles = profiles
        self.keep_alive_timer = None

    def __del__(self):
        self.keep_alive_timer.stop()

    def auth_header(self, username, password):
        return {
            "Authorization": "Basic "
            + b64encode((username + ":" + password).encode()).decode()
        }

    async def connect(self):
        print("trying to connect")
        try:
            self.ws = await websocket_connect(
                HTTPRequest(
                    url=self.url,
                    headers=self.auth_header(self.username, self.password),
                    connect_timeout=10,
                )
            )

            if self.keep_alive_timer == None:
                self.keep_alive_timer = PeriodicCallback(
                    self.keep_alive, self.timeout * 1000
                )
                self.keep_alive_timer.start()
            IOLoop.current().add_callback(self.recv_loop)

        except Exception:
            print("connection error")
            self.ws = None

        if self.ws is None:
            raise Exception("ws is none. Idk what happened.")

    async def recv_loop(self):
        while True:
            msg = await self.ws.read_message()
            if msg is None:
                break
            else:
                await self.handle_message(msg)

    async def keep_alive(self):
        if self.ws is None:
            try:
                await self.connect()
            except Exception:
                IOLoop.current().call_later(10, self.keep_alive)  # retry in 10 seconds
            else:
                await self.reregister_devices()
        else:
            print("Keep Alive")
            try:
                await self.ws.write_message(json_encode({"type": "keep-alive"}))
            except Exception:
                self.ws = None
                IOLoop.current().call_later(10, self.keep_alive)  # retry in 10 seconds

    async def handle_message(self, message):
        try:
            data = json_decode(message)
            msg_type = data.get("type", None)
            params = data.get("params", None)
        except Exception:
            return

        if not msg_type:
            return
        elif msg_type == "restart":
            print("Got restart request for {}".format(params))
            await self.kill(params)

    async def kill(self, device):
        for keys in self.profiles:
            if self.profiles[keys]["username"] == device:
                deviceName = keys
                break

        p = subprocess(
            ["pkill", "-u", "villager-" + deviceName],
            stdout=subprocess.STREAM,
            stderr=subprocess.STREAM,
        )

        try:
            await p.wait_for_exit()
        except Exception:
            return False
        return True

    async def register_device(self,deviceName):
        if deviceName not in self.registered: 
            self.registered.append(deviceName)
        await self.send_registration_msg(deviceName)

    async def reregister_devices(self):
        for deviceName in self.registered:
            await self.send_registration_msg(deviceName)

    async def send_registration_msg(self, device):
        await self.ws.write_message(json_encode({"type": "register", "params": device}))

class New_Device_Handler:
    def __init__(self, client, profiles={}):
        self.client = client
        self.profiles = profiles

    async def handle_create_event(self, pathname):
        print("New Device Created")
        await self.register_device(pathname, self.profiles)

    async def register_device(self, path, profiles):
        matches = device_re.match(path)
        if matches:
            profile_name = matches.group(1)

            clientProfile = profiles.get(profile_name, False)
            if clientProfile:
                print("Registering new Client: {}".format(clientProfile["username"]))
                await self.client.register_device(clientProfile["username"])


def get_profiles():
    config = ConfigParser()
    config.read("/opt/hc-client/.config.ini")

    all_profiles = {}

    for key in config:
        profile = config[key]

        if not profile.get("username", False) or not profile.get("password", False):
            continue

        settings = {
            "username": profile["username"],
            "password": profile["password"],
        }

        all_profiles[key] = settings
    return all_profiles


async def watch_directories(directories, handler):
    with Inotify() as inotify:
        for dirs in directories:
            inotify.add_watch(dirs, Mask.CREATE)

            for files in os.listdir(dirs):
                full_path = os.path.join(dirs, files)
                if os.path.isdir(full_path):
                    await handler.handle_create_event(full_path)

        async for event in inotify:
            await handler.handle_create_event(str(event.path))


async def main():
    profiles = get_profiles()

    newClient = Client(
        "wss://localhost:8080/device/controller",
        profiles["controller"]["username"],
        profiles["controller"]["password"],
        profiles,
    )
    while True:
        try:
            await newClient.connect()
            break
        except Exception:
            await sleep(10)

    DeviceHandler = New_Device_Handler(client=newClient, profiles=profiles)

    IOLoop.current().add_callback(watch_directories, ["/tmp/devices"], DeviceHandler)


if __name__ == "__main__":
    IOLoop.current().add_callback(main)
    IOLoop.current().start()
