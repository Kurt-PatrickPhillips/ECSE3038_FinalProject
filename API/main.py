
import time
import json
import pandas as pd
from flask_cors import CORS
from json import load, loads
from datetime import datetime
from bson.json_util import dumps
from flask_pymongo import PyMongo
from gevent.pywsgi import WSGIServer
from flask import Flask, request, jsonify
from marshmallow import Schema, fields, ValidationError
from flask import Flask, Response,
from gevent import monkey
monkey.patch_all()


mongo_uri = "mongodb+srv://kurtp:thislab3@cluster0.wn7il.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

app = Flask(__name__)

app.config["MONGO_URI"] = mongo_uri
cors = CORS(app)
mongo = PyMongo(app)

class PatientSchema(Schema):
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    age = fields.Integer(required=True)
    patient_id = fields.String(required=True)
    
class RecordSchema(Schema):
    patient_id = fields.String(required=True)
    position = fields.Integer(required=True)
    temperature = fields.Integer(required=True)
    last_updated = fields.String(required=True)


@app.route("/api/patient", methods=["GET"])
def get_all_patient_data():

    patients = mongo.db.patients.find()
    return jsonify(loads(dumps(patients)))


@app.route("/api/patient/<id>", methods=["GET"])
def get_one_patient_data(id):

    patient = mongo.db.patients.find_one({"patient_id": id})
    return jsonify(loads(dumps(patient)))


@app.route("/api/patient", methods=["POST"])
def post_patient_data():

    try:
        now = datetime.now()
        dt = now.strftime("%d/%m/%Y %H:%M:%S")

        first_name = request.json["first_name"]
        last_name = request.json["last_name"]
        age = request.json["age"]
        patient_id = request.json["patient_id"]

        jsonBody = {
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
            "patient_id": patient_id
        }

        print(jsonBody)

        patient_data = PatientSchema().load(jsonBody)
        mongo.db.patients.insert_one(patient_data)

        return{
            "success": True,
            "message": "Added Patient",
            "date": dt
        }
    except ValidationError as e:
        return e.messages, 400


@app.route("/api/patient/<id>", methods=["PATCH"])
def patch_patient(id):

    mongo.db.patients.update_one({"patient_id": id}, {"$set": request.json})
    patient = mongo.db.patients.find_one({"patient_id": id})

    return loads(dumps(patient))


@app.route("/api/patient/<id>", methods=["DELETE"])
def delete_patient_data(id):

    result = mongo.db.patients.delete_one({"patient_id": id})

    if result.deleted_count == 1:
        return {
            "success": True,
        }
    else:
        return{
            "success": False,
        }, 400


@app.route("/api/record/graph/<id>", methods=["GET"])
def get_graph_data(id):

    def str_to_time(time_data):
        hr = int(time_data[11:13])
        min = int(time_data[14:16])
        return (60*hr + min)

    graph_data = []

    now = datetime.now()
    dt = now.strftime("%d/%m/%Y %H:%M:%S")
    curr_time = str_to_time(dt)
    print(curr_time)

    record = mongo.db.records.find({"patient_id": id})
    record_data = loads(dumps(record))
    for info in record_data:
        record_time = str_to_time(info["last_updated"])
        print(record_time)

        if ((curr_time - record_time) <= 30):
            graph_data.append(info)

    print(graph_data)
    return jsonify(loads(json.dumps(graph_data)))


@app.route("/api/record/<id>", methods=["GET"])
def get_one_record(id):

    record = mongo.db.records.find_one({"patient_id": id})
    print(record)
    return jsonify(loads(dumps(record)))


@app.route("/listen")
def listen():

    def respond_to_client():
        while True:
            global pos
            global id
            counter = 100
            _data = json.dumps({"position": str(pos), "id": id})
            yield f"id: 1\ndata: {_data}\nevent: online\n\n"
            time.sleep(3)
    return Response(respond_to_client(), mimetype='text/event-stream')


@app.route("/api/record", methods=["POST"])
def post_record_data():

    global pos
    global id
    try:
        now = datetime.now()
        dt = now.strftime("%d/%m/%Y %H:%M:%S")

        patient_id = request.json["patient_id"]
        position = request.json["position"]
        temperature = request.json["temperature"]
        last_updated = dt

        pos = position
        id = patient_id

        jsonBody = {
            "patient_id": patient_id,
            "position": position,
            "temperature": temperature,
            "last_updated": last_updated
        }

        record_data = RecordSchema().load(jsonBody)
        mongo.db.records.insert_one(record_data)

        print(jsonBody)

        return {
            "success": True,
            "msg": "data saved successfully",
            "date": dt
        }
    except ValidationError as e:
        return e.messages, 400


if __name__ == "__main__":
    http_server = WSGIServer(("192.168.0.4", 5000), app)
    http_server.serve_forever()
