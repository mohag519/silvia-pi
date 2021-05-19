#!/usr/bin/python

from time import sleep, time
import config as conf

"""
Input:timeSinceLastSteal
output : steam, circuitbreaker, timeSinceLastSteaming
"""
def steaming(timeSinceLastSteaming):
    print("line11")
    if conf.steam_pin == True:
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
    