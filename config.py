#!/usr/bin/python
import board
#PIN 0-8 3v3 pull-up default, 9-27 pull-down default

# Pin # for relay connected to heating element (Note: GPIO pin#)
he_pin = 26

thermo_pin = board.D5
steam_pin = 22

#overriding strictly or through pin for scheduled heating. 'True' or pin=on means always on.
always_override = True
override_pin = 19

led_pin = 13

# Default goal temperature
set_temp = 96.
set_steam_temp = 145.

#Use Fahrenheit?
use_fahrenheit = False

# Default alarm time
snooze = '07:00'

# Pressure gauge
pressure_enable = True

#circuit breaker time in minutes convert to seconds
circuitBreakerTime = 20 * 60

#temp lowpoint and high point (Celsius)
low_temp_b = 0
high_temp_b = 110

low_temp_s = 130
high_temp_s = 160

# Main loop sample rate in seconds
sample_time = 0.1

# PID Proportional, Integral, and Derivative value
P = 10
I = 1.5
D = 20.0

#Web/REST Server Options
host = '0.0.0.0'
port = 8080
