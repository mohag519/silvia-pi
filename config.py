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
