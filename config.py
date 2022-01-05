#!/usr/bin/python
import board
#PIN 0-8 3v3 pull-up default, 9-27 pull-down default

# Pin # for relay connected to heating element (Note: GPIO pin#)
he_pin = 26

thermo_pin = board.D5
steam_pin = 13

#overriding strictly or through pin for scheduled heating. 'True' or pin=on means always on.
override = True
override_pin = 19

led_pin = 6

# Default goal temperature
set_temp = 96.
set_steam_temp = 145.

#Use Fahrenheit?
use_fahrenheit = False

# Default alarm time
snooze = '07:00'

#circuit breaker time in minutes convert to seconds
circuitBreakerTime = 20 * 60

#TODO: Change this into a matrix.
TimerOnMo = '08:40'
TimerOffMo = '10:00'
TimerOnTu = '08:40'
TimerOffTu = '10:00'
TimerOnWe = '08:40'
TimerOffWe = '10:00'
TimerOnTh = '08:40'
TimerOffTh = '10:00'
TimerOnFr = '08:40'
TimerOffFr = '10:00'
TimerOnSa = '10:00'
TimerOffSa = '12:00'
TimerOnSu = '10:00'
TimerOffSu = '12:00'


#temp lowpoint and high point (Celsius)
low_temp_b = 85
high_temp_b = 110

low_temp_s = 130
high_temp_s = 160

# Main loop sample rate in seconds
sample_time = 0.1

# PID Proportional, Integral, and Derivative value
P = 3.3
I = 0.3
D = 22.0

#Web/REST Server Options
host = '0.0.0.0'
port = 8080
