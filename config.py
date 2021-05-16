#!/usr/bin/python

# Raspberry Pi SPI Port and Device
spi_port = 0
spi_dev = 0

# Pin # for relay connected to heating element
he_pin = 26

# Default goal temperature
set_temp = 93.

# Default alarm time
snooze = '07:00'


TimerOnMo = '06:00'
TimerOffMo = '23:00'
TimerOnTu = '06:00'
TimerOffTu = '23:00'
TimerOnWe = '06:00'
TimerOffWe = '23:00'
TimerOnTh = '06:00'
TimerOffTh = '23:00'
TimerOnFr = '06:00'
TimerOffFr = '23:00'
TimerOnSa = '06:00'
TimerOffSa = '23:00'
TimerOnSu = '00:00'
TimerOffSu = '23:00'


#temp lowpoint and high point
low_temp_b = 85
high_temp_b = 110

# Main loop sample rate in seconds
sample_time = 0.1

# PID Proportional, Integral, and Derivative values
Pc = 3.4
Ic = 0.3
Dc = 20.#40.0

Pw = 2.9
Iw = 0.3
Dw = 40.0

#Web/REST Server Options
port = 8080
