import configparser
import os
from pathlib import Path

FILE = 'app_config.ini'

if(os.environ.get('SNAP_COMMON')):
    DIRECTORY = os.environ['SNAP_COMMON']
else:
    DIRECTORY = str(Path.home())

app_config = configparser.ConfigParser()
app_config.read( os.path.join( DIRECTORY, FILE ) )

def save_config_file():
    with open( os.path.join( DIRECTORY, FILE ) , 'w') as configfile:
        app_config.write(configfile)