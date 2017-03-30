from flask import Flask, request, Response
from datetime import datetime
from twilio import twiml
from urllib import urlretrieve
import os
app = Flask(__name__, static_url_path='/static')
site_url = 'http://vpn.rkfl.us/'

@app.route('/voice.xml', methods=['GET', 'POST'])
def basic_twiml():
    resp = twiml.Response()
    if request.values.get('CallSid') == None:
        return Response(response=str(resp), status=200, mimetype='text/xml')
    if request.values.get('CallStatus') == 'ringing':
        resp.pause(length=2)
        resp.say('Welcome to the message center.', voice='man')
    resp.pause(length=1)
    with resp.gather(numDigits=1, action='/menu.xml') as gather:
        gather.say('To listen to the last recorded message, press 1. To leave a message, press 2.', voice='woman')
    resp.hangup()
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/menu.xml', methods=['GET', 'POST'])
def menu_options():
    resp = twiml.Response()
    digit = request.values.get('Digits')
    if digit == '1':
        resp.say('You will now hear the last recorded message.', voice='man')
        resp.pause(length=1)
        with resp.gather(action='/voice.xml', finishOnKey='*') as gather:
            gather.play(site_url + 'static/lastmessage.wav')
        resp.redirect('/voice.xml')
    elif digit == '2':
        resp.say('Okay. Please leave your message after the tone.', voice='man')
        resp.record(action='/record.xml', finishOnKey='*', recordingStatusCallback='/record-callback.xml')
        resp.hangup()
    else:
        resp.say('I\'m sorry, that wasn\'t a valid choice.', voice='woman')
        resp.pause(length=1)
        resp.redirect('/voice.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/record.xml', methods=['GET', 'POST'])
def record_redirect():
    resp = twiml.Response()
    resp.say('Thanks for leaving your message.', voice='man')
    resp.redirect('/voice.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/record-callback.xml', methods=['GET', 'POST'])
def record_finished():
    resp = twiml.Response()
    if os.path.isfile('static/lastmessage.wav'):
        os.remove('static/lastmessage.wav')
    urlretrieve(request.values.get('RecordingUrl'), 'static/lastmessage.wav')
    return Response(response=str(resp), status=200, mimetype='text/xml')
