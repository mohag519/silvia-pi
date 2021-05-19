#!/usr/bin/python

from time import sleep, time
import config as conf
import RPi.GPIO as GPIO

"""
Input:timeSinceLastSteal
output : steam, circuitbreaker, timeSinceLastSteaming
"""
def steaming(timeSinceLastSteaming):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(conf.steam_pin,GPIO.IN,initial=0)
    steam_pin = GPIO.input(conf.steam_pin)

    print("steam pin is ",steam_pin)
    if steam_pin == True:
        print("steaming")
        #TODO add protection timer to turn off steam even after a while for protection,TURNOFF COMPLETELY
        #resetted steam pin since new press
        if timeSinceLastSteaming == None:
            timeSinceLastSteaming = time()
        
        #steam working fine
        if time() - timeSinceLastSteaming < conf.circuitBreakerTime:
            return True,False,timeSinceLastSteaming
        #circuit protection
        return False, True, timeSinceLastSteaming
    #not steaming = espresso temp
    else:
        return False,False,None
    