from flask import Flask, Response
from dicttoxml import dicttoxml
from datetime import datetime
app = Flask(__name__)

@app.route('/voice.xml')
def basic_twiml():
    now = datetime.now()
    twiml = {u'Say': "Hello there! It is now the minute {0:%M} of the hour {0:%H}.".format(now)}
    xml = dicttoxml(twiml, attr_type=False, custom_root='Response')
    resp = Response(response=xml, status=200, mimetype='text/xml')
    return resp
