#!/usr/bin/env python3

import cherrypy
import sqlite3
import os.path
from hashlib import sha512

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
            self.add_item("Cash Operation", "Fill/Withdraw cash from the cash register",  0, 1)

    def add_item(self, name, description, price=0, su_item=0):
        with sqlite3.connect(DATABASE) as c:
            c.execute(''' INSERT INTO 
                          items(name,
                                description,
                                price,
                                su_item) 
                          VALUES (?, ?, ?, ?) ''',
                          (name,
                           description,
                           price,
                           su_item))



class Trollocash(object):

    @cherrypy.expose
    def index(self):
        return "Welcome to Trollocash"

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
        backend.add_item("Spende",
                         "Eine Geldspende beliebiger Höhe")
        backend.add_item("Parkticket",
                         "Parkticket fürs Campgelände",
                         "8.00")
        backend.add_item("Schokoriegel",
                         "Ein Schokoriegel ist zwar nicht gesund, aber süß.",
                         "1.00")
        



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
                        'tools.sessions.on': True,
                        'tools.basic_auth.realm': 'Trollocash Login',
                        'tools.basic_auth.users': userdata,
                        'tools.basic_auth.encrypt': encrypt_pw},
            '/admin': {'tools.basic_auth.on': True,
                        'tools.sessions.on': True,
                        'tools.basic_auth.realm': 'Trollocash Admin Login',
                        'tools.basic_auth.users': superuserdata,
                        'tools.basic_auth.encrypt': encrypt_pw}
    })



    cherrypy.engine.start()
    cherrypy.engine.block()

