#!/usr/bin/python
import json

def rest_server(dummy, state):
    from utility import utility
    from bottle import route, run, get, post, request, static_file, abort
    from subprocess import call
    from datetime import datetime
    import config as conf
    import os

    # '/root/silvia-pi'#os.path.dirname(__file__)
    basedir = os.path.dirname(os.path.abspath(__file__))
    wwwdir = basedir+'/www/'

    @route('/')
    def docroot():
        return static_file('index.html', wwwdir)

    @route('/<filepath:path>')
    def servfile(filepath):
        return static_file(filepath, wwwdir)

    @route('/curtemp')
    def curtemp():
        return str(utility.c_to_f(state['avgtemp'])) if conf.use_fahrenheit else str(state['avgtemp'])

    @get('/settemp')
    def settemp():
        return str(utility.c_to_f(state['settemp'])) if conf.use_fahrenheit else str(state['settemp'])

    @post('/settemp')
    def post_settemp():
        try:
            settemp = str(utility.f_to_c(float(request.forms.get('settemp')))) if conf.use_fahrenheit else float(request.forms.get('settemp'))
            if settemp >= conf.low_temp_b and settemp <= conf.high_temp_b:
                state['settemp'] = settemp
                return str(settemp)
            else:
                abort(400, 'Temperature out of range.')
        except:
            abort(400,'Invalid value for set temp.')

    @post('/setsteamtemp')
    def post_setsteamtemp():
        try:
            tempInput = float(request.forms.get('steamtemp'))
            steamtemp = utility.f_to_c(tempInput) if conf.use_fahrenheit else tempInput
            if steamtemp >= conf.low_temp_s and steamtemp <= conf.high_temp_s:
                state['steamtemp'] = steamtemp
                return str(steamtemp)
            else:
                abort(400, 'Temperature out of range.')
        except:
            abort(400,'Invalid value for set temp.')

    @get('/pid')
    def getpid():
        pidValues = {
            "p": state['Kp'],
            "i": state['Ki'],
            "d": state['Kp']
        }
        return json.dumps(pidValues)

    @post('/pid')
    def setpid():
        try:
            pid = request.json
            
            state['Kp'] = float(pid["p"])
            state['Ki'] = float(pid["i"])
            state['Kd'] = float(pid["d"])
        except:
            abort(400, 'Invalid value for PID')

    @get('/snooze')
    def get_snooze():
        return str(state['snooze'])

    @post('/snooze')
    def post_snooze():
        snooze = request.forms.get('snooze')
        try:
            datetime.strptime(snooze, '%H:%M')
        except:
            abort(400,'Invalid time format.')
        state['snoozeon'] = True
        state['snooze'] = snooze
        return str(snooze)

    @post('/resetsnooze')
    def reset_snooze():
        state['snoozeon'] = False
        return True

    @get('/allstats')
    def allstats():
        return dict(state)

    @route('/restart')
    def restart():
        call(["reboot"])
        return ''

    @route('/shutdown')
    def shutdown():
        call(["shutdown", "-h", "now"])
        return ''

    @get('/healthcheck')
    def healthcheck():
        return 'OK'

    run(host=conf.host, port=conf.port)
