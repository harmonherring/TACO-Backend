import os

import requests
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import cross_origin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

app = Flask(__name__)

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
def get_clients():
    if request.method == 'GET':
        return parse_client_as_json(Client.query.all())
    elif request.method == 'PUT':
        return False

@app.route('/tasks', methods=['GET'])
def tasks():
    return parse_task_as_json(Task.query.all())

@app.route('/tasks/<uid>', methods=['GET', 'POST'])
def get_tasks():
    if request.method == 'GET':
        #returns tasks for specified UID
        return False
    else:
        #Updates the task ID by UID
        return False

@app.route('/clients/uid', methods=['POST'])
def update():
    #updates aspects of user ID by UID
    return False


def parse_task_as_json(tasks: list):
    json = []
    for task in tasks:
        json.append(return_task_json(task))
    return jsonify(json)

def return_task_json(task):
    return {
        'id': task.id,
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
