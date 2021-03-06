#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Pwm.py
#
# Solar-boat Project 2019
#   created on: 2019/08/01
#   Author: Tetsuro Ninomiya
#

import RPi.GPIO as GPIO
import time
from queue import Queue


class PwmRead:
    def __init__(self, pin_mode, pin_servo, pin_thruster, pin_OR):
        self.pin_servo = pin_servo
        self.pin_thruster = pin_thruster
        self.pin_mode = pin_mode
        self.pulse_width = [0.0, 0.0, 0.0, 1500.0]  # [us] # mode, servo, thruster, OR
        self.num_cycles = 7
        self.pin_OR = pin_OR
        # variables for out of range
        self._or_queue = Queue()
        self._or_queue_size = 20
        for _ in range(self._or_queue_size):
            self._or_queue.put(1500)
        self._or_mean = 1500

        # setup for GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_servo, GPIO.IN)
        GPIO.setup(pin_thruster, GPIO.IN)
        GPIO.setup(pin_mode, GPIO.IN)
        GPIO.setup(pin_OR, GPIO.IN)

    def measurePulseWidth(self):
        """
        PWM frequency is 50 Hz
        So a pulse width must be under 20 ms
        The range of the receiver's signal(ON) is 1.0 ~ 2.0 ms
        1.0 ms : LOW
        1.5 ms : Neutral
        2.0 ms : HIGH

        There is a little delay, 0.01 ~ 0.03 ms
        For an error, if range is above 2.0 ms, not counted

        (M-02)
        [MODE]
        above 2.0 ms : DOWN
        under 1.0 ms : UP

        [SERVO][THRUSTER]
        max 1.94 ms     : DOWN
        neutral 1.53 ms
        min 1.13 ms     : UP
        """
        # print(PwmRead.num_cycles)
        # a = time.time()

        # mode
        sum = 0.0
        num_error = 0
        for i in range(self.num_cycles):
            GPIO.wait_for_edge(self.pin_mode, GPIO.RISING)
            start = time.time()
            GPIO.wait_for_edge(self.pin_mode, GPIO.FALLING)
            pulse = (time.time() - start) * 1000 * 1000
            if (pulse > 900) and (pulse < 2200):
                sum = sum + pulse
            else:
                num_error = num_error + 1

        if self.num_cycles != num_error:
            ave = sum / (self.num_cycles - num_error)
            if (ave > 700) and (ave < 2300):
                self.pulse_width[0] = ave

        # servo
        sum = 0.0
        num_error = 0
        for i in range(self.num_cycles):
            GPIO.wait_for_edge(self.pin_servo, GPIO.RISING)
            start = time.time()
            GPIO.wait_for_edge(self.pin_servo, GPIO.FALLING)
            pulse = (time.time() - start) * 1000 * 1000
            if (pulse > 900) and (pulse < 2200):
                sum = sum + pulse
            else:
                num_error = num_error + 1

        if self.num_cycles != num_error:
            ave = sum / (self.num_cycles - num_error)
            if (ave > 1000) and (ave < 2000):
                self.pulse_width[1] = ave -350

        # thruster
        sum = 0.0
        num_error = 0
        for i in range(self.num_cycles):
            GPIO.wait_for_edge(self.pin_thruster, GPIO.RISING)
            start = time.time()
            GPIO.wait_for_edge(self.pin_thruster, GPIO.FALLING)
            pulse = (time.time() - start) * 1000 * 1000
            if (pulse > 900) and (pulse < 2200):
                sum = sum + pulse
            else:
                num_error = num_error + 1

        if self.num_cycles != num_error:
            ave = sum / (self.num_cycles - num_error)
            ave = round(ave, -2)
            if (ave > 1000) and (ave < 2000):
                if ave < 1100:
                    self.pulse_width[2] = 1100
                elif ave > 1900:
                    self.pulse_width[2] = 1900
                else:
                    self.pulse_width[2] = ave

        # b = time.time() - a
        # print("It takes ", b, "[s] to measure PWM")

        # insert measurement pin_OR # calculation self.pulse_width[3]
        GPIO.wait_for_edge(self.pin_OR, GPIO.RISING)
        start = time.time()
        GPIO.wait_for_edge(self.pin_OR, GPIO.FALLING)
        latest_or_pulse = (time.time() - start) * 1000 * 1000

        # update queue
        oldest_or_pulse = self._or_queue.get()
        self._or_queue.put(latest_or_pulse)

        # update mean value
        self._or_mean += (latest_or_pulse - oldest_or_pulse) / self._or_queue_size

        self.pulse_width[3] = self._or_mean

        return

    def printPulseWidth(self):
        print("mode:     ", self.pulse_width[0], "[us]")
        print("servo:    ", self.pulse_width[1], "[us]")
        print("thruster: ", self.pulse_width[2], "[us]")
        print("OR_judgement: ", self.pulse_width[3], "[us]")
        print("")
        return

    def finalize(self):
        GPIO.cleanup(self.pin_mode)
        GPIO.cleanup(self.pin_servo)
        GPIO.cleanup(self.pin_thruster)
        GPIO.cleanup(self.pin_OR)
        return


# test code
if __name__ == "__main__":
    pwm_read = PwmRead(4, 2, 3)
    for i in range(20):
        time.sleep(1)
        pwm_read.measurePulseWidth()
        pwm_read.printPulseWidth()
    pwm_read.finalize()
