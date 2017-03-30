from flask import Flask, request, Response
from datetime import datetime
from twilio import twiml
from urllib import urlretrieve
import random
import os
import sqlite3
app = Flask(__name__, static_url_path='/static')
site_url = 'http://vpn.rkfl.us/'
conn = sqlite3.connect('mboard.db')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users(userid INTEGER PRIMARY KEY, name_recording TEXT, permissions INTEGER NOT NULL, login_pin TEXT, lastseen INTEGER NOT NULL);')
cur.execute('CREATE TABLE IF NOT EXISTS messages(messageid INTEGER PRIMARY KEY, userid INTEGER REFERENCES users(userid) ON DELETE CASCADE, message_recording TEXT NOT NULL, created_datetime INTEGER NOT NULL, message_length INTEGER NOT NULL);')
cur.execute('CREATE TABLE IF NOT EXISTS viewed_messages(messageid INTEGER REFERENCES messages(messageid) ON DELETE CASCADE, userid INTEGER REFERENCES users(userid) ON DELETE CASCADE);')
cur.execute('CREATE TABLE IF NOT EXISTS numbers(userid INTEGER REFERENCES users(userid) ON DELETE CASCADE, number TEXT UNIQUE NOT NULL);')
conn.commit()

call_dict = {}

@app.route('/voice.xml', methods=['GET', 'POST'])
def basic_twiml():
    resp = twiml.Response()
    if request.values.get('CallSid') == None:
        return Response(response=str(resp), status=200, mimetype='text/xml')
    if request.values.get('CallStatus') == 'ringing':
        resp.pause(length=2)
        resp.say('Welcome to the tilde town message board.', voice='man')
    cur = conn.cursor()
    cur.execute('SELECT userid FROM numbers WHERE number=?', (request.values.get('From')[2:],))
    user_from_number = cur.fetchone()
    if user_from_number == None:
        resp.say('You are currently a guest user.', voice='man')
    else:
        user_from_number = user_from_number[0]
        cur.execute('UPDATE users SET lastseen=? WHERE userid=?', (int((datetime.utcnow()-datetime(1970,1,1)).total_seconds()), user_from_number))
        conn.commit()
        cur.execute('SELECT name_recording FROM users WHERE userid=?', (user_from_number,))
        resp.say('Welcome back', voice='man')
        resp.play(site_url + 'static/' + cur.fetchone()[0])
    resp.pause(length=1)
    if user_from_number != None:
        resp.redirect('/prompt-user.xml')
    else:
        resp.redirect('/prompt-guest.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/prompt-user.xml', methods=['GET', 'POST'])
def user_prompt():
    resp = twiml.Response()
    with resp.gather(numDigits=1, action='/menu-user.xml') as gather:
        gather.say('You\'re basically fucked because I haven\'t implemented this part yet.', voice='woman')
        gather.say('To listen to the most recent message, press 1. To leave a message of your own, press 2.', voice='woman')
    resp.pause(length=2)
    resp.redirect('/prompt-user.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/prompt-guest.xml', methods=['GET', 'POST'])
def guest_prompt():
    resp = twiml.Response()
    with resp.gather(numDigits=1, action='/menu-guest.xml') as gather:
        gather.say('To listen to the most recent message, press 1. To log in as a user, press 2. To register as a new user, press 3.', voice='woman')
    resp.pause(length=2)
    resp.redirect('/prompt-guest.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/menu-user.xml', methods=['GET', 'POST'])
def user_menu():
    resp = twiml.Response()
    digit = request.values.get('Digits')
    cur.execute('SELECT userid FROM numbers WHERE number=?', (request.values.get('From')[2:],))
    user_from_number = cur.fetchone()[0]
    if digit == '1':
        cur.execute('SELECT userid, message_recording, created_datetime FROM messages LIMIT 10 ORDER BY created_datetime DESC')
        lastmessage = cur.fetchone()
        if lastmessage == None:
            resp.say('There are no messages in the system!', voice='man')
            resp.redirect('/prompt-user.xml')
        else:
            created_time = datetime.fromtimestamp(int(lastmessage[2]))
            cur.execute('SELECT name_recording FROM users WHERE userid=?', (lastmessage[0],))
            user_greet = cur.fetchone()[0]
            resp.say('This is the most recent message, recorded at {0:%I} {0:%M} {0:%p} on {0:%A}, {0:%B} {0:%d}.'.format(created_time), voice='man')
            resp.say('It was recorded by', voice='man')
            resp.play(site_url + 'static/' + user_greet)
            resp.pause(length=1)
            resp.play(site_url + 'static/' + lastmessage[1])
            resp.redirect('/prompt-user.xml')
    elif digit == '2':
        resp.redirect('/record-message.xml')
    else:
        resp.say('That is not a valid option.', voice='feman')
        resp.redirect('/prompt-user.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/menu-guest.xml', methods=['GET', 'POST'])
def guest_menu():
    resp = twiml.Response()
    digit = request.values.get('Digits')
    if digit == '1':
        resp.say('You will now hear the last recorded message.', voice='man')
        resp.pause(length=1)
        with resp.gather(action='/prompt-guest.xml', finishOnKey='*') as gather:
            gather.play(site_url + 'static/lastmessage.wav')
        resp.redirect('/prompt-guest.xml')
    elif digit == '2':
        resp.say('Okay. To log in, we need to know the PIN you were given when you registered.', voice='man')
        resp.pause(length=1)
        resp.redirect('/user-login.xml')
    elif digit == '3':
        resp.say('Alright. We\'ll register your phone number, and you\'ll record your name.', voice='man')
        resp.pause(length=1)
        resp.redirect('/create-user.xml')
    else:
        resp.say('I\'m sorry, that wasn\'t a valid choice.', voice='woman')
        resp.pause(length=1)
        resp.redirect('/prompt-guest.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/create-user.xml', methods=['GET', 'POST'])
def create_user():
    resp = twiml.Response()
    resp.say('Now say your name, and press star when you\'re finished.', voice='man')
    resp.record(action='/record-name.xml', playBeep='false', finishOnKey='*', maxLength=3, recordingStatusCallback='/record-name-callback.xml')
    resp.say('I\'m sorry, I didn\'t hear that.', voice='man')
    resp.redirect('/create-user.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/record-name-callback.xml', methods=['GET', 'POST'])
def name_callback():
    resp = twiml.Response()
    urlretrieve(request.values.get('RecordingUrl'), 'static/' + request.values.get('RecordingUrl').split('/')[-1] + '.wav')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/record-name.xml', methods=['GET', 'POST'])
def name_recorded():
    resp = twiml.Response()
    digits = request.values.get('Digits')
    if digits == None or digits == '*':
        call_dict.update({request.values.get('CallSid'): request.values.get('RecordingUrl').split('/')[-1] + '.wav'})
        resp.say('Here\'s what I heard.', voice='man')
        resp.play(request.values.get('RecordingUrl') + '.wav')
        with resp.gather(numDigits=1, timeout=10) as gather:
            resp.say('If you want to keep that recording, do nothing. If you want to change it, press any key.', voice='man')
            resp.pause(length=5)
        cur = conn.cursor()
        cur.execute('INSERT INTO users (name_recording, permissions, lastseen) VALUES (?, 0, ?)', (request.values.get('RecordingUrl').split('/')[-1] + '.wav', int((datetime.utcnow()-datetime(1970,1,1)).total_seconds())))
        conn.commit()
        cur.execute('SELECT userid FROM users WHERE name_recording=?', (request.values.get('RecordingUrl').split('/')[-1] + '.wav',))
        newid = cur.fetchone()[0]
        cur.execute('INSERT INTO numbers (userid, number) VALUES (?, ?)', (newid, request.values.get('From')[2:]))
        conn.commit()
        resp.say('Fantastic. Thanks for registering!', voice='man')
        resp.redirect('/create-pin.xml')
    else:
        os.remove('static/' + call_dict[request.values.get('CallSid')])
        call_dict.pop(request.values.get('CallSid'))
        resp.redirect('/create-user.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/create-pin.xml', methods=['GET', 'POST'])
def create_pin():
    resp = twiml.Response()
    cur.execute('SELECT userid FROM numbers WHERE number=?', (request.values.get('From')[2:],))
    user_from_number = cur.fetchone()[0]
    resp.say('Now, we\'re going to give you a number you can use to log in from other phone numbers.', voice='man')
    pin = []
    for i in range(0,6):
        pin += str(random.randint(0,9))
    spokenpin = '. '.join(pin) + '.'
    resp.say('Here is the PIN we generated for you. Be sure to write it down.', voice='man')
    resp.pause(length=1)
    resp.say(spokenpin, voice='woman')
    resp.pause(length=1)
    resp.say('Once again, here is the PIN we generated for you.', voice='man')
    resp.pause(length=1)
    resp.say(spokenpin, voice='woman')
    cur.execute('UPDATE users SET login_pin=? WHERE userid=?', (''.join(pin), user_from_number))
    conn.commit()
    resp.pause(length=1)
    resp.say('You\'re all set up now. Welcome to tilde town!', voice='man')
    resp.redirect('/prompt-user.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/user-login.xml', methods=['GET', 'POST'])
def user_login():
    resp = twiml.Response()
    digits = request.values.get('Digits')
    if digits == None:
        with resp.gather(numDigits=6, timeout=10) as gather:
            gather.say('Please enter that six digit PIN now.', voice='man')
        resp.say('I didn\'t hear you enter a PIN.', voice='man')
        resp.redirect('/user-login.xml')
    else:
        cur.execute('SELECT userid FROM users WHERE login_pin=?', (digits,))
        userid = cur.firstone()
        if userid == None:
            resp.say('I\'m sorry, but I don\'t recognize that PIN.', voice='man')
            resp.redirect('/prompt-guest.xml')
        else:
            cur.execute('INSERT INTO numbers (userid, number) VALUES (?, ?)', (userid[0], request.values.get('From')[2:]))
            conn.commit()
            resp.redirect('/voice.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/record-message.xml', methods=['GET', 'POST'])
def record_message():
    resp = twiml.Response()
    resp.say('At the sound of the tone, start recording your message. Press any key to stop.', voice='man')
    resp.pause(length=1)
    resp.record(action='/add-message.xml', recordingStatusCallback='/add-message-callback.xml')
    resp.say('I\'m sorry, I didn\'t hear anything.', voice='man')
    resp.redirect('/record-message.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/add-message.xml', methods=['GET', 'POST'])
def add_message():
    resp = twiml.Response()
    cur.execute('SELECT userid FROM numbers WHERE number=?', (request.values.get('From')[2:],))
    user_from_number = cur.fetchone()[0]
    cur.execute('INSERT INTO messages (userid, message_recording, created_datetime, message_length) VALUES (?, ?, ?, ?)', (user_from_number, request.values.get('RecordingUrl').split('/')[-1] + '.wav', int((datetime.utcnow()-datetime(1970,1,1)).total_seconds()), request.values.get('RecordingDuration')))
    conn.commit()
    resp.say('Thank you for recording your message!', voice='man')
    resp.redirect('/prompt-user.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/add-message-callback.xml', methods=['GET', 'POST'])
def add_message_callback():
    resp = twiml.Response()
    urlretrieve(request.values.get('RecordingUrl'), 'static/' + request.values.get('RecordingUrl').split('/')[-1] + '.wav')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/record.xml', methods=['GET', 'POST'])
def record_redirect():
    resp = twiml.Response()
    resp.say('Thanks for leaving your message.', voice='man')
    resp.redirect('/prompt-guest.xml')
    return Response(response=str(resp), status=200, mimetype='text/xml')

@app.route('/record-callback.xml', methods=['GET', 'POST'])
def record_finished():
    resp = twiml.Response()
    if os.path.isfile('static/lastmessage.wav'):
        os.remove('static/lastmessage.wav')
    urlretrieve(request.values.get('RecordingUrl'), 'static/lastmessage.wav')
    return Response(response=str(resp), status=200, mimetype='text/xml')
