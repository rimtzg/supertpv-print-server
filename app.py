from flask import Flask, render_template, g, request, session, flash, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from bson.json_util import dumps, loads
import sqlite3
from jinja2 import Template
import json
import os

from parser import TagParser

########################################################################
#                                                                      #
#                                  INIT                                #
#                                                                      #
########################################################################
app = Flask(__name__)

app.config.from_pyfile('server.cfg', silent=True)
auth = HTTPBasicAuth()

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
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
    with app.open_resource('schemas.sql', mode='r') as f:
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
    #init_db()
    return render_template('index.html')

@app.route('/test')
def test():
    pass

########################################################################
#                                                                      #
#                                 LOGIN                                #
#                                                                      #
########################################################################

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
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
    if(data):
        db = get_db()
        cur = db.execute('select * from templates where url=? order by id desc limit 1', [template_url])
        result = cur.fetchone()

        if(result):
            template = Template(result["text"])
            parser = TagParser()
            text = template.render(data)
            print( parser.feed(text) )
            return text
        else:
            return MakeJson({"error": "The template "+str(template_url)+" does not exist"})
    else:
        return MakeJson({"error": "None data was recibed"})

########################################################################
#                                                                      #
#                               PRINTERS                               #
#                                                                      #
########################################################################

@app.route('/printers')
def show_printers():
    db = get_db()
    cur = db.execute('select id, name, route, chars from printers order by id desc')
    printers = cur.fetchall()
    return render_template('show_printers.html', printers=printers)

@app.route('/printer/add', methods=['POST'])
def add_printer():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into printers (name, route, chars) values (?, ?, ?)',
                 [request.form['name'], request.form['route'], request.form['chars']])
    db.commit()
    flash('New printer was successfully added')
    return redirect(url_for('show_printers'))

@app.route('/printer/save', methods=['POST'])
def save_printer():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('update printers set route=?, chars=? where id=?',
                [ request.form['route'], request.form['chars'], request.form['id'] ])
    db.commit()
    flash('Template was successfully saved')
    return redirect(url_for('show_printers'))

@app.route('/printer/delete', methods=['POST'])
def delete_printer():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('delete from printers where id=?',
                 [request.form['id']])
    db.commit()
    flash('Printer was successfully deleted')
    return redirect(url_for('show_printers'))

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
    app.run(host='0.0.0.0', debug=False)