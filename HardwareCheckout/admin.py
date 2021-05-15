from configparser import ConfigParser
from functools import partial
from typing import Dict, Coroutine, Iterable

from sqlalchemy import func
from tornado.locks import Lock, ioloop
from tornado.web import authenticated, MissingArgumentError
from tornado_sqlalchemy import as_future

from .models import DeviceQueue, Role, DeviceType, User, UserQueue, UserRoles, ctfd_db
from .webutil import Blueprint, UserBaseHandler, make_session, Timer
from .auth import PasswordHasher
from .device import DeviceStateHandler

admin = Blueprint()


@admin.route("/", name="admin")
class AdminHandler(UserBaseHandler):
    queues: Iterable[str] = []
    queueTimer = None
    queueTimerLock = Lock()

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.ADMIN_FUNCTIONS: Dict[str, Coroutine[None, None, str]] = {
            "addDeviceType": self.addDeviceType,
            "addDevice": self.addDevice,
            "addAdmin": self.addAdmin,
            "changeDevicePassword": self.changeDevicePassword,
            "rmDevice": self.rmDevice,
            "killSession": self.killSession,
            "toggleQueue": self.toggle_queue,
        }
        if not AdminHandler.queueTimer:
            ioloop.IOLoop.current().add_callback(self.startQueueUpdateTimer)

    @classmethod
    async def startQueueUpdateTimer(cls):
        async with cls.queueTimerLock():
            if cls.queueTimer is None:
                cls.queueTimer = Timer(cls.queueUpdate, timeout=300)

    @classmethod
    async def queueUpdate(cls):
        with make_session() as session:
            try:
                cls.queues = await as_future(
                        session.query(
                            DeviceType.id,
                            DeviceType.name,
                            func.count(UserQueue.userId),
                            DeviceType.enabled,
                        )
                        .select_from(DeviceType)
                        .join(UserQueue, isouter=True)
                        .group_by(DeviceType.id, DeviceType.name)
                        .all
                    )
            except Exception:
                pass # Uhhhhh... what do?

    @authenticated
    async def get(self):
        with self.make_session() as session:
            try:
                roles = await as_future(
                    session.query(Role.name).join(UserRoles).join(User).filter(User.id==self.current_user).all
                )
                for role in roles:
                    if 'Admin' in role:
                        break
                else:
                    return self.redirect(self.reverse_url("main"))
            except Exception:
                return self.redirect(self.reverse_url("main"))

        return self.render("admin.html", queues=self.queues, messages=None)

    @authenticated
    async def post(self):
        with self.make_session() as session:
            try:
                roles = await as_future(
                    session.query(Role.name).join(UserRoles).join(User).filter(User.id==self.current_user).all
                )
                for role in roles:
                    if 'Admin' in role:
                        break
                else:
                    return self.redirect(self.reverse_url("main"))
            except Exception:
                return self.redirect(self.reverse_url("main"))

        # Try and get the type parameter so we can decide what type of request this is
        try:
            req_type = self.get_argument("type")
        except MissingArgumentError:
            return self.render("admin.html", messages="Error in form submission")

        try:
            errors = await self.ADMIN_FUNCTIONS.get(req_type, (lambda: "Invalid function"))()
        except Exception as e:
            errors = str(e)
        finally:
            if errors:
                print(
                    "Invalid Admin function by user {}: {}".format(
                        self.current_user, req_type
                    )
                )
                return self.render("error.html", error=errors)

        return self.render("admin.html", queues=self.queues, messages=errors)

    async def addDeviceType(self) -> str:
        try:
            name = self.get_argument("name")
        except MissingArgumentError:
            return "Missing device type"

        with self.make_session() as session:
            await as_future(partial(session.add, DeviceType(name=name, enabled=1)))

        await self.queueUpdate()

        return ""

    async def addDevice(self) -> str:
        try:
            device_info = self.get_argument("device_info")
            device_type = self.get_argument("device_type")
        except MissingArgumentError:
            return "Missing device type or config file info"

        config = ConfigParser()
        try:
            config.read_string(device_info)
        except KeyError:
            return "Error while trying to read the config file"

        error_msg = ""
        with self.make_session() as session:
            device_type_id = await as_future(
                session.query(DeviceType.id).filter_by(name=device_type).one
            )

            for section in config.sections():
                try:
                    session.add(
                        DeviceQueue(
                            name=config[section]["username"],
                            password=PasswordHasher.hash(config[section]["password"]),
                            state="want-provision",
                            type=device_type_id,
                        )
                    )
                except Exception as e:
                    error_msg += str(e) + "\n"
                    continue

        return error_msg

    async def addAdmin(self) -> str:
        if ctfd_db:
            return "Please use the CTFd system to manage admin roles"
        try:
            username = self.get_argument("username")
            password = self.get_argument("password")
        except MissingArgumentError:
            return "Missing username or password"

        with self.make_session() as session:
            try:
                admin = await as_future(
                    session.query(Role).filter_by(name="Admin").first
                )
                human = await as_future(
                    session.query(Role).filter_by(name="Human").first
                )
                device = await as_future(
                    session.query(Role).filter_by(name="Device").first
                )
            except Exception:
                return "Error while finding roles"

            try:
                await as_future(
                    partial(
                        session.add,
                        User(
                            name=username,
                            password=PasswordHasher.hash(password),
                            roles=[admin, human, device],
                        ),
                    )
                )
            except Exception:
                return "Error while attempting to add user"
        return ""

    async def changeDevicePassword(self) -> str:
        try:
            username = self.get_argument("username")
            password = self.get_argument("password")
        except MissingArgumentError:
            return "Missing username or password"

        with self.make_session() as session:
            try:
                device = await as_future(
                    session.query(DeviceQueue).filter_by(name=username).one
                )
                device.password = PasswordHasher.hash(password)
            except Exception:
                return "Error while updating password"

        return ""

    async def rmDevice(self) -> str:
        # TODO: is this safe to do? what are the implications if someone is connected?
        try:
            device = self.get_argument("device")
        except MissingArgumentError:
            return "Missing device"

        with self.make_session() as session:
            try:
                device = await as_future(
                    session.query(DeviceQueue).filter_by(name=device).one
                )
                await as_future(partial(session.delete, device))
            except Exception:
                return "Failed to remove device"
        return ""

    async def killSession(self) -> str:
        try:
            deviceName = self.get_argument("device")
        except MissingArgumentError:
            return "Missing Device name"

        with self.make_session() as session:
            try:
                deviceID = await as_future(
                    session.query(DeviceQueue.id).filter_by(name=deviceName).one
                )
            except Exception:
                return "Error while looking up device"

        await DeviceStateHandler.killSession(deviceID[0])
        return ""

    async def toggle_queue(self) -> str:
        try:
            queueID = self.get_argument("queue")
        except MissingArgumentError:
            return "Missing Device name"

        with self.make_session() as session:
            try:
                queue = await as_future(
                    session.query(DeviceType).filter_by(id=queueID).one
                )
            except Exception:
                return "Failed to find that queue type"

            queue.enabled = 1 if not queue.enabled else 0

        await self.queueUpdate()

        return ""
