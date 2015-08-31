#!/usr/bin/env python3

import cherrypy
import sqlite3
import os.path
from hashlib import sha512

DATABASE_DIR = "database"
DATABASE_FILE = "trollocash_development.db"
DATABASE = os.path.join(os.path.dirname(__file__), DATABASE_DIR, DATABASE_FILE)


class Trollocash(object):

    @cherrypy.expose
    def index(self):
        return "Welcome to Trollocash"

    @cherrypy.expose
    def admin(self):
        return "Welcome to Trollocash Admin Interface"

class Users(object):

    def __init__(self):
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
    users.add_user("Alice", "Password", 1)
    users.add_user("Bob", "Whatever", 0)
    users.add_user("Karen", "Gisela", 0)

    userdata = users.get_users()
    superuserdata = users.get_superusers()

    cherrypy.config.update({
        'server.socket_host': '127.0.0.1',
        'server.socket_port': 8025,
        'server.thread_pool_max': 500,
        'server.thread_pool': 100,
        'log.screen': True
    })

    trollocash = Trollocash()

    cherrypy.tree.mount(trollocash, "/", {
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

