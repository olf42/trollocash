#!/usr/bin/env python3

import cherrypy
import sqlite3
import os.path
from hashlib import sha512
from jinja2 import Environment, PackageLoader

DATABASE_DIR = "database"
DATABASE_FILE = "trollocash_development.db"
DATABASE = os.path.join(os.path.dirname(__file__), DATABASE_DIR, DATABASE_FILE)

class Backend(object):

    def __init__(self):
        pass

    def create_db(self):
        with sqlite3.connect(DATABASE) as c:
            c.execute(''' CREATE TABLE 
                          IF NOT EXISTS 
                          items(id INTEGER PRIMARY KEY,
                                name TEXT,
                                description TEXT,
                                price REAL,
                                visible INTEGER,
                                su_item INTEGER) ''')
            c.execute(''' CREATE TABLE 
                          IF NOT EXISTS 
                          bookings(id INTEGER PRIMARY KEY,
                                datetime TEXT,
                                item_id INTEGER,
                                details TEXT, 
                                amount INTEGER,
                                value REAL,
                                FOREIGN KEY(item_id) REFERENCES items(id)
                                ) ''')
            self.add_item(name="Cash Operation",
                          description="Fill/Withdraw cash from the cash register",
                          price=0.0,
                          visible=0,
                          su_item=1)

    def add_item(self, name, description, visible, price=0, su_item=0):
        with sqlite3.connect(DATABASE) as c:
            c.execute(''' INSERT INTO 
                          items(name,
                                description,
                                price,
                                visible,
                                su_item) 
                          VALUES (?, ?, ?, ?, ?) ''',
                          (name,
                           description,
                           price,
                           visible,
                           su_item))


    def get_visible_items(self):
        result = []
        keys = ["id", "name", "description", "price"]
        with sqlite3.connect(DATABASE) as c:
            response = c.execute(''' SELECT id,name,description,price
                          FROM items
                          WHERE visible = 1 AND
                          su_item = 0''')
        for item in response.fetchall():
            result.append(dict(zip(keys,list(item))))
        return result


class Trollocash(object):

    @cherrypy.expose
    def index(self):
        backend = Backend()
        items = backend.get_visible_items()
        template = env.get_template('index.html')
        return template.render(items=items)

    @cherrypy.expose
    def admin(self):

        return "Welcome to Trollocash Admin Interface"

class Users(object):

    def __init__(self):
        pass

    def create_db(self):
        with sqlite3.connect(DATABASE) as c:
            c.execute(''' CREATE TABLE 
                          IF NOT EXISTS 
                          users(id INTEGER PRIMARY KEY,
                                username TEXT,
                                password TEXT,
                                superuser INTEGER) ''')

    def add_user(self, username, password, superuser):
        with sqlite3.connect(DATABASE) as c:
            c.execute(''' INSERT INTO 
                          users(username, 
                                password,
                                superuser) 
                          VALUES (?, ?, ?) ''',
                          (username,
                           encrypt_pw(password),
                           superuser))

    def get_users(self):
        with sqlite3.connect(DATABASE) as c:
            self.users = c.execute(''' SELECT username,password
                          FROM users''')
        return dict(self.users.fetchall())

    def get_superusers(self):
        with sqlite3.connect(DATABASE) as c:
            self.users = c.execute(''' SELECT username,password
                          FROM users WHERE superuser = 1''')
        return dict(self.users.fetchall())

def encrypt_pw(pw):
        return sha512(pw.encode("utf-8")).hexdigest()


if __name__ == '__main__':

    env = Environment(loader=PackageLoader('trollocash', 'templates'))

    users = Users()
    backend = Backend()

    # Test Data
    if not os.path.isfile(DATABASE):
        users.create_db()
        backend.create_db()
        users.add_user("Alice",
                       "Password",
                       1)
        users.add_user("Bob",
                       "Whatever",
                       0)
        users.add_user("Karen",
                       "Gisela",
                       0)
        backend.add_item(name="Spende",
                         description="Eine Geldspende beliebiger Höhe",
                         visible=1)
        backend.add_item(name="Parkticket",
                         description="Parkticket fürs Campgelände",
                         visible=1,
                         price="8.00")
        backend.add_item(name="Schokoriegel",
                         description="Ein Schokoriegel ist zwar nicht gesund, aber süß.",
                         visible=1,
                         price="1.00")

    current_dir = os.path.dirname(os.path.realpath(__file__))

    userdata = users.get_users()
    superuserdata = users.get_superusers()

    cherrypy.config.update({
        'server.socket_host': '127.0.0.1',
        'server.socket_port': 8025,
        'server.thread_pool_max': 500,
        'server.thread_pool': 100,
        'log.screen': True
    })

    cherrypy.tree.mount(Trollocash(), "/", {
            '/': {'tools.basic_auth.on': True,
                        'tools.staticdir.on': True,
                        'tools.staticdir.dir': os.path.join(current_dir, 'public'),
                        'tools.sessions.on': True,
                        'tools.basic_auth.realm': 'Trollocash Login',
                        'tools.basic_auth.users': userdata,
                        'tools.basic_auth.encrypt': encrypt_pw},
            '/admin': {'tools.basic_auth.on': True,
                        'tools.staticdir.on': True,
                        'tools.staticdir.dir': os.path.join(current_dir, 'public'),
                        'tools.sessions.on': True,
                        'tools.basic_auth.realm': 'Trollocash Admin Login',
                        'tools.basic_auth.users': superuserdata,
                        'tools.basic_auth.encrypt': encrypt_pw}
    })



    cherrypy.engine.start()
    cherrypy.engine.block()

