#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Driver.py
#
# Solar-boat Project 2019
#   created on: 2019/07/27
#   Author: Tetsuro Ninomiya
#

from State import State
from Params import Params
from Status import Status
from Logger import Logger
from PwmOut import PwmOut
from PwmRead import PwmRead
from Pid import PositionalPID
from ina226 import ina226

import time
import sys

INA226_ADDRESS = 0x40

ina226_averages_t = dict(
    INA226_AVERAGES_1=0b000,
    INA226_AVERAGES_4=0b001,
    INA226_AVERAGES_16=0b010,
    INA226_AVERAGES_64=0b011,
    INA226_AVERAGES_128=0b100,
    INA226_AVERAGES_256=0b101,
    INA226_AVERAGES_512=0b110,
    INA226_AVERAGES_1024=0b111,
)


class Driver:
    def __init__(self):
        self.state = State(0)
        self.params = Params()
        self.status = Status(self.params)
        self.sleep_time = 1
        self.pwm_read = PwmRead(
            self.params.pin_mode_in,
            self.params.pin_servo_in,
            self.params.pin_thruster_in,
            self.params.pin_OR,
        )
        self.pwm_out = PwmOut(self.params.pin_servo_out, self.params.pin_thruster_out)
        self.pid = PositionalPID()
        self.logger = Logger()
        self.logger.open()
        # Whether experienced OR mode or not
        self.or_experienced = False

        # setup for ina226
        print("Configuring INA226..")
        self.iSensor = ina226(INA226_ADDRESS, 1)
        self.iSensor.configure(
            avg=ina226_averages_t["INA226_AVERAGES_4"],
        )
        self.iSensor.calibrate(rShuntValue=0.002, iMaxExcepted=1)

        time.sleep(1)

        print("Configuration Done")

        current = self.iSensor.readShuntCurrent()

        print("Current Value is " + str(current) + "A")

        print("Mode is " + str(hex(self.iSensor.getMode())))

    def load(self, filename):
        print("loading", filename)
        f = open(filename, "r")

        line = f.readline()
        line = f.readline()
        self.state.time_limit = int(line.split()[1])  # Time Limit
        line = f.readline()
        self.sleep_time = float(line.split()[1])  # Sleep time

        line = f.readline()
        line = f.readline()
        line = f.readline()
        p = float(line.split()[1])  # P
        line = f.readline()
        i = float(line.split()[1])  # I
        line = f.readline()
        d = float(line.split()[1])  # D
        self.pid.setPID(p, i, d)

        line = f.readline()
        line = f.readline()
        line = f.readline()
        num = int(line.split()[1])  # Number of waypoints
        line = f.readline()
        for i in range(num):
            line = f.readline()
            self.status.waypoint.addPoint(
                float(line.split()[0]), float(line.split()[1])
            )
        f.close()
        return

    def doOperation(self):
        while self.state.inTimeLimit():
            self.readPWM()
            self.readGps()

            # for test
            self.pwm_read.printPulseWidth()
            # ina226
            print(
                "Current: "
                + str(round(self.iSensor.readShuntCurrent(), 3))
                + "A"
                + ", Voltage: "
                + str(round(self.iSensor.readBusVoltage(), 3))
                + "V"
                + ", Power:"
                + str(round(self.iSensor.readBusPower(), 3))
                + "W"
            )

            mode = self.getMode()
            if mode == "RC":
                self.remoteControl()
            elif mode == "AN":
                self.autoNavigation()
            elif mode == "OR":
                self.outOfRangeOperation()

            self.outPWM()
            self.printLog()
            time.sleep(self.sleep_time)
        return

    def getMode(self):
        return self.status.mode

    def updateMode(self):
        mode_duty_ratio = self.pwm_read.pulse_width[0]
        or_pulse = self.pwm_read.pulse_width[3]
        # OR mode
        if or_pulse < 1300 or (1500 <= mode_duty_ratio and self.or_experienced):
            if not self.or_experienced:
                self.status.updateWayPoint()
            self.status.mode = "OR"
            self.or_experienced = True
        # RC mode
        elif 0 < mode_duty_ratio < 1500:
            self.status.mode = "RC"
        # AN mode
        elif 1500 <= mode_duty_ratio and not self.or_experienced:
            self.status.mode = "AN"
        else:
            print("Error: mode updating failed", file=sys.stderr)
        return

    def readGps(self):
        self.status.readGps()
        self.updateMode()
        # if self.status.isGpsError():
        # self.status.mode = 'RC'
        return

    def updateStatus(self):
        status = self.status
        status.calcTargetDirection()
        status.calcTargetDistance()
        status.updateTarget()
        return

    # Read pwm pulsewidth
    # Set the readout signals as the output signals
    def readPWM(self):
        self.pwm_read.measurePulseWidth()
        self.pwm_out.servo_pulsewidth = self.pwm_read.pulse_width[1]
        self.pwm_out.thruster_pulsewidth = self.pwm_read.pulse_width[2]
        return

    def outPWM(self):
        self.pwm_out.updatePulsewidth()
        return

    def autoNavigation(self):
        self.updateStatus()
        boat_direction = self.status.boat_direction
        target_direction = self.status.target_direction
        servo_pulsewidth = self.pid.getStepSignal(target_direction, boat_direction)
        self.pwm_out.servo_pulsewidth = servo_pulsewidth
        self.pwm_out.thruster_pulsewidth = 1250
        return

    def remoteControl(self):
        # Do nothing
        return

    def outOfRangeOperation(self):
        # Be stationary
        # self.pwm_out.finalize()
        # update waypoint where the boat was
        self.autoNavigation()
        return

    def printLog(self):
        timestamp_string = self.status.timestamp_string
        mode = self.getMode()
        latitude = self.status.latitude
        longitude = self.status.longitude
        speed = self.status.speed
        direction = self.status.boat_direction
        servo_pw = self.pwm_out.servo_pulsewidth
        thruster_pw = self.pwm_out.thruster_pulsewidth
        t_direction = self.status.target_direction
        t_distance = self.status.target_distance
        target = self.status.waypoint.getPoint()
        t_latitude = target[0]
        t_longitude = target[1]
        err = self.pid.ErrBack
        current = str(round(self.iSensor.readShuntCurrent(), 3))
        voltage = str(round(self.iSensor.readBusVoltage(), 3))
        power = str(round(self.iSensor.readBusPower(), 3))

        # To print logdata
        print(timestamp_string)
        print(
            "[%s MODE] LAT=%.7f, LON=%.7f, SPEED=%.2f [km/h], DIRECTION=%lf"
            % (mode, latitude, longitude, speed, direction)
        )
        print(
            "DUTY (SERVO, THRUSTER):       (%6.1f, %6.1f) [us]"
            % (servo_pw, thruster_pw)
        )
        print("TARGET (LATITUDE, LONGITUDE): (%.7f, %.7f)" % (t_latitude, t_longitude))
        print(
            "TARGET (DIRECTION, DISTANCE): (%5.2f, %5.2f [m])"
            % (t_direction, t_distance)
        )
        print("")

        # To write logdata (csv file)
        log_list = [
            timestamp_string,
            mode,
            latitude,
            longitude,
            direction,
            speed,
            t_latitude,
            t_longitude,
            servo_pw,
            thruster_pw,
            t_direction,
            t_distance,
            err,
            current,
            voltage,
            power,
        ]
        self.logger.write(log_list)
        return

    def finalize(self):
        self.logger.close()
        self.pwm_out.finalize()
        return


if __name__ == "__main__":
    print("Driver")
    driver = Driver()
    driver.load("parameter_sample.txt")
