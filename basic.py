from flask import Flask, request, Response
from datetime import datetime
from twilio import twiml
app = Flask(__name__)

@app.route('/voice.xml', methods=['GET', 'POST'])
def basic_twiml():
    now = datetime.now()
    resp = twiml.Response()
    if request.values.get('CallSid') == None:
        return Response(response=str(resp), status=200, mimetype='text/xml')

    resp.pause(length=2)
    resp.say('Thank you for calling this beautiful telephone number. Your phone number is {}'.format(request.values.get('From')), voice='man')
    resp.pause(length=5)
    resp.say(request.values.get('CallSid'), voice='woman')
    return Response(response=str(resp), status=200, mimetype='text/xml')
