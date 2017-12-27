from flask import Flask, render_template, g, request, session, flash, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from bson.json_util import dumps, loads
import sqlite3
from jinja2 import Template
import json
import os
import configparser
from zebra import zebra

from parser import TagParser

########################################################################
#                                                                      #
#                                  INIT                                #
#                                                                      #
########################################################################
app = Flask(__name__)
auth = HTTPBasicAuth()

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect( os.path.join( os.environ['SNAP_COMMON'], config['SERVER']['DATABASE'] ))
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
    with app.open_resource( config['SERVER']['SCHEMA'], mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

def MakeBson(json_raw):
    text = json.dumps(json_raw)
    bson = loads(text)
    return bson

def MakeJson(cursor):
    text = dumps(cursor)
    bytes = text.encode()
    return bytes

########################################################################
#                                                                      #
#                             FIRST REQUEST                            #
#                                                                      #
########################################################################

@app.before_first_request
def first_start():
    #if not (os.path.isfile( app.config['DATABASE'] )):
    init_db()
    pass

########################################################################
#                                                                      #
#                            ERROR HANDLER                             #
#                                                                      #
########################################################################

@app.errorhandler(400)
def pageBadRequest(error):
    return MakeJson({"error" : "400 Bad Request"})

@app.errorhandler(401)
def pageUnauthorizedAccess(error):
    return MakeJson({"error" : "401 Unauthorized Access"})

@app.errorhandler(404)
def pageNotFound(error):
    return MakeJson({"error" : "404 Not Found"})

@app.errorhandler(405)
def pageMethodNotAllowed(error):
    return MakeJson({"error" : "405 Method Not Allowed"})

@app.errorhandler(500)
def pageInternalServerError(error):
    return MakeJson({"error" : "500 Internal Server Error"})

########################################################################
#                                                                      #
#                                 HOME                                 #
#                                                                      #
########################################################################

@app.route('/')
def main():
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
#                                 ONFIG                                #
#                                                                      #
########################################################################

@app.route('/config')
def config():
    return render_template('config.html', config=config)

@app.route('/config/save', methods=['POST'])
def save_config():
    if not session.get('logged_in'):
        abort(401)

    config['SERVER']['DATABASE'] = request.form['server_database']
    config['SERVER']['SCHEMA'] = request.form['server_schema']
    config['SERVER']['SECRET_KEY'] = request.form['server_secret_key']
    config['SERVER']['DEBUG'] = request.form['server_debug']

    config['APP']['SECURITY'] = request.form['app_security']
    config['APP']['USERNAME'] = request.form['app_username']
    config['APP']['PASSWORD'] = request.form['app_password']

    config['SYNC']['SERVER'] = request.form['sync_server']
    config['SYNC']['PORT'] = request.form['sync_port']
    config['SYNC']['DELAY'] = request.form['sync_delay']
    config['SYNC']['USERNAME'] = request.form['sync_username']
    config['SYNC']['PASSWORD'] = request.form['sync_password']
    config['SYNC']['TOKEN'] = request.form['sync_token']

    with open( os.path.join( os.environ['SNAP_COMMON'], 'print-server.ini' ) , 'w') as configfile:
        config.write(configfile)

    flash('Configuration was successfully saved')
    return redirect(url_for('config'))

########################################################################
#                                                                      #
#                                 LOGIN                                #
#                                                                      #
########################################################################

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != config['APP']['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != config['APP']['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('main'))
    return render_template('login.html', error=error)

@app.route('/admin/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('main'))

########################################################################
#                                                                      #
#                                 PRINT                                #
#                                                                      #
########################################################################

@app.route('/print/<template_url>', methods=['POST'])
def print(template_url):
    data = MakeBson(request.json)
    printer_name = request.form['printer']
    copies = request.form['copies']

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
                parser = TagParser()
                text = template.render(data)

                if(ticket_printer_object):
                    print( parser.feed(text) )

                if(label_printer_object):
                    printer = zebra(label_printer_object['queue'])
                    printer.setup(direct_thermal=label_printer_object['direct_thermal'], label_height=(label_printer_object['height'], label_printer_object['gap']), label_width=label_printer_object['width'])
                    printer.output(text)

                return MakeJson({"error": "Successfully printed"})
            else:
                return MakeJson({"error": "The template "+str(template_url)+" does not exist"})
        else:
            return MakeJson({"error": "None data was recibed"})
    else:
        return MakeJson({"error": "The printer was not indicated"})

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
    config = configparser.ConfigParser()
    config.read( os.path.join( os.environ['SNAP_COMMON'], 'app_config.ini' ) )
    app.secret_key = config['SERVER']['SECRET_KEY']
    app.run(host='0.0.0.0', debug=config['SERVER']['DEBUG'] )