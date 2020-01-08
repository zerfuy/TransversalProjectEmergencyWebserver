# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2019 Grey Li
    :license: MIT, see LICENSE for more details.
"""
from flask import Flask, render_template
from flask_assets import Environment, Bundle
from flask_ckeditor import CKEditor
import json
import psycopg2
import ctypes
import serial
import sys
import requests
from flask_debugtoolbar import DebugToolbarExtension
import logging

app = Flask(__name__)
app.debug = True
app.secret_key = 'development key'

toolbar = DebugToolbarExtension(app)
assets = Environment(app)
ckeditor = CKEditor(app)

css = Bundle('css/bootstrap.min.css',
             'css/bootstrap.css',
             'css/dropzone.min.css',
             'css/jquery.Jcrop.min.css',
             'css/style.css',
             'css/leaflet-routing-machine.css',
             'css/leaflet.css',
             filters='cssmin', output='gen/packed.css')

js = Bundle('js/jquery.min.js',
            'js/popper.min.js',
            'js/bootstrap.min.js',
            'js/bootstrap.js',
            'js/moment-with-locales.min.js',
            'js/dropzone.min.js',
            'js/jquery.Jcrop.min.js',
            'js/leaflet-routing-machine.js',
            'js/leaflet.js',
            filters='jsmin', output='gen/packed.js')

assets.register('js_all', js)
assets.register('css_all', css)

def SendInflux():
    user = ''
    password = ''
    dbname = 'historisation'
    dbuser = ''
    dbuser_password = 'my_secret_password'
    json_body = [
        {
            "measurement": "analysis_data",
            "tags": {
                "type": "fire",
            },
            "time": str(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')),
            "fields": {
                "Float_value": 0.64,
                "Int_value": 3,
                "String_value": "Text",
                "Bool_value": True
            }
        }
    ]

    client = InfluxDBClient(host, port, user, password, dbname)

    print("Create database: " + dbname)
    client.create_database(dbname)

    print("Write points: {0}".format(json_body))
    client.write_points(json_body)


def getSer():
    if sys.platform.startswith('win'):
        SERIALPORT = "COM4"
    else:
        SERIALPORT = "/dev/ttyUSB1"

    return serial.Serial(
        port=SERIALPORT,
        baudrate=115200
    )


# potential improvments : 
# async calls via multiple connections
@app.route('/')
def index():

    # read serial port to get fires
    ser = getSer()

    a = ""

    try:
        pass
        a = ser.readline()
        ser.close()
    except serial.SerialException:
        ser.close()
        print("Serial {} port not available".format(SERIALPORT))

    tab = []
    finalfires = []
    tab = str(a, 'utf-8').split(";")
    for fire in tab:
        finalfires.append(fire.split(","))

    try:
        # establish database connection
        conn = psycopg2.connect(
            host="manny.db.elephantsql.com",
            database="ngcbqvhq",
            user="ngcbqvhq",
            password="Ppjleq3n6HQF5qPheDze2QFzG4LHxTAf")

        # initialise all database info
        fire_engine_table = {}
        fire_engine_table["fire_engine_id"] = "id"
        fire_engine_table["fire_engine_id_station"] = "id_station"
        fire_engine_table["fire_engine_x_pos"] = "x_pos"
        fire_engine_table["fire_engine_y_pos"] = "y_pos"
        fire_engine_table["fire_engine_table_name"] = "fire_engine"

        intervention_table = {}
        intervention_table["intervention_id"] = "intervention.id"
        intervention_table["intervention_id_fire_engine"] = "id_fire_engine"
        intervention_table["intervention_id_fire"] = "id_fire"
        intervention_table["intervention_table_name"] = "intervention"
        intervention_table["intervention_route"] = "route"

        fire_table = {}
        fire_table["fire_id"] = "fire.id"
        fire_table["fire_id_real_pos"] = "fire.id_real_pos"
        fire_table["fire_intensity"] = "intensity"
        fire_table["fire_table_name"] = "fire"

        real_pos_table = {}
        real_pos_table["real_pos_id"] = "real_pos.id"
        real_pos_table["real_pos_real_x"] = "real_x"
        real_pos_table["real_pos_real_y"] = "real_y"
        real_pos_table["real_pos_name"] = "real_pos"

        cur = conn.cursor()

        #Update all fires in EM database
        for fire in finalfires:
            cur.execute("UPDATE {0} set {1} = {2} where {3} = {4}".format(
                fire_table["fire_table_name"],
                fire_table["fire_intensity"],
                str(fire[1]),
                fire_table["fire_id"],
                str(fire[0]))
            )
        conn.commit()

        # get fire_engines
        cur.execute("select {0}, {1}, {2} from {3} where {4} in (select {5} from {6})".format(
            fire_engine_table["fire_engine_x_pos"],
            fire_engine_table["fire_engine_y_pos"],
            fire_engine_table["fire_engine_id"],
            fire_engine_table["fire_engine_table_name"],
            fire_engine_table["fire_engine_id"],
            intervention_table["intervention_id_fire_engine"],
            intervention_table["intervention_table_name"])
        )
        fire_engines = []
        row = cur.fetchone()
        while row is not None:
            fire_engines.append(list(row))
            row = cur.fetchone()

        # get fire_engines positions
        fire_engines_pos = []
        for elem in fire_engines:
            fire_engines_pos.append(elem[:-1])


        # get active fires to disp
        cur.execute("select {0}, {1}, {2}, intensity from {3}, {4} where {5} = {6} and intensity > 0".format(
            real_pos_table["real_pos_real_x"],
            real_pos_table["real_pos_real_y"],
            fire_table["fire_id"],
            fire_table["fire_table_name"],
            real_pos_table["real_pos_name"],
            fire_table["fire_id_real_pos"],
            real_pos_table["real_pos_id"])
        )
        firesToDisp = []
        row = cur.fetchone()
        while row is not None:
            firesToDisp.append(list(row))
            row = cur.fetchone()


        # get fires
        cur.execute("select {0}, {1}, {2} from {3}, {4} where {5} = {6}".format(
            real_pos_table["real_pos_real_x"],
            real_pos_table["real_pos_real_y"],
            fire_table["fire_id"],
            fire_table["fire_table_name"],
            real_pos_table["real_pos_name"],
            fire_table["fire_id_real_pos"],
            real_pos_table["real_pos_id"])
        )
        fires = []
        row = cur.fetchone()
        while row is not None:
            fires.append(list(row))
            row = cur.fetchone()
        

        # get active fires positions
        fire_pos = []
        for elem in fires:
            fire_pos.append(elem[:-1])

        # get all interventions, so we can use fire/engine link
        cur.execute("select {0}, {1}, {2} from {3}".format(
            intervention_table["intervention_id_fire_engine"],
            intervention_table["intervention_id_fire"],
            intervention_table["intervention_id"],
            intervention_table["intervention_table_name"]
            ))
        interventions_complex = []
        row = cur.fetchone()
        while row is not None:
            interventions_complex.append(list(row))
            row = cur.fetchone()
        interventions = []
        for elem in interventions_complex:
            interventions.append(elem[:-1])

        # Establish itineraries from fire_engines to active fires, according to the existing interventions
        fromTo = []
        for intervention in interventions:
            idEngine = intervention[0]
            idFire = intervention[1]
            fromEngine = []
            toFire = []
            for item in fire_engines:
                if item[2] == idEngine:
                    fromEngine = item[:-1]
            for item in fires:
                if item[2] == idFire:
                    toFire = item[:-1]
            fromTo.append([fromEngine, toFire])


        # TODO influx insert

        # Parse fire_engines from 0 à x, donc on peut attribuer les chemins sans le meme ordre
        routingInfo = list()
        for ft in fromTo:
            link = "http://router.project-osrm.org/route/v1/driving/" + str(ft[0][1]) + "," + str(ft[0][0]) + ";" + str(ft[1][1]) + "," + str(ft[1][0]) + "?overview=full"
            if "routes" in requests.get(link).json():
                #ctypes.windll.user32.MessageBoxW(0, str(ft), "Your title", 1)
                res = requests.get(link).json()["routes"][0]["geometry"]
                routingInfo.append(res)
                # insert routes in db
                cur.execute(("update {0} set {1} = '{2}' where {3} = (select {4} from {5} where round({6}::numeric,4) = {7} and round({8}::numeric,4) = {9})").format(
                    intervention_table["intervention_table_name"],
                    intervention_table["intervention_route"],
                    str(res).replace("['", "").replace("']", ""),
                    intervention_table["intervention_id_fire_engine"],
                    fire_engine_table["fire_engine_id"],
                    fire_engine_table["fire_engine_table_name"],
                    fire_engine_table["fire_engine_x_pos"],
                    str(round(ft[0][0], 4)),
                    fire_engine_table["fire_engine_x_pos"],
                    str(round(ft[0][1], 4))))
                conn.commit()
            else:
                cur.execute("select {0} from {1} where {2} in (select {3} from {4} where round({5}::numeric,4) = {6} and round({7}::numeric,4) = {8})".format(
                    intervention_table["intervention_route"],
                    intervention_table["intervention_table_name"],
                    intervention_table["intervention_id_fire_engine"],
                    fire_engine_table["fire_engine_id"],
                    fire_engine_table["fire_engine_table_name"],
                    fire_engine_table["fire_engine_x_pos"],
                    str(round(ft[0][0], 4)),
                    fire_engine_table["fire_engine_y_pos"],
                    str(round(ft[0][1], 4))))
                routingInfo.append(str(cur.fetchone()[0]))

        logging.warning("fire_engines_pos : " + str(fire_engines_pos))
        logging.warning("routingInfo : " + str(routingInfo))
        logging.warning("firesToDisp : " + str(firesToDisp))
        return render_template('index.html', fire_engines=fire_engines_pos, routingInfo=routingInfo, fires=firesToDisp)
    except Exception as e:
        return render_template('index.html')
        ctypes.windll.user32.MessageBoxW(0, str(e), "Your title", 1)