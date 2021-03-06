from typing import Iterable, Tuple, Dict, Union

from tornado_sqlalchemy import as_future
from sqlalchemy import func, or_
from tornado import locks, ioloop


from .models import DeviceQueue, DeviceType, User, UserQueue, TwitchStream
from .webutil import Blueprint, UserBaseHandler, Timer, make_session

main = Blueprint()


@main.route("/", name="main")
class MainHandler(UserBaseHandler):
    timer = None
    RWTerminals: Iterable[Tuple[str, str]] = []
    ROTerminals: Iterable[Tuple[str, str]] = []
    queues: Iterable[Dict[str, Union[str,int]]] = []
    pictures: Iterable[Tuple[str, str, int]] = []
    tstreams: Iterable[str] = []
    lock = locks.Lock()

    def initialize(self):
        # If no background queue update thread as started, start it
        if self.timer is None:
            ioloop.IOLoop.current().add_callback(self.startTimer)

    @classmethod
    async def startTimer(cls):
        async with cls.lock:  # we don't want the overhead of getting the lock EVERY loop, so this should be fine
            if cls.timer is None:
                print("Scheduling")
                cls.timer = Timer(cls.updateQueues, timeout=5)

    async def get(self):
        """
        Home path for the site

        :return:
        """
        # default values
        terminals = self.ROTerminals
        tstreams = self.tstreams
        pictures = self.pictures
        devices = []
        queues = []
        adminuser = False
        show_streams = True

        # check if use is logged in
        if self.current_user:
            with self.make_session() as session:
                # check if the user is an admin
                try:
                    current_user: User = await as_future(
                        session.query(User).filter_by(id=self.current_user).one
                    )
                except Exception:
                    pass
                else:
                    if current_user.has_roles("Admin"):
                        adminuser = True
                        terminals = self.RWTerminals
                        show_streams = False
                    
                    # Get any devices the user may own.
                    devices = await current_user.get_owned_devices_async(session)
                    devices = [
                        {"name": dev[0], "sshAddr": dev[1], "webUrl": dev[2]}
                        for dev in devices
                    ]

            queues = self.queues

        self.render(
            "index.html",
            devices=devices,
            tstreams=tstreams,
            queues=queues,
            show_streams=show_streams,
            terminals=terminals,
            pictures=pictures,
            adminuser=adminuser,
        )

    @classmethod
    async def updateQueues(cls):
        async with cls.lock:
            with make_session() as session:
                cls.RWTerminals = await as_future(
                    session.query(User.name, DeviceQueue.roUrl, DeviceQueue.webUrl, DeviceQueue.sshAddr)
                    .join(User.deviceQueueEntry)
                    .filter_by(state="in-use")
                    .all
                )
                cls.queues = [
                    {"id": item[0], "name": item[1], "size": item[2]}
                    for item in await as_future(
                        session.query(
                            DeviceType.id,
                            DeviceType.name,
                            func.count(UserQueue.userId),
                        )
                        .select_from(DeviceType)
                        .filter_by(enabled=1)
                        .join(UserQueue, isouter=True)
                        .group_by(DeviceType.id, DeviceType.name)
                        .all
                    )
                ]
                cls.ROTerminals = await as_future(
                    session.query(User.name, DeviceQueue.roUrl)
                    .join(User.deviceQueueEntry)
                    .filter(DeviceQueue.state == "in-use")
                    .filter(User.ctf == 0)
                    .all
                )
                cls.tstreams = await as_future(session.query(TwitchStream.name).all)
                cls.pictures = await as_future(
                    session.query(
                        DeviceType.image_path, DeviceType.name, DeviceType.enabled
                    ).all
                )
