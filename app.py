from flask import Flask
from flask_httpauth import HTTPBasicAuth
from bson.json_util import dumps, loads

########################################################################
#                                                                      #
#                                  INIT                                #
#                                                                      #
########################################################################

app = Flask(__name__)
auth = HTTPBasicAuth()

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
#                           FIRST REQUEST SYNC                         #
#                                                                      #
########################################################################

@app.before_first_request
def first_start():
    pass

########################################################################
#                                                                      #
#                             ERROR HANDKER                            #
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
    return MakeJson({"ok" : "Hola Mundo"})

########################################################################
#                                                                      #
#                                 START                                #
#                                                                      #
########################################################################

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=True)