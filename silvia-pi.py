#!/usr/bin/python

def he_control_loop(dummy, state):
    from time import sleep
    from datetime import datetime, timedelta
    import RPi.GPIO as GPIO
    import config as conf

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(conf.he_pin, GPIO.OUT)
    GPIO.output(conf.he_pin, 0)

    heating = False

    try:
        while True:
            # if state['snoozeon'] == True:
            #     now = datetime.now()
            #     dt = datetime.strptime(state['snooze'], '%H:%M')
            #     if dt.hour == now.hour and dt.minute == now.minute:
            #         state['snoozeon'] = False

            avgpid = state['avgpid']

            if not state['awake']:
                state['heating'] = False
                GPIO.output(conf.he_pin, 0)
                sleep(1)
            else:
                if avgpid >= 100:
                    state['heating'] = True
                    GPIO.output(conf.he_pin, 1)
                    sleep(1)
                elif avgpid > 0 and avgpid < 100:
                    state['heating'] = True
                    GPIO.output(conf.he_pin, 1)
                    sleep(avgpid/100.)
                    GPIO.output(conf.he_pin, 0)
                    sleep(1-(avgpid/100.))
                    state['heating'] = False
                else:
                    GPIO.output(conf.he_pin, 0)
                    state['heating'] = False
                    sleep(1)

    finally:
        GPIO.output(conf.he_pin, 0)
        GPIO.cleanup()


def pid_loop(dummy, state):
    import sys
    from time import sleep, time
    import datetime
    from math import isnan
    import Adafruit_GPIO.SPI as SPI
    import Adafruit_MAX31855.MAX31855 as MAX31855
    import PID as PID
    import config as conf

    def c_to_f(c):
        return c * 9.0 / 5.0 + 32.0

    sensor = MAX31855.MAX31855(spi=SPI.SpiDev(conf.spi_port, conf.spi_dev))

    pid = PID.PID(conf.Pc, conf.Ic, conf.Dc)
    pid.SetPoint = state['settemp']
    pid.setSampleTime(conf.sample_time*5)

    nanct = 0
    i = 0
    j = 0
    pidhist = [0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    avgpid = 0.
    temphist = [0., 0., 0., 0., 0.]
    avgtemp = 0.
    lastsettemp = state['settemp']
    lasttime = time()
    sleeptime = 0
    iscold = True
    iswarm = False
    lastcold = 0
    lastwarm = 0

    try:
        while True:  # Loops 10x/second
            tempc = sensor.readTempC()
            if isnan(tempc):
                nanct += 1
                if nanct > 100000:
                    sys.exit
                continue
            else:
                nanct = 0

            # tempf = c_to_f(tempc)
            temphist[i % 5] = tempc
            avgtemp = sum(temphist)/len(temphist)

            if avgtemp < 30:
                lastcold = i

            if avgtemp > 90:
                lastwarm = i

            if iscold and (i-lastcold)*conf.sample_time > 60*15:
                pid = PID.PID(conf.Pw, conf.Iw, conf.Dw)
                pid.SetPoint = state['settemp']
                pid.setSampleTime(conf.sample_time*5)
                iscold = False

            if iswarm and (i-lastwarm)*conf.sample_time > 60*15:
                pid = PID.PID(conf.Pc, conf.Ic, conf.Dc)
                pid.SetPoint = state['settemp']
                pid.setSampleTime(conf.sample_time*5)
                iscold = True

            if state['settemp'] != lastsettemp:
                pid.SetPoint = state['settemp']
                lastsettemp = state['settemp']

            if i % 10 == 0:
                pid.update(avgtemp)
                pidout = pid.output
                pidhist[i/10 % 10] = pidout
                avgpid = sum(pidhist)/len(pidhist)

            state['i'] = i
            state['tempc'] = round(tempc, 2)
            state['avgtemp'] = round(avgtemp, 2)
            state['pidval'] = round(pidout, 2)
            state['avgpid'] = round(avgpid, 2)
            state['pterm'] = round(pid.PTerm, 2)
            if iscold:
                state['iterm'] = round(pid.ITerm * conf.Ic, 2)
                state['dterm'] = round(pid.DTerm * conf.Dc, 2)
            else:
                state['iterm'] = round(pid.ITerm * conf.Iw, 2)
                state['dterm'] = round(pid.DTerm * conf.Dw, 2)
            state['iscold'] = iscold

            print (datetime.now())
            print(state)

            sleeptime = lasttime+conf.sample_time-time()
            if sleeptime < 0:
                sleeptime = 0
            sleep(sleeptime)
            i += 1
            lasttime = time()

    finally:
        pid.clear


def rest_server(dummy, state):
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
        return str(state['avgtemp'])

    @get('/settemp')
    def settemp():
        return str(state['settemp'])

    @post('/settemp')
    def post_settemp():
        try:
            settemp = float(request.forms.get('settemp'))
            if settemp >= conf.low_temp_b and settemp <= conf.high_temp_b:
                state['settemp'] = settemp
                return str(settemp)
            else:
                print("wrong temp 186")
                # abort(400,'Set temp out of range 200-260.')
        except:
            print("line189 wrong number set temp")
            # abort(400,'Invalid number for set temp.')

    # @post('/setMonday')

    @get('/snooze')
    def get_snooze():
        return str(state['snooze'])

    @post('/snooze')
    def post_snooze():
        snooze = request.forms.get('snooze')
        try:
            datetime.strptime(snooze, '%H:%M')
        except:
            print("line202,wrong time format")
            # abort(400,'Invalid time format.')
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

    @post('/TimerOnMo')
    def post_TimerOnMo():
        TimerOnMo = request.forms.get('TimerOnMo')
        try:
            datetime.strptime(TimerOnMo,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOnMo'] = TimerOnMo
        return str(TimerOnMo)

    @post('/TimerOnTu')
    def post_TimerOnTu():
        TimerOnTu = request.forms.get('TimerOnTu')
        try:
            datetime.strptime(TimerOnTu,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOnTu'] = TimerOnTu
        return str(TimerOnTu)

    @post('/TimerOnWe')
    def post_TimerOnWe():
        TimerOnWe = request.forms.get('TimerOnWe')
        try:
            datetime.strptime(TimerOnWe,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOnWe'] = TimerOnWe
        return str(TimerOnWe)

    @post('/TimerOnTh')
    def post_TimerOnTh():
        TimerOnTh = request.forms.get('TimerOnTh')
        try:
            datetime.strptime(TimerOnTh,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOnTh'] = TimerOnTh
        return str(TimerOnTh)

    @post('/TimerOnFr')
    def post_TimerOnFr():
        TimerOnFr = request.forms.get('TimerOnFr')
        try:
            datetime.strptime(TimerOnFr,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOnFr'] = TimerOnFr
        return str(TimerOnFr)

    @post('/TimerOnSa')
    def post_TimerOnSa():
        TimerOnSa = request.forms.get('TimerOnSa')
        try:
            datetime.strptime(TimerOnSa,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOnSa'] = TimerOnSa
        return str(TimerOnSa)

    @post('/TimerOnSu')
    def post_TimerOnSu():
        TimerOnSu = request.forms.get('TimerOnSu')
        try:
            datetime.strptime(TimerOnSu,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOnSu'] = TimerOnSu
        return str(TimerOnSu)

    @post('/TimerOffMo')
    def post_TimerOffMo():
        TimerOffMo = request.forms.get('TimerOffMo')
        try:
            datetime.strptime(TimerOffMo,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOffMo'] = TimerOffMo
        return str(TimerOffMo)

    @post('/TimerOffTu')
    def post_TimerOffTu():
        TimerOffTu = request.forms.get('TimerOffTu')
        try:
            datetime.strptime(TimerOffTu,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOffTu'] = TimerOffTu
        return str(TimerOffTu)

    @post('/TimerOffWe')
    def post_TimerOffWe():
        TimerOffWe = request.forms.get('TimerOffWe')
        try:
            datetime.strptime(TimerOffWe,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOffWe'] = TimerOffWe
        return str(TimerOffWe)

    @post('/TimerOffTh')
    def post_TimerOffTh():
        TimerOffTh = request.forms.get('TimerOffTh')
        try:
            datetime.strptime(TimerOffTh,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOffTh'] = TimerOffTh
        return str(TimerOffTh)

    @post('/TimerOffFr')
    def post_TimerOffFr():
        TimerOffFr = request.forms.get('TimerOffFr')
        try:
            datetime.strptime(TimerOffFr,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOffFr'] = TimerOffFr
        return str(TimerOffFr)

    @post('/TimerOffSa')
    def post_TimerOffSa():
        TimerOffSa = request.forms.get('TimerOffSa')
        try:
            datetime.strptime(TimerOffSa,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOffSa'] = TimerOffSa
        return str(TimerOffSa)

    @post('/TimerOffSu')
    def post_TimerOffSu():
        TimerOffSu = request.forms.get('TimerOffSu')
        try:
            datetime.strptime(TimerOffSu,'%H:%M')
        except:
            pass
    #       abort(400,'Invalid time format.')
        state['TimerOffSu'] = TimerOffSu
        return str(TimerOffSu)


    run(host='0.0.0.0', port=conf.port, server='auto')


if __name__ == '__main__':
    from multiprocessing import Process, Manager
    from time import sleep
    from urllib2 import urlopen
    import config as conf
    import timer

    manager = Manager()
    pidstate = manager.dict()
    pidstate['snooze'] = conf.snooze
    pidstate['snoozeon'] = False
    pidstate['i'] = 0
    pidstate['settemp'] = conf.set_temp
    pidstate['avgpid'] = 0.

    state = manager.dict()    
    state['TimerOnMo'] = conf.TimerOnMo
    state['TimerOffMo'] = conf.TimerOffMo
    state['TimerOnTu'] = conf.TimerOnTu
    state['TimerOffTu'] = conf.TimerOffTu
    state['TimerOnWe'] = conf.TimerOnWe
    state['TimerOffWe'] = conf.TimerOffWe
    state['TimerOnTh'] = conf.TimerOnTh
    state['TimerOffTh'] = conf.TimerOffTh
    state['TimerOnFr'] = conf.TimerOnFr
    state['TimerOffFr'] = conf.TimerOffFr
    state['TimerOnSa'] = conf.TimerOnSa
    state['TimerOffSa'] = conf.TimerOffSa
    state['TimerOnSu'] = conf.TimerOnSu
    state['TimerOffSu'] = conf.TimerOffSu

    pidstate['awake'] = timer.timer(state)

    p = Process(target=pid_loop, args=(1, pidstate))
    p.daemon = True
    p.start()

    h = Process(target=he_control_loop, args=(1, pidstate))
    h.daemon = True
    h.start()

    r = Process(target=rest_server, args=(1, pidstate))
    r.daemon = True
    r.start()

    # Start Watchdog loop
    piderr = 0
    weberr = 0
    weberrflag = 0
    urlhc = 'http://localhost:'+str(conf.port)+'/healthcheck'

    lasti = pidstate['i']
    sleep(1)

    while p.is_alive() and h.is_alive() and r.is_alive():
        curi = pidstate['i']
        if curi == lasti:
            piderr = piderr + 1
        else:
            piderr = 0

        lasti = curi

        if piderr > 9:
            print ('ERROR IN PID THREAD, RESTARTING')
            p.terminate()

        try:
            hc = urlopen(urlhc, timeout=2)
        except:
            weberrflag = 1
        else:
            if hc.getcode() != 200:
                weberrflag = 1

        if weberrflag != 0:
            weberr = weberr + 1

        if weberr > 9:
            print ('ERROR IN WEB SERVER THREAD, RESTARTING')
            r.terminate()

        weberrflag = 0

        sleep(1)
