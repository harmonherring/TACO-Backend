import os
from random import randint
import json

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

    def __init__(self, id, name, target, port, chunksize):
        self.id = id
        self.name = name
        self.target = target
        self.port = port
        self.chunksize = chunksize


class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    task_id = db.Column(db.Integer)
    active = db.Column(db.Integer)

    def __init__(self, id, name, task_id, active):
        self.id = id
        self.name = name
        self.task_id = task_id
        self.active = active


@app.route('/', methods=['GET'])
def test():
    return "dick..."


@app.route('/clients', methods=['GET', 'PUT'])
def all_clients():
    if request.method == 'GET':
        return parse_client_as_json(Client.query.all())
    elif request.method == 'PUT':
        return False


@app.route('/tasks', methods=['GET', 'PUT'])
def all_tasks():
    if request.method == 'GET':
        return parse_task_as_json(Task.query.all()), 200
    elif request.method == 'PUT':
        # Get Parameters
        name = request.args.get('name')
        target = request.args.get('target')
        port = request.args.get('port')
        chunksize = request.args.get('chunksize')

        # Create uuid
        id = randint(0, 999999999)
        while not is_key_unique(id):
            id = randint(0, 999999999)

        # Add New Task
        new_task = Task(id=id, name=name, target=target, port=port, chunksize=chunksize)
        db.session.add(new_task)
        db.session.flush()
        db.session.commit()
        return jsonify(return_task_json(new_task)), 201


@app.route('/tasks/<uid>', methods=['GET', 'PUT', 'DELETE'])
def singular_task(uid):
    if request.method == 'GET':
        return parse_task_as_json(Task.query.filter_by(id=uid).all()), 200
    elif request.method == 'PUT':
        # Get Data for the matching task
        task = Task.query.filter_by(id=uid).first()
        task.name = request.args.get('name')

        # Determine what data is in the PUT method, fill in the blanks
        if request.args.get('name'):
            task.name = request.args.get('name')
        if request.args.get('target'):
            task.target = request.args.get('target')
        if request.args.get('port'):
            task.port = request.args.get('port')
        if request.args.get('chunksize'):
            task.chunksize = request.args.get('chunksize')

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
    if request.method == 'GET':
        return parse_client_as_json(Client.query.filter_by(id=uid).all()), 200
    elif request.method == 'PUT':
        # Get data for referenced client
        client = return_client_json(Client.query.filter_by(id=uid).all()[0])

        # Determine what is being changed
        if request.args.get('name'):
            client.name = request.args.get('name')
        if request.args.get('task_id'):
            client.task_id = request.args.get('task_id')
        if request.args.get('active'):
            client.active = request.args.get('active')

        # Perform update
        db.session.flush()
        db.session.commit()
        return jsonify(return_client_json(client)), 201
    elif request.method == 'DELETE':
        Client.query.filter_by(id=uid).delete()
        db.session.flush()
        db.session.commit()
        return "Success", 200


def parse_task_as_json(tasks: list):
    json = []
    for task in tasks:
        json.append(return_task_json(task))
    return jsonify(json)


def return_task_json(task):
    return {
        'id': task.id,
        'name': task.name,
        'target': task.target,
        'port': task.port,
        'chunksize': task.chunksize,
    }


def parse_client_as_json(clients: list):
    json = []
    for client in clients:
        json.append(return_client_json(client))
    return jsonify(json)


def return_client_json(client):
    return {
        'id': client.id,
        'name': client.name,
        'task_id': client.task_id,
        'active': client.active,
    }

def is_key_unique(key):
    if Task.query.filter_by(id=key).all():
        return False
    return True
