#SYSTEM
import os
from os.path import exists

#GLOBALS
from flask import Flask, render_template, g, request, session, flash, redirect, url_for, abort, jsonify
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
from bson.json_util import dumps, loads
import sqlite3

import jinja2
from jinja2 import Template

import json
import configparser
from zebra import Zebra
import requests
import logging
import threading
import time
from escpos.printer import File
from pathlib import Path
from datetime import datetime, date, timedelta

#LOCALS
from parser import TagParser
from config import app_config, save_config_file

#Import FILTERS
from filters import str_filter
from filters import url_pagination
from filters import date_filter
from filters import datetime_filter
from filters import currency_filter
from filters import integer_filter
from filters import numeric_filter
from filters import percent_filter
from filters import time_filter
from filters import to_object_id_filter
from filters import calendar_filter
from filters import humanize_date
from filters import human_datetime_filter

########################################################################
#                                                                      #
#                               VARIABLES                              #
#                                                                      #
########################################################################
if(os.environ.get('SNAP_COMMON')):
    DIRECTORY = os.environ['SNAP_COMMON']
else:
    DIRECTORY = str(Path.home())

########################################################################
#                                                                      #
#                                  INIT                                #
#                                                                      #
########################################################################
app = Flask(__name__)
cors = CORS(app)
auth = HTTPBasicAuth()
app.secret_key = app_config['SERVER']['SECRET_KEY']

TEMPLATE_TEXT = 'Test'

logging.basicConfig(level=logging.DEBUG)

########################################################################
#                                                                      #
#                              PROCESSORS                              #
#                                                                      #
########################################################################

jinja2.filters.FILTERS['oid'] = to_object_id_filter
jinja2.filters.FILTERS['str'] = str_filter
jinja2.filters.FILTERS['date'] = date_filter
jinja2.filters.FILTERS['time'] = time_filter
jinja2.filters.FILTERS['datetime'] = datetime_filter
jinja2.filters.FILTERS['currency'] = currency_filter
jinja2.filters.FILTERS['numeric'] = numeric_filter
jinja2.filters.FILTERS['percent'] = percent_filter
jinja2.filters.FILTERS['integer'] = integer_filter
jinja2.filters.FILTERS['calendar'] = calendar_filter
jinja2.filters.FILTERS['humanize'] = humanize_date
jinja2.filters.FILTERS['human_datetime'] = human_datetime_filter

########################################################################
#                                                                      #
#                                   DB                                 #
#                                                                      #
########################################################################

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect( os.path.join( DIRECTORY, app_config['SERVER']['DATABASE'] ))
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource( app_config['SERVER']['SCHEMA'], mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    app.logger.info('Initialized the database.')

########################################################################
#                                                                      #
#                                FUNCTIONS                             #
#                                                                      #
########################################################################

def MakeBson(json_raw):
    text = json.dumps(json_raw)
    bson = loads(text)
    return bson

def MakeJson(cursor):
    text = dumps(cursor)
    bytes = text.encode()
    return bytes

def get_token(server=None, port=None, url=None, username=None, password=None):
    response = None
    token = None

    server_url = 'http://' + server + ":" + port + "/" + url

    app.logger.info("Getting data from " + server_url )

    try:
        response = requests.get(server_url,
                        auth=requests.auth.HTTPBasicAuth(
                          username,
                          password))

    except:
        app.logger.exception("Conection error!")

    if(response):
        app.logger.info( 'Response:' + response.text)

        if (response.status_code == requests.codes.ok):
            token = response.text
            app.logger.info( 'Token:' + token)

    return token

########################################################################
#                                                                      #
#                             FIRST REQUEST                            #
#                                                                      #
########################################################################

from syncs import sync_templates

@app.before_first_request
def first_start():
    #if not (os.path.isfile( app.conf['DATABASE'] )):
    init_db()
    # start_sync()
    #start_sync()
    thread = threading.Thread(target=sync_templates)
    thread.start()

    pass

########################################################################
#                                                                      #
#                             ERROR HANDKER                            #
#                                                                      #
########################################################################

@app.errorhandler(400)
def pageBadRequest(error):
    return jsonify({"error" : "400 Bad Request"}), 400

@app.errorhandler(401)
def pageUnauthorizedAccess(error):
    return jsonify({"error" : "401 Unauthorized Access"}), 401

@app.errorhandler(403)
def pageForbidden(error):
    return jsonify({"error" : "403 Forbidden"}), 403

@app.errorhandler(404)
def pageNotFound(error):
    return jsonify({"error" : "404 Not Found"}), 404

@app.errorhandler(405)
def pageMethodNotAllowed(error):
    return jsonify({"error" : "405 Method Not Allowed"}), 405

@app.errorhandler(500)
def pageInternalServerError(error):
    return jsonify({"error" : "500 Internal Server Error"}), 500

########################################################################
#                                                                      #
#                                 HOME                                 #
#                                                                      #
########################################################################

@app.route('/')
def index():
    db = get_db()
    #GET TICKET PRINTERS
    cur = db.execute('select * from ticket_printers order by id desc')
    ticket_printers = cur.fetchall()

    #GET LABEL PRINTERS
    cur = db.execute('select * from label_printers order by id desc')
    label_printers = cur.fetchall()

    #GET TEMPLATES
    cur = db.execute('select * from templates order by id desc')
    templates = cur.fetchall()
    return render_template('index.html', ticket_printers=ticket_printers, label_printers=label_printers, templates=templates)

@app.route('/test')
def test():
    pass

########################################################################
#                                                                      #
#                                CONFIG                                #
#                                                                      #
########################################################################

@app.route('/config')
def show_config():
    return render_template('config.html', config=app_config)

@app.route('/config/save', methods=['POST'])
def save_config():
    if not session.get('logged_in'):
        abort(401)

    app_config['SERVER']['DATABASE'] = request.form['server_database']
    app_config['SERVER']['SCHEMA'] = request.form['server_schema']
    app_config['SERVER']['SECRET_KEY'] = request.form['server_secret_key']
    app_config['SERVER']['DEBUG'] = request.form['server_debug']

    app_config['APP']['SECURITY'] = request.form['app_security']
    app_config['APP']['USERNAME'] = request.form['app_username']
    app_config['APP']['PASSWORD'] = request.form['app_password']

    app_config['SYNC']['SERVER'] = request.form['sync_server']
    app_config['SYNC']['DELAY'] = request.form['sync_delay']
    app_config['SYNC']['TOKEN'] = request.form['sync_token']

    save_config_file()

    flash('Configuration was successfully saved')
    return redirect(url_for('show_config'))

########################################################################
#                                                                      #
#                                 LOGIN                                #
#                                                                      #
########################################################################

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app_config['APP']['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app_config['APP']['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route('/admin/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))

########################################################################
#                                                                      #
#                                 PRINT                                #
#                                                                      #
########################################################################

@app.route('/print/<printer_name>/<template_url>', methods=['POST'])
def print_data(template_url, printer_name):
    data = MakeBson(request.json)

    copies = 1
    if(request.args.get('copies')):
        copies = int(request.args['copies'])

    app.logger.info(data)
    app.logger.info(printer_name)
    app.logger.info(copies)

    if(printer_name):
        if(data):
            db = get_db()
            cur = db.execute('select * from templates where url=? order by id desc limit 1', [template_url])
            template_object = cur.fetchone()

            db = get_db()
            cur = db.execute('select * from ticket_printers where uri=? order by id desc limit 1', [printer_name])
            ticket_printer_object = cur.fetchone()

            db = get_db()
            cur = db.execute('select * from label_printers where uri=? order by id desc limit 1', [printer_name])
            label_printer_object = cur.fetchone()

            if(template_object):
                template = Template(template_object['text'])
                text = template.render(data, copies=copies) + '\n'
                app.logger.info('Rendered text: ' + text )

                if(ticket_printer_object):
                    app.logger.info(dict(ticket_printer_object))

                    if(exists(ticket_printer_object['route'])):
                        printer = File(ticket_printer_object['route'])
                        parser = TagParser()

                        for x in range(copies):
                            parser.parse(printer, text, ticket_printer_object['chars'])
                            app.logger.info('Print copy no. ' + str(x) )

                if(label_printer_object):
                    printer = Zebra(label_printer_object['queue'])
                    printer.setup(direct_thermal=label_printer_object['direct_thermal'])
                    printer.output(text)

                return MakeJson({"status": "Successfully printed"})
            else:
                return abort(404, "The template "+str(template_url)+" does not exist")
        else:
            return abort(400, "None data was recibed")
    else:
        return abort(404, "The printer was not indicated")

########################################################################
#                                                                      #
#                            TICKET PRINTERS                           #
#                                                                      #
########################################################################

@app.route('/printers/ticket/list', methods=['GET', 'POST'])
def list_ticket_printers():
    db = get_db()
    cur = db.execute('select * from ticket_printers order by id desc')
    results = cur.fetchall()
    printers = []
    for result in results:
        printer = {}
        printer["id"] = result["id"]
        printer["name"] = result["name"]
        printer["route"] = result["route"]
        printer["chars"] = int(result["chars"])
        printer["uri"] = result["uri"]

        printers.append(printer)
    return MakeJson(printers)

@app.route('/printers/ticket')
def show_ticket_printers():
    db = get_db()
    cur = db.execute('select * from ticket_printers order by id desc')
    printers = cur.fetchall()
    return render_template('show_ticket_printers.html', printers=printers)

@app.route('/printer/ticket/add', methods=['POST'])
def add_ticket_printer():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into ticket_printers (name, route, chars, uri) values (?, ?, ?, ?)',
                 [request.form['name'], request.form['route'], request.form['chars'], request.form['name'].replace(' ', '').lower() ])
    db.commit()
    flash('New printer was successfully added')
    return redirect(url_for('show_ticket_printers'))

@app.route('/printer/ticket/save', methods=['POST'])
def save_ticket_printer():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('update ticket_printers set route=?, chars=? where id=?',
                [ request.form['route'], request.form['chars'], request.form['id'] ])
    db.commit()
    flash('Template was successfully saved')
    return redirect(url_for('show_ticket_printers'))

@app.route('/printer/ticket/delete', methods=['POST'])
def delete_ticket_printer():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('delete from ticket_printers where id=?',
                 [request.form['id']])
    db.commit()
    flash('Printer was successfully deleted')
    return redirect(url_for('show_ticket_printers'))

@app.route('/printer/ticket/test', methods=['POST'])
def test_ticket_printer():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    cur = db.execute('select * from ticket_printers where id=?', [request.form['id']])
    ticket_printer_object = cur.fetchone()

    template = Template(TEMPLATE_TEXT)
    text = template.render({})
    
    if(ticket_printer_object):
        printer = File(ticket_printer_object['route'])
        parser = TagParser()
        parser.parse(printer, text)

    flash('The test was send printed')
    return redirect(url_for('show_ticket_printers'))

########################################################################
#                                                                      #
#                             LABEL PRINTERS                           #
#                                                                      #
########################################################################

@app.route('/printers/label/list', methods=['GET', 'POST'])
def list_label_printers():
    db = get_db()
    cur = db.execute('select * from label_printers order by id desc')
    results = cur.fetchall()
    printers = []
    for result in results:
        printer = {}
        printer["id"] = result["id"]
        printer["name"] = result["name"]
        printer["queue"] = result["queue"]
        printer["width"] = int(result["width"])
        printer["height"] = int(result["height"])
        printer["gap"] = int(result["gap"])
        if (result["direct_thermal"] == "true"):
            printer["direct_thermal"] = True
        else:
            printer["direct_thermal"] = False
        printer["uri"] = result["uri"]

        printers.append(printer)
    return MakeJson(printers)

@app.route('/printers/label')
def show_label_printers():
    db = get_db()
    cur = db.execute('select * from label_printers order by id desc')
    printers = cur.fetchall()
    return render_template('show_label_printers.html', printers=printers)

@app.route('/printer/label/add', methods=['POST'])
def add_label_printer():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()

    db.execute('insert into label_printers (name, queue, width, height, gap, direct_thermal, uri) values (?, ?, ?, ?, ?, ?, ?)',
        [ request.form['name'], request.form['queue'], request.form['width'], request.form['height'], request.form['gap'], request.form['direct_thermal'], request.form['name'].replace(' ', '').lower()] )
                 #[ request.form['name'], request.form['queue'], request.form['width'], request.form['height'], request.form['gap'], request.form['direct_thermal'] ] )
    db.commit()
    flash('New printer was successfully added')
    return redirect(url_for('show_label_printers'))

@app.route('/printer/label/save', methods=['POST'])
def save_label_printer():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('update label_printers set queue=?, width=?, height=?, gap=?, direct_thermal=? where id=?',
                [ request.form['queue'], request.form['width'], request.form['height'], request.form['gap'], request.form['direct_thermal'], request.form['id'] ])
    db.commit()
    flash('Template was successfully saved')
    return redirect(url_for('show_label_printers'))

@app.route('/printer/label/delete', methods=['POST'])
def delete_label_printer():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('delete from label_printers where id=?',
                 [request.form['id']])
    db.commit()
    flash('Printer was successfully deleted')
    return redirect(url_for('show_label_printers'))

########################################################################
#                                                                      #
#                              TEMPLATES                               #
#                                                                      #
########################################################################

@app.route('/templates')
def show_templates():
    db = get_db()
    cur = db.execute('select id, name, url, text from templates order by id desc')
    templates = cur.fetchall()
    return render_template('show_templates.html', templates=templates)

@app.route('/template/add', methods=['POST'])
def add_template():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into templates (name, url, text) values (?, ?, ?)',
                 [request.form['name'], request.form['url'], request.form['text']])
    db.commit()
    flash('New template was successfully added')
    return redirect(url_for('show_templates'))

@app.route('/template/save', methods=['POST'])
def save_template():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('update templates set url=?, text=? where id=?',
                [ request.form['url'], request.form['text'], request.form['id'] ])
    db.commit()
    flash('Template was successfully saved')
    return redirect(url_for('show_templates'))

@app.route('/template/delete', methods=['POST'])
def delete_template():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('delete from templates where id=?',
                 [request.form['id']])
    db.commit()
    flash('Template was successfully deleted')
    return redirect(url_for('show_templates'))

########################################################################
#                                                                      #
#                                 START                                #
#                                                                      #
########################################################################

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=app_config['SERVER']['DEBUG'] )
