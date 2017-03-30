from flask import Flask, Response
from xmltodict import unparse
from datetime import datetime
from collections import OrderedDict
app = Flask(__name__)

@app.route('/voice.xml')
def basic_twiml():
    now = datetime.now()
    twiml = OrderedDict([
        ('Response', OrderedDict([
            ('Pause', {
                '@length': '2'
                }),
            ('Say', {
                '#text': 'Hello there! It is now {0:%H} {0:%M} {0:%p}.'.format(now),
                '@voice': 'woman'
                })
            ]))
        ])

    xml = unparse(twiml)
    resp = Response(response=xml, status=200, mimetype='text/xml')
    return resp
