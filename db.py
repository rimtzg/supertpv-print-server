import os
import sqlite3
from flask import current_app as app, g
from pathlib import Path
from config import app_config

if(os.environ.get('SNAP_COMMON')):
    DIRECTORY = os.environ['SNAP_COMMON']
else:
    DIRECTORY = str(Path.home())

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect( os.path.join( DIRECTORY, app_config['SERVER']['DATABASE'] ))
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    db = connect_db()
    return db

def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource( app_config['SERVER']['SCHEMA'], mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()