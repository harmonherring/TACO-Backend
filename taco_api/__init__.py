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

@app.route('/client/register', methods=['GET'])
def verify():
    #returns a unique UID
    return False

@app.route('/client/<uid>', methods=['GET'])
def return_tasks():
    #indexes Tasks DB and returns tasks for the specifed uid
    return False

