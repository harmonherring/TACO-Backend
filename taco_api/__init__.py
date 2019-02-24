from functools import wraps

import requests
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import cross_origin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

app = Flask(__name__)

# Disable SSL certificate verification warning
requests.packages.urllib3.disable_warnings()

# Disable SQLAlchemy modification tracking
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

@app.route('/', methods=['GET'])
def test():
    return "fuck you"

@app.route('/clients', methods=['GET', 'POST'])
def get_clients():
    if request.method == 'GET':
        #return all clients
        return False
    else:
        #creates new client
        return False

@app.route('/tasks', methods=['GET','POST'])
def tasks():
    if request.method == 'GET':
        #return all tasks
        return False
    else:
        #creat a new task
        return False

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
