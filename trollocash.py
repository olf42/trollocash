#!/usr/bin/env python3

import cherrypy
import datetime
import sqlite3
import os.path
from hashlib import sha512
from jinja2 import Environment, PackageLoader

DATABASE_DIR = "database"
DATABASE_FILE = "trollocash_development.db"
DATABASE = os.path.join(os.path.dirname(__file__), DATABASE_DIR, DATABASE_FILE)
TICKET_PREFIX = "PC16"
LOG_TYPE = {0:"info",
            1:"warning",
            2:"error"}
LOG_DISPLAY = {0:"success",
               1:"warning",
               2:"danger"}

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
            c.execute(''' CREATE TABLE 
                          IF NOT EXISTS 
                          log(id INTEGER PRIMARY KEY,
                                datetime TEXT,
                                message TEXT,
                                type INTEGER
                                ) ''')
            self.write_log("Tables created")
            self.add_item(name="Cash Operation",
                          description="Fill/Withdraw cash from the cash register",
                          price=0.0,
                          visible=0,
                          su_item=1)


    def write_log(self, message, logtype=0):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")
        with sqlite3.connect(DATABASE) as c:
            c.execute(''' INSERT INTO 
                          log(datetime,
                              message,
                              type)
                          VALUES (?, ?, ?) ''',
                          (now,
                           message,
                           logtype))


    def get_log(self):
        result = []
        keys = ["datetime", "message", "type"]
        with sqlite3.connect(DATABASE) as c:
            response = c.execute(''' SELECT datetime, message, type
                          FROM log
                          ORDER BY datetime DESC''')
        for item in response.fetchall():
            itemdict =dict(zip(keys,list(item)))
            result.append(itemdict)
        return result


    def add_item_id(self, itemid, name, description, visible, price=0, su_item=0):
        if not self.get_item_id(itemid):
            with sqlite3.connect(DATABASE) as c:
                c.execute(''' INSERT INTO 
                              items(id,
                                    name,
                                    description,
                                    price,
                                    visible,
                                    su_item) 
                              VALUES (?, ?, ?, ?, ?, ?) ''',
                              (itemid,
                               name,
                               description,
                               price,
                               visible,
                               su_item))
            self.write_log("Item {0} added".format(itemid))
        else:
            raise KeyError

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
        self.write_log("Item {0} added".format(name))

    def get_item_id(self, itemid):
        keys = ["name", "description", "price"]
        with sqlite3.connect(DATABASE) as c:
            response = c.execute(''' SELECT name,description,price
                          FROM items
                          WHERE id = ?''',
                          (itemid,))
            return dict(zip(keys,list(response.fetchall())))

    def get_item_string(self, searchstring):
        keys = ["name", "description", "price"]
        with sqlite3.connect(DATABASE) as c:
            response = c.execute(''' SELECT name,description,price
                          FROM items
                          WHERE description like ?''',
                          ('%'+searchstring+'%',))
            return dict(zip(keys,list(response.fetchall())))

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

    def process_book_request(self, kwargs):
        pass

class Trollocash(object):

    def process_request(self, kwargs):
        try:
            searchstring = kwargs['searchstring']
        except:
            raise KeyError

        backend = Backend()

        # Either a Barcode with specific prefix
        # Or a ticket-ID
        # Or a search String
        if searchstring.startswith(TICKET_PREFIX):
            itemid= searchstring.split('/')[-1]
            ticket = backend.get_item_id(itemid)
        else:
            try:
                itemid = int(searchstring)
                ticket = backend.get_item_id(itemid)
            except:
                ticket = backend.get_item_string(searchstring)
        if ticket:
            return {'text':ticket['name']}
        else:
            return {'text':"Nothing found"}

    @cherrypy.expose
    def index(self, **kwargs):
        backend = Backend()
        items = backend.get_visible_items()
        template = env.get_template('index.html')
        if len(kwargs)>0:
            infoblock = self.process_request(kwargs)
            return template.render(items=items, infoblock=infoblock)
        return template.render(items=items)

class Trolloadmin(object):

    def __init__(self):
        self.backend_ = Backend()

    @cherrypy.expose
    def index(self):

        return "Welcome to Trollocash Admin Interface"

    @cherrypy.expose
    def log(self):
        template = env.get_template('log.html')
        logs = self.backend_.get_log()
        for message in logs:
            message['type'] = LOG_DISPLAY[message['type']]
        return template.render(logs=logs)

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
        backend.add_item_id(itemid=123123123,
                         name="Ticket",
                         description="Peter Müller\nBungalow 151\nBett 4",
                         visible=0,
                         price="0.00")
        backend.add_item_id(itemid=456456456,
                         name="Ticket",
                         description="Frank Zander\nBungalow 9\nBett 1",
                         visible=0,
                         price="0.00")

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
                  'tools.basic_auth.encrypt': encrypt_pw}
    })
    cherrypy.tree.mount(Trolloadmin(), "/admin", {
            '/': {'tools.basic_auth.on': True,
                  'tools.staticdir.on': True,
                  'tools.staticdir.dir': os.path.join(current_dir, 'public'),
                  'tools.sessions.on': True,
                  'tools.basic_auth.realm': 'Trollocash Admin Login',
                  'tools.basic_auth.users': superuserdata,
                  'tools.basic_auth.encrypt': encrypt_pw}
    })



    cherrypy.engine.start()
    cherrypy.engine.block()

