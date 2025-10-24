import logging
import requests
import json
from datetime import datetime
from time import sleep
import sqlite3

# from flask_script import Server
from bson.objectid import ObjectId

from db import get_db
from config import app_config

# from schemas.cashiers import schema as cashier_schema

def sync_templates():
    logging.info('START SYNC TEMPLATES')

    templates = Templates()
    templates.get()

    # while True:
    #     templates.get()

    #     sleep(120)
    
class Templates():
    def get(self):
        server = app_config['API']['URL']
        token = app_config['API']['TOKEN']

        if(token):
            url = '{}/templates/list'.format( server )

            headers = {
                'Authorization' : f"Bearer {token}"
            }

            response = None
            try:
                response = requests.get(url, headers=headers)
            except requests.exceptions.RequestException as err:
                logging.exception(err)

            if(response and response.status_code == requests.codes.ok):
                logging.info( 'Response: ' + response.text)

                templates = json.loads(response.text)

                db = get_db()
                sql = 'replace into templates (name, text, url) values (?, ?, ?)'

                for template in templates:
                    try:
                        db.execute(sql, [ template['name'], template['text'], template['url'] ])
                        db.commit()
                    except sqlite3.OperationalError as e:
                        logging.error('Sqlite: ' + str(e))

                return True
                
        return False