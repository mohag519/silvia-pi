#!/usr/bin/python

from datetime import timedelta


def he_control_loop(_, state):
    from time import sleep
    import RPi.GPIO as GPIO
    import config as conf

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(conf.he_pin, GPIO.OUT)
    GPIO.output(conf.he_pin, 0)

    heating_interval = 0.5

    try:
        while True:
            pidval = state['pidval']
            
            if not state['awake'] or state['circuitBreaker']:
                state['heating'] = False
                GPIO.output(conf.he_pin, 0)
                sleep(heating_interval)
            else:
                if pidval >= 50:
                    state['heating'] = True
                    GPIO.output(conf.he_pin, 1)
                    sleep(heating_interval)
                elif pidval > 0 and pidval < 50:
                    #closest_ten = math.ceil(pidval * 10 / 50) // 10 # ex: 63.3 => 0.7

                    GPIO.output(conf.he_pin, 1)
                    state['heating'] = True
                    sleep(heating_interval * (pidval / 50))

                    GPIO.output(conf.he_pin, 0)
                    state['heating'] = False
                    sleep(heating_interval - heating_interval * (pidval / 50))
                else:
                    GPIO.output(conf.he_pin, 0)
                    state['heating'] = False
                    sleep(heating_interval)
    
    finally:
        GPIO.output(conf.he_pin, 0)
        GPIO.cleanup()

def pid_loop(_, state):
    import sys
    import time
    from math import isnan
    import Adafruit_ADS1x15 as ADS1x15
    import PID as PID
    import config as conf
    from brewOrSteaming import steaming
    import RPi.GPIO as GPIO    


    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(conf.brew_pin,GPIO.IN,GPIO.PUD_DOWN)

    pid = PID.PID(state['Kp'], state['Ki'], state['Kd'])
    pid.SetPoint = state['settemp']
    pid.setSampleTime(conf.sample_time)
    
    brew_pin = GPIO.input(conf.brew_pin)
    start_time = None
    end_time = None
    timeDiff = 0

    nanct = 0
    i = 0
    temphist = [0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    avgtemp = 0.
    circuitBreaker = False
    timeSinceLastSteam = None

    adc = ADS1x15.ADS1115()
    
    try:
        while True:  # Loops every <sample-time>
            pid.setKp(state['Kp'])
            pid.setKi(state['Ki'])
            pid.setKd(state['Kd'])

            temp = read_temperature(adc)
            
            if(conf.pressure_enable):
                pressure = read_pressure(adc)
            
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

            temphist[i % len(temphist)] = temp
            avgtemp = sum(temphist)/len(temphist)
            
            #circuitbreaker is on
            if circuitBreaker:
                continue

            if steam and state['steamtemp'] != pid.SetPoint:
                pid.SetPoint = state['steamtemp']
            elif not steam and state['settemp'] != pid.SetPoint:
                pid.SetPoint = state['settemp']

            pid.update(avgtemp)
            pidout = pid.output

            #Calculating brewtime
            new_brew_pin = GPIO.input(conf.brew_pin)
            if new_brew_pin != brew_pin:
                brew_pin = new_brew_pin
                if new_brew_pin == GPIO.HIGH:
                    start_time = time.time()
                    end_time = None
                elif start_time != None:
                    end_time = time.time()
                    timeDiff = end_time - start_time
            elif start_time != None:
                if end_time == None:
                    timeDiff =  time.time() - start_time
                else:
                    timeDiff = end_time - start_time
                    
            state['brewtime'] = timeDiff

            state['i'] = i
            state['temp'] = temp
            if conf.pressure_enable :
                state['pressure'] = pressure
            state['avgtemp'] = round(avgtemp, 2)
            state['setpoint'] = pid.SetPoint
            state['pidval'] = round(pidout, 2)
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
        pid.clear

def read_temperature(adc):
    averageFactor = 3
    tempAvg = [0 for _ in range(averageFactor)]
    # Choose a gain of 1 for reading voltages from 0 to 4.09V.
    # Or pick a different gain to change the range of voltages that are read:
    #  - 2/3 = +/-6.144V
    #  -   1 = +/-4.096V
    #  -   2 = +/-2.048V
    #  -   4 = +/-1.024V
    #  -   8 = +/-0.512V
    #  -  16 = +/-0.256V
    # See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
    GAIN = 2
    for i in range(averageFactor):
        vOut = (adc.read_adc(0, GAIN) * 2.048) / 32767 
        #Temperature = (Vout - 1.25) / 0.005 V
        tempAvg[i] = (vOut - 1.25) / 0.005 - 4 #I have no idea why it's 4 degrees off
    return sum(tempAvg)/averageFactor

def read_pressure(adc):
    averageFactor = 1
    pressureAvg = [0 for _ in range(averageFactor)]
    # Choose a gain of 1 for reading voltages from 0 to 4.09V.
    # Or pick a different gain to change the range of voltages that are read:
    #  - 2/3 = +/-6.144V
    #  -   1 = +/-4.096V
    #  -   2 = +/-2.048V
    #  -   4 = +/-1.024V
    #  -   8 = +/-0.512V
    #  -  16 = +/-0.256V
    # See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
    GAIN = 2/3
    for i in range(averageFactor):
        vOut = (adc.read_adc(1, GAIN) * 6.144) / 32767
        pressureAvg[i] = (vOut / 5) * 10
    return sum(pressureAvg) / averageFactor

def printState(state):
    for key, value in state.items():
        if key == 'brewtime':
            print(f'{key} : {value}')

if __name__ == '__main__':
    from multiprocessing import Process, Manager
    from time import sleep
    from urllib.request import urlopen
    import config as conf
    from restServer import rest_server
    import RPi.GPIO as GPIO

    manager = Manager()
    state = manager.dict()
    state['snooze'] = conf.snooze
    state['snoozeon'] = False
    state['i'] = 0
    state['settemp'] = conf.set_temp
    state['steamtemp'] = conf.set_steam_temp
    state['circuitBreaker'] = None
    state['steam'] = False
    state['pidval'] = 0.
    state['Kp'] = conf.P
    state['Ki'] = conf.I
    state['Kd'] = conf.D
    state['brewtime'] = None

    state['awake'] = True

    p = Process(target=pid_loop, args=(1, state))
    p.daemon = True
    p.start()

    h = Process(target=he_control_loop, args=(1, state))
    h.daemon = True
    h.start()

    r = Process(target=rest_server, args=(1, state))
    r.daemon = True
    r.start()

    # Start Watchdog loop
    piderr = 0
    weberr = 0
    weberrflag = 0
    urlhc = 'http://localhost:'+str(conf.port)+'/healthcheck'

    lasti = state['i']
    sleep(1)

    #Setting up led, will in this case work as a indicator if mainprocess is running
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(conf.led_pin, GPIO.OUT)
    GPIO.output(conf.led_pin, 0)

    try:
        while p.is_alive() and h.is_alive() and r.is_alive():
            GPIO.output(conf.led_pin, 1)
            curi = state['i']
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
                else:
                    weberrflag = 0

            if weberrflag != 0:
                weberr = weberr + 1

            if weberr > 99:
                print ('ERROR IN WEB SERVER THREAD, RESTARTING')
                r.terminate()

            weberrflag = 0

            sleep(1)
    finally:
        GPIO.cleanup()
