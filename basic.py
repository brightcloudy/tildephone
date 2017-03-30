from flask import Flask, request, Response
from datetime import datetime
from twilio import twiml
from urllib import urlretrieve
app = Flask(__name__, static_url_path='/static')
site_url = 'http://vpn.rkfl.us/'

@app.route('/voice.xml', methods=['GET', 'POST'])
def basic_twiml():
    resp = twiml.Response()
    if request.values.get('CallSid') == None:
        return Response(response=str(resp), status=200, mimetype='text/xml')

    resp.pause(length=2)
    resp.say('Thank you for calling this number. Your phone number is {}'.format(' '.join(list(request.values.get('From'))[1:])), voice='man')
    resp.pause(length=1)
    with resp.gather(numDigits=1, action='/menu.xml') as gather:
        gather.say('To listen to a song, press 1. To leave a message, press 2.')
    resp.hangup()
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/menu.xml', methods=['GET', 'POST'])
def menu_options():
    resp = twiml.Response()
    digit = request.values.get('Digits')
    if digit == '1':
        resp.say('You will now hear a song for your enjoyment.', voice='woman')
        resp.pause(length=2)
        resp.play(site_url + 'static/tapemachine.mp3')
        resp.hangup()
    elif digit == '2':
        resp.say('Okay. Please leave your message after the tone.', voice='man')
        resp.record(action='/record.xml', finishOnKey='*', recordingStatusCallback='/record-callback.xml')
        resp.hangup()
    else:
        resp.say('You fucked up and picked a bad option. Die.')
        resp.hangup()
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/record.xml', methods=['GET', 'POST'])
def record_redirect():
    resp = twiml.Response()
    resp.hangup()
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/record-callback.xml', methods=['GET', 'POST'])
def record_finished():
    resp = twiml.Response()
    urlretrieve(request.values.get('RecordingUrl'), request.values.get('RecordingSid'))
    return Response(response=str(resp), status=200, mimetype='text/xml')
