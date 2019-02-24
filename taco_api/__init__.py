from functools import wrapimport os

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

@app.route('/', methods=['GET'])
def test():
    return "fuck you"

@app.route('/clients', methods=['GET', 'POST'])
def get_clients():
    if flask.request.method == 'GET':
        return "all clients"

@app.route('/tasks', methods=['GET'])
def tasks():
    return "here some tasks"

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

#text commit
