#!/usr/bin/env python3

import serial
import logging
import random
from time import time
import RPi.GPIO as GPIO


port = '/dev/ttyAMA0'
baudrate = 38400
target = random.randint(0, 255)
data = target
last_run_ms = 0
curr_ms = 0
wait_ms = 0

logging.basicConfig(
        format='%(asctime)s.%(msecs)03d [%(target)s (%(target_hex)s)] %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

old_factory = logging.getLogRecordFactory()

def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.target = target
    record.target_hex = '0x{:02x}'.format(target)
    return record

logging.setLogRecordFactory(record_factory)

def move_data_towards_target(data):
    global target
    if data == target:
        target = random.randint(0,255)

    elif data < target:
        data += 1
    else:
        data -= 1
    return data

with serial.Serial(port,baudrate) as ser:
    # Toggle RESET pin on attiny
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(22, GPIO.OUT)
    GPIO.output(22, GPIO.LOW)
    GPIO.output(22, GPIO.HIGH)
    while True:
        s = ''
        while True:
            s += ser.read().decode()
            if s[-1] == '\r': break

        logging.info("< {}".format(s.replace('\r','\\r')))
        command = b''
        curr_ms = time() * 1000
        # We can safely skip configuration commands in our sim (AT*)
        if s.startswith('AT'):
            command = b'>'
        else:
            # Pick a random amount of time to wait between data changes
            if curr_ms - last_run_ms >= wait_ms:
                last_run_ms = time() * 1000
                wait_ms = random.randint(100,3000)
                data = move_data_towards_target(data)
            # Set command to a mock elm327 response which includes the data
            command = '7E8 03 41 05 {:02x} \r\r>'.format(data).encode()
        logging.info("> {}".format(command.decode().replace('\r','\\r')))
        # Reply to device with command    
        ser.write(command)
