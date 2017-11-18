import configparser
import logging
import os.path
from datetime import datetime

#buscamos el archivo de configuracion
#si existe lo leemos
#copiamos los datos en las variables
#si no existe creamos el fichero y escribimos las variables por defecto

class Config:
    def __init__(self):
        self.data = configparser.ConfigParser()

        if not(os.path.isfile('config.ini')):
            self.new_config()

        self.data.read('config.ini')

    def read(self, section, key, type=str, value=""):
        if(self.data.has_section(section)):
            if(type == bool):
                data = self.data[section].getboolean(key)
            elif(type == int):
                data = self.data[section].getint(key)
            elif(type == float):
                data = self.data[section].getfloat(key)
            else:
                data = self.data[section].get(key)
        else:
            data = False
        return data

    def write(self, section, key, value=""):
        if not(self.data.has_section(section)):
            self.data[section] = {}
        #if(self.data.has_option(section, key)):
        self.data[section][key] = str(value)

        logging.info(section + key + value)

        self.write_file()

    def new_config(self):
        self.data["SERVER"] = {}
        self.data["SERVER"]["IP"] = "localhost"
        self.data["SERVER"]["PORT"] = "5000"
        self.data["SERVER"]["TIMEOUT"] = "30"
        self.data["LOCAL"] = {}
        self.data["LOCAL"]["SERVER"] = "False"
        self.data["LOCAL"]["SYNC_DATE"] = "2010-01-01 00:00:01.000001"
        self.data["DATA_BASE"] = {}
        self.data["DATA_BASE"]["IP"] = "localhost"
        self.data["DATA_BASE"]["PORT"] = "27017"
        self.data["DATA_BASE"]["NAME"] = "TPV"
        self.write_file()

    def write_file(self):
        with open('config.ini', 'w') as configfile:
            self.data.write(configfile)

    def get_config(self):
        date = self.data["LOCAL"]["SYNC_DATE"]
        date_object = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
        self.data["LOCAL"]["SYNC_DATE"] = str(date_object)
        return self.data

    def set_config(self, data):
        try:
            self.data.read_dict(data)
            self.write_file()
            return {"ok" : "Configuracion guardada"}
        except:
            return {"error" : "Sucedio un error al guardar el diccionario"}