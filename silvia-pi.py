#!/usr/bin/python
def he_control_loop(_, state, timeState):
    from time import sleep
    import RPi.GPIO as GPIO
    import config as conf

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(conf.he_pin, GPIO.OUT)
    GPIO.output(conf.he_pin, 0)

    heating_interval = 1

    try:
        while True:
            state['awake'] = timer.timer(timeState)
            pidval = state['pidval']
            
            if not state['awake'] or state['circuitBreaker']:
                state['heating'] = False
                GPIO.output(conf.he_pin, 0)
                sleep(heating_interval)
            else:
                if pidval >= 100:
                    state['heating'] = True
                    GPIO.output(conf.he_pin, 1)
                    sleep(heating_interval)
                elif pidval > 0 and pidval < 100:
                    GPIO.output(conf.he_pin, 1)
                    state['heating'] = True
                    sleep(pidval//100.)
                    GPIO.output(conf.he_pin, 0)
                    state['heating'] = False
                    sleep(heating_interval-(pidval//100.))
                else:
                    GPIO.output(conf.he_pin, 0)
                    state['heating'] = False
                    sleep(heating_interval)
    finally:
        GPIO.output(conf.he_pin, 0)
        GPIO.cleanup()

def pid_loop(dummy, state):
    import sys
    from time import sleep, time
    from math import isnan
    import adafruit_max31855 as MAX31855
    import board
    import PID as PID
    import config as conf
    from brewOrSteaming import steaming
    import RPi.GPIO as GPIO
    import digitalio

    sensorPin = digitalio.DigitalInOut(conf.thermo_pin)
    sensor = MAX31855.MAX31855(board.SPI(), sensorPin)

    pid = PID.PID(state['Kp'], state['Ki'], state['Kd'])
    pid.SetPoint = state['settemp']
    pid.setSampleTime(conf.sample_time)

    nanct = 0
    i = 0
    pidhist = [0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    avgpid = 0.
    temphist = [0., 0., 0., 0., 0.]
    avgtemp = 0.
    circuitBreaker = False
    timeSinceLastSteam = None

    try:
        while True:  # Loops 10x/second
            pid.setKp(state['Kp'])
            pid.setKi(state['Ki'])
            pid.setKd(state['Kd'])

            temp = sensor.temperature
            steam,circuitBreaker,timeSinceLastSteam = steaming(timeSinceLastSteam)
            state['steam'] = steam
            state['circuitBreaker'] = circuitBreaker

            if isnan(temp):
                nanct += 1
                if nanct > 100000:
                    print("ERROR IN READING TEMPERATURE")
                    sys.exit
                continue
            else:
                nanct = 0

            temphist[i % 5] = temp
            avgtemp = sum(temphist)//len(temphist)
            
            #circuitbreaker is on
            if circuitBreaker:
                continue

            if steam and state['steamtemp'] != pid.SetPoint:
                pid.SetPoint = state['steamtemp']
            elif not steam and state['settemp'] != pid.SetPoint:
                pid.SetPoint = state['settemp']

            pid.update(avgtemp)
            pidout = pid.output
            pidhist[i % 5] = pidout
            avgpid = sum(pidhist)//len(pidhist)

            state['i'] = i
            state['temp'] = temp
            state['avgtemp'] = round(avgtemp, 2)
            state['setpoint'] = pid.SetPoint
            state['pidval'] = round(pidout, 2)
            state['avgpid'] = round(avgpid, 2)
            state['pterm'] = round(pid.PTerm, 2)
            state['iterm'] = round(pid.ITerm * conf.I, 2)
            state['dterm'] = round(pid.DTerm * conf.D, 2)
            state['Kp'] = round(pid.Kp, 2)
            state['Ki'] = round(pid.Ki, 2)
            state['Kd'] = round(pid.Kd, 2)

            if i % 10 == 0:
                printState(state)

            sleep(conf.sample_time)
            i += 1

    finally:
        GPIO.cleanup()
        sensorPin.deinit()
        pid.clear

def printState(state):
    for key, value in state.items():
        print(f'{key} : {value}')

if __name__ == '__main__':
    from multiprocessing import Process, Manager
    from time import sleep
    from urllib.request import urlopen
    import config as conf
    import timer
    from restServer import rest_server
    import RPi.GPIO as GPIO

    manager = Manager()
    pidstate = manager.dict()
    pidstate['snooze'] = conf.snooze
    pidstate['snoozeon'] = False
    pidstate['i'] = 0
    pidstate['settemp'] = conf.set_temp
    pidstate['steamtemp'] = conf.set_steam_temp
    pidstate['circuitBreaker'] = None
    pidstate['steam'] = False
    pidstate['pidval'] = 0.
    pidstate['avgpid'] = 0.
    pidstate['Kp'] = conf.P
    pidstate['Ki'] = conf.I
    pidstate['Kd'] = conf.D

    timeState = manager.dict()    
    timeState['TimerOnMo'] = conf.TimerOnMo
    timeState['TimerOffMo'] = conf.TimerOffMo
    timeState['TimerOnTu'] = conf.TimerOnTu
    timeState['TimerOffTu'] = conf.TimerOffTu
    timeState['TimerOnWe'] = conf.TimerOnWe
    timeState['TimerOffWe'] = conf.TimerOffWe
    timeState['TimerOnTh'] = conf.TimerOnTh
    timeState['TimerOffTh'] = conf.TimerOffTh
    timeState['TimerOnFr'] = conf.TimerOnFr
    timeState['TimerOffFr'] = conf.TimerOffFr
    timeState['TimerOnSa'] = conf.TimerOnSa
    timeState['TimerOffSa'] = conf.TimerOffSa
    timeState['TimerOnSu'] = conf.TimerOnSu
    timeState['TimerOffSu'] = conf.TimerOffSu

    # timeState['override'] = conf.always_override

    pidstate['awake'] = timer.timer(timeState)

    p = Process(target=pid_loop, args=(1, pidstate))
    p.daemon = True
    p.start()

    h = Process(target=he_control_loop, args=(1, pidstate, timeState))
    h.daemon = True
    h.start()

    r = Process(target=rest_server, args=(1, pidstate, timeState))
    r.daemon = True
    r.start()

    # Start Watchdog loop
    piderr = 0
    weberr = 0
    weberrflag = 0
    urlhc = 'http://localhost:'+str(conf.port)+'/healthcheck'

    lasti = pidstate['i']
    sleep(1)

    #Setting up led, will in this case work as a indicator if mainprocess is running
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(conf.led_pin, GPIO.OUT)
    GPIO.output(conf.led_pin, 0)

    try:
        while p.is_alive() and h.is_alive() and r.is_alive():
            GPIO.output(conf.led_pin, 1)
            curi = pidstate['i']
            if curi == lasti:
                piderr = piderr + 1
            else:
                piderr = 0

            if piderr > 9:
                print ('ERROR IN PID THREAD, RESTARTING')
                p.terminate()
            
            lasti = curi

            try:
                healthcheck = urlopen(urlhc, timeout=10)
            except:
                weberrflag = 1
            else:
                if healthcheck.getcode() != 200:
                    weberrflag = 1

            if weberrflag != 0:
                weberr = weberr + 1

            if weberr > 9:
                print ('ERROR IN WEB SERVER THREAD, RESTARTING')
                r.terminate()

            weberrflag = 0

            sleep(1)
    finally:
        GPIO.cleanup()
