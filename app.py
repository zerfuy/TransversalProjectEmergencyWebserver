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
from flask_mysqldb import MySQL
import json
import psycopg2
import ctypes
import serial
import sys
import requests
import json


app = Flask(__name__)
app.secret_key = 'dev key'

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

mysql = MySQL(app)


# potential improvments : 
# async calls via multiple connections
# functions
@app.route('/')

def index():

    # read serial port to get fires
    if sys.platform.startswith('win'):
        SERIALPORT = "COM4"
    else:
        SERIALPORT = "/dev/ttyUSB0"

    a = ""

    # ser = serial.Serial(
    #     port=SERIALPORT,
    #     baudrate=115200
    # )

    try:
        pass
        # a = ser.readline()
        # ser.close()
    except serial.SerialException:
        print("Serial {} port not available".format(SERIALPORT))

    a = "59,1;58,1;57,0;56,0;55,0;54,0;53,0;52,0;51,0;50,0;49,0;48,1;47,0;46,0;45,0;44,0;43,0;42,0;41,0;40,0;39,0;38,0;37,0;36,0;35,0;34,0;33,0;32,0;31,0;30,0;29,0;28,0;27,0;26,0;25,0;24,0;23,0;22,0;21,0;20,0;19,0;18,0;17,0;16,0;15,0;14,0;13,0;12,0;11,0;10,0;9,0;8,0;7,0;6,0;5,0;4,0;3,0;2,0;1,0"

    tab = []
    finalfires = []
    tab = a.split(";")
    for fire in tab:
        finalfires.append(fire.split(","))

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
    intervention_table["intervention_id_fire_engine"] = "id_fire_engine"
    intervention_table["intervention_id_fire"] = "id_fire"
    intervention_table["intervention_table_name"] = "intervention"
    intervention_table["intervention_route"] = "route"

    fire_table = {}
    fire_table["fire_id"] = "id"
    fire_table["fire_id_real_pos"] = "id_real_pos"
    fire_table["fire_intensity"] = "intensity"
    fire_table["fire_table_name"] = "fire"

    real_pos_table = {}
    real_pos_table["real_pos_id"] = "id"
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

    # get fire_engines positions in fire_engines
    cur.execute("select {0}, {1}, {2}, {3} from {4}".format(
        fire_engine_table["fire_engine_id"],
        fire_engine_table["fire_engine_id_station"],
        fire_engine_table["fire_engine_x_pos"],
        fire_engine_table["fire_engine_y_pos"],
        fire_engine_table["fire_engine_table_name"])
    )
    fire_engines = []
    row = cur.fetchone()
    while row is not None:
        fire_engines.append(list(row[2:]))
        row = cur.fetchone()

    # get intervention relations
    cur.execute("select {0}, {1} from {2} where {3} in (select {4} from {5})".format(
        fire_engine_table["fire_engine_x_pos"],
        fire_engine_table["fire_engine_y_pos"],
        fire_engine_table["fire_engine_table_name"],
        fire_engine_table["fire_engine_id"],
        intervention_table["intervention_id_fire_engine"],
        intervention_table["intervention_table_name"])
    )
    fire_engines_pos = []
    row = cur.fetchone()
    while row is not None:
        fire_engines_pos.append(list(row))
        row = cur.fetchone()

    # get active fire positions
    cur.execute("select {0}, {1} from {2} where {3} in (select {4} from {5} where {6} in (select {7} from {8}))".format(
        real_pos_table["real_pos_real_x"],
        real_pos_table["real_pos_real_y"],
        real_pos_table["real_pos_name"],
        real_pos_table["real_pos_id"],
        fire_table["fire_id_real_pos"],
        fire_table["fire_table_name"],
        fire_table["fire_id"],
        intervention_table["intervention_id_fire"],
        intervention_table["intervention_table_name"]))
    fires = []
    row = cur.fetchone()
    while row is not None:
        fires.append(list(row))
        row = cur.fetchone()

    # Establish itineraries from fire_engines to active fires
    fromTo = []
    if len(fire_engines_pos) == len(fires):
        for i in range(0, len(fire_engines_pos)):
            fromTo.append([fire_engines_pos[i], fires[i]])

    # Parse fire_engines from 0 à x, donc on peut attribuer les chemins sans le meme ordre
    routingInfo = list()
    for ft in fromTo:
        link = "http://router.project-osrm.org/route/v1/driving/" + str(ft[0][1]) + "," + str(ft[0][0]) + ";" + str(ft[1][1]) + "," + str(ft[1][0]) + "?overview=full"
        if "routes" in requests.get(link).json().keys():
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
            cur.execute(("select {0} from {1} where {2} = (select {3} from {4} where round({5}::numeric,4) = {6} and round({7}::numeric,4) = {8})").format(
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

    cur.close()
    return render_template('index.html', fire_engines=fire_engines, routingInfo=routingInfo, fires=fires)