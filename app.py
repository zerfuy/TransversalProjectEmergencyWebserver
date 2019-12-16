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


app = Flask(__name__)
app.secret_key = 'dev key'

app.config['MYSQL_HOST'] = 'manny.db.elephantsql.com'
app.config['MYSQL_USER'] = 'juynhvrm'
app.config['MYSQL_PASSWORD'] = 'H-FZ4Jrenwgd_c2Xzte7HLsYJzB_6q5D'
app.config['MYSQL_DB'] = 'juynhvrm'
mysql = MySQL(app)

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


@app.route('/')

def index():
    conn = psycopg2.connect(host="manny.db.elephantsql.com", database="juynhvrm", user="juynhvrm", password="H-FZ4Jrenwgd_c2Xzte7HLsYJzB_6q5D")

    cur = conn.cursor()
    cur.execute('SELECT version()')
    db_version = cur.fetchone()

    fire_engines = [[45.784680, 4.893310], [45.783380, 4.813370], [45.782680, 4.897370], [45.780680, 4.893570]]
    fromTo = [[[45.783680, 4.893370], [45.779121, 4.873990]],
        [[45.767311, 4.834310], [43.603951, 1.444510]]]


    return render_template('index.html', fire_engines=fire_engines, fromTo=fromTo)
