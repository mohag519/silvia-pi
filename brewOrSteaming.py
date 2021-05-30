#!/usr/bin/python

from time import sleep, time
import config as conf
import RPi.GPIO as GPIO

"""
Input:timeSinceLastSteal
output : steam, circuitbreaker, timeSinceLastSteaming
"""
def steaming(timeSinceLastSteaming):
    steam_pin = GPIO.input(conf.steam_pin)

    print("steam pin is ",steam_pin)
    if steam_pin == True:
        print("steaming")
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
    