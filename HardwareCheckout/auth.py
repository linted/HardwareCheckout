
from functools import partial


from passlib.context import CryptContext
from tornado.web import RequestHandler, MissingArgumentError, authenticated
from tornado_sqlalchemy import SessionMixin, as_future


from .models import User, Role, db
from .webutil import Blueprint, UserBaseHandler

auth = Blueprint()

PasswordHasher = CryptContext(schemes=("bcrypt_sha256","pbkdf2_sha256"), pbkdf2_sha256__default_rounds=45000)


@auth.route("/login", name="login")
class LoginHandler(UserBaseHandler):
    async def post(self):
        """
        Path that handles the actual logging in of users. All super basic at this point.
        """
        # Try and get the parameters we care about, exception is thrown if non existent
        try:
            name = self.get_argument("name")
            password = self.get_argument("password")
        except MissingArgumentError:
            return self.render("login.html", messages="Missing username or password")

        # Make sure that they are actual values and not just empty.
        if not name or not password:
            return self.render("login.html", messages="Invalid username or password")

        # Do a user lookup for the provided username
        try:
            with self.make_session() as session:
                userId, userHash = await as_future(
                    session.query(User.id, User.password).filter_by(name=name).first
                )
        except Exception:
            return self.render("login.html", messages="Invalid username or password")

        # Check if they provided the right password
        if not userPass or not PasswordHasher.verify(password, userHash):
            return self.render("login.html", messages="Invalid username or password")

        # Successful login, they deserve a cookie
        self.set_secure_cookie("user", str(userId), expires_days=2)
        return self.redirect(self.reverse_url("main"))

    def get(self):
        """
        Serves the html for the login page.
        """
        return self.render("login.html", messages=None)


@auth.route("/signup")
class SignUpHandler(UserBaseHandler):
    def get(self):
        """
        Serves the html for the signup page
        """
        return self.render("signup.html", messages=None)

    async def post(self):
        """
        Super basic signup handler
        """
        # Try and get the parameters we care about, exception is thrown if non existent
        try:
            name = self.get_argument("name")
            password = self.get_argument("password")
        except MissingArgumentError:
            return self.render("signup.html", messages="Missing username or password")

        try:
            ctf = 1 if self.get_argument("ctf") is not None else 0
        except Exception:
            ctf = 0

        with self.make_session() as session:
            # Check and see if that username already exists
            user = await as_future(session.query(User).filter_by(name=name).first)

            if user:
                return self.render("signup.html", messages="User name already exists")

            # Get a copy of the human role
            roles = await as_future(session.query(Role).filter_by(name="Human").first)

            # Create the new user entry
            new_user = User(
                name=name,
                password=PasswordHasher.hash(password),
                ctf=ctf,
                roles=[roles],
            )

            # add it to the db
            session.add(new_user)

        return self.redirect(self.reverse_url("login"))


@auth.route("/logout", name="logout")
class LogoutHandler(UserBaseHandler):
    @authenticated
    def get(self):
        """
        Path that handles logging a user out.
        """
        self.clear_cookie("user")
        return self.redirect(self.reverse_url("main"))
