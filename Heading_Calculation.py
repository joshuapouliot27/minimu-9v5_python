#!/usr/bin/python
#
#	This program  reads the angles from the acceleromter, gyrscope
#	and mangnetometeron a BerryIMU connected to a Raspberry Pi.
#
#	This program includes a number of calculations to improve the
#	values returned from BerryIMU. If this is new to you, it
#	may be worthwhile first to look at berryIMU-simple.py, which
#	has a much more simplified version of code which would be easier
#	to read.
#
#
#	http://ozzmaker.com/
#
#    Copyright (C) 2016  Mark Williams
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Library General Public
#    License as published by the Free Software Foundation; either
#    version 2 of the License, or (at your option) any later version.
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    Library General Public License for more details.
#    You should have received a copy of the GNU Library General Public
#    License along with this library; if not, write to the Free
#    Software Foundation, Inc., 59 Temple Place - Suite 330, Boston,
#    MA 02111-1307, USA
import os
import time
import math
from LIS3MDL import LIS3MDL
from LSM6DS33 import LSM6DS33
import datetime

RAD_TO_DEG = 57.29578
M_PI = 3.14159265358979323846
G_GAIN = 0.00875  # [deg/s/LSB]  If you change the dps for gyro, you need to update this value accordingly
AA = 0.40  # Complementary filter constant

magXmax = 4149
magYmax = 1643
magZmax = 8910
magXmin = -2745
magYmin = -4985
magZmin = 2674

# Kalman filter variables
Q_angle = 0.02
Q_gyro = 0.0015
R_angle = 0.005
y_bias = 0.0
x_bias = 0.0
XP_00 = 0.0
XP_01 = 0.0
XP_10 = 0.0
XP_11 = 0.0
YP_00 = 0.0
YP_01 = 0.0
YP_10 = 0.0
YP_11 = 0.0
KFangleX = 0.0
KFangleY = 0.0


def kalmanFilterY(accAngle, gyroRate, DT):
    y = 0.0
    S = 0.0

    global KFangleY
    global Q_angle
    global Q_gyro
    global y_bias
    global YP_00
    global YP_01
    global YP_10
    global YP_11

    KFangleY = KFangleY + DT * (gyroRate - y_bias)

    YP_00 = YP_00 + (- DT * (YP_10 + YP_01) + Q_angle * DT)
    YP_01 = YP_01 + (- DT * YP_11)
    YP_10 = YP_10 + (- DT * YP_11)
    YP_11 = YP_11 + (+ Q_gyro * DT)

    y = accAngle - KFangleY
    S = YP_00 + R_angle
    K_0 = YP_00 / S
    K_1 = YP_10 / S

    KFangleY = KFangleY + (K_0 * y)
    y_bias = y_bias + (K_1 * y)

    YP_00 = YP_00 - (K_0 * YP_00)
    YP_01 = YP_01 - (K_0 * YP_01)
    YP_10 = YP_10 - (K_1 * YP_00)
    YP_11 = YP_11 - (K_1 * YP_01)

    return KFangleY


def kalmanFilterX(accAngle, gyroRate, DT):
    x = 0.0
    S = 0.0

    global KFangleX
    global Q_angle
    global Q_gyro
    global x_bias
    global XP_00
    global XP_01
    global XP_10
    global XP_11

    KFangleX = KFangleX + DT * (gyroRate - x_bias)

    XP_00 = XP_00 + (- DT * (XP_10 + XP_01) + Q_angle * DT)
    XP_01 = XP_01 + (- DT * XP_11)
    XP_10 = XP_10 + (- DT * XP_11)
    XP_11 = XP_11 + (+ Q_gyro * DT)

    x = accAngle - KFangleX
    S = XP_00 + R_angle
    K_0 = XP_00 / S
    K_1 = XP_10 / S

    KFangleX = KFangleX + (K_0 * x)
    x_bias = x_bias + (K_1 * x)

    XP_00 = XP_00 - (K_0 * XP_00)
    XP_01 = XP_01 - (K_0 * XP_01)
    XP_10 = XP_10 - (K_1 * XP_00)
    XP_11 = XP_11 - (K_1 * XP_01)


    return KFangleX

def readACCx():
    return gyro_accel.get_accelerometer_data().x


def readACCy():
    return gyro_accel.get_accelerometer_data().y


def readACCz():
    return gyro_accel.get_accelerometer_data().z


def readMAGx():
    return magn.get_magnetometer_data().x


def readMAGy():
    return magn.get_magnetometer_data().y


def readMAGz():
    return magn.get_magnetometer_data().z


def readGYRx():
    return gyro_accel.get_gyroscope_data().x


def readGYRy():
    return gyro_accel.get_gyroscope_data().y


def readGYRz():
    return gyro_accel.get_gyroscope_data().z

gyroXangle = 0.0
gyroYangle = 0.0
gyroZangle = 0.0
CFangleX = 0.0
CFangleY = 0.0
kalmanX = 0.0
kalmanY = 0.0

magn = LIS3MDL()
gyro_accel = LSM6DS33()

a = datetime.datetime.now()

while True:
    # Read the accelerometer,gyroscope and magnetometer values
    ACCx = readACCx()
    ACCy = readACCy()
    ACCz = readACCz()
    GYRx = readGYRx()
    GYRy = readGYRy()
    GYRz = readGYRz()
    MAGx = readMAGx()
    MAGy = readMAGy()
    MAGz = readMAGz()

    # Apply hard iron calibration to compass
    MAGx -= (magXmin + magXmax) / 2
    MAGy -= (magYmin + magYmax) / 2
    MAGz -= (magZmin + magZmax) / 2

    ##Calculate loop Period(LP). How long between Gyro Reads
    b = datetime.datetime.now() - a
    a = datetime.datetime.now()
    LP = b.microseconds / (1000000 * 1.0)

    # Convert Gyro raw to degrees per second
    rate_gyr_x = GYRx * G_GAIN
    rate_gyr_y = GYRy * G_GAIN
    rate_gyr_z = GYRz * G_GAIN

    # Calculate the angles from the gyro.
    gyroXangle += rate_gyr_x * LP
    gyroYangle += rate_gyr_y * LP
    gyroZangle += rate_gyr_z * LP

    ##Convert Accelerometer values to degrees
    AccXangle = (math.atan2(ACCy, ACCz) + M_PI) * RAD_TO_DEG
    AccYangle = (math.atan2(ACCz, ACCx) + M_PI) * RAD_TO_DEG

    ####################################################################
    ######################Correct rotation value########################
    ####################################################################
    # Change the rotation value of the accelerometer to -/+ 180 and
    # move the Y axis '0' point to up.
    #
    # Two different pieces of code are used depending on how your IMU is mounted.
    # If IMU is up the correct way, Skull logo is facing down, Use these lines
    AccXangle -= 180.0
    if AccYangle > 90:
        AccYangle -= 270.0
    else:
        AccYangle += 90.0
    #
    #
    #
    #
    # If IMU is upside down E.g Skull logo is facing up;
    # if AccXangle >180:
    #        AccXangle -= 360.0
    # AccYangle-=90
    # if (AccYangle >180):
    #        AccYangle -= 360.0
    ############################ END ##################################


    # Complementary filter used to combine the accelerometer and gyro values.
    CFangleX = AA * (CFangleX + rate_gyr_x * LP) + (1 - AA) * AccXangle
    CFangleY = AA * (CFangleY + rate_gyr_y * LP) + (1 - AA) * AccYangle

    # Kalman filter used to combine the accelerometer and gyro values.
    kalmanY = kalmanFilterY(AccYangle, rate_gyr_y, LP)
    kalmanX = kalmanFilterX(AccXangle, rate_gyr_x, LP)

    ####################################################################
    ############################MAG direction ##########################
    ####################################################################
    # If IMU is upside down, then use this line.  It isnt needed if the
    # IMU is the correct way up
    # MAGy = -MAGy
    #
    ############################ END ##################################


    # Calculate heading
    heading = 180 * math.atan2(MAGy, MAGx) / M_PI

    # Only have our heading between 0 and 360
    if heading < 0:
        heading += 360

    # Normalize accelerometer raw values.
    accXnorm = ACCx / math.sqrt(ACCx * ACCx + ACCy * ACCy + ACCz * ACCz)
    accYnorm = ACCy / math.sqrt(ACCx * ACCx + ACCy * ACCy + ACCz * ACCz)

    ####################################################################
    ###################Calculate pitch and roll#########################
    ####################################################################
    # Us these two lines when the IMU is up the right way. Skull logo is facing down
    pitch = math.asin(accXnorm)
    roll = -math.asin(accYnorm / math.cos(pitch))
    #
    # Us these four lines when the IMU is upside down. Skull logo is facing up
    # accXnorm = -accXnorm				#flip Xnorm as the IMU is upside down
    # accYnorm = -accYnorm				#flip Ynorm as the IMU is upside down
    # pitch = math.asin(accXnorm)
    # roll = math.asin(accYnorm/math.cos(pitch))
    #
    ############################ END ##################################

    # Calculate the new tilt compensated values
    magXcomp = MAGx * math.cos(pitch) + MAGz * math.sin(pitch)
    magYcomp = MAGx * math.sin(roll) * math.sin(pitch) + MAGy * math.cos(roll) - MAGz * math.sin(roll) * math.cos(pitch)

    # Calculate tilt compensated heading
    tiltCompensatedHeading = 180 * math.atan2(magYcomp, magXcomp) / M_PI

    if tiltCompensatedHeading < 0:
        tiltCompensatedHeading += 360

    os.system("clear")
    print("Complementary filter angle X: {:8.6} \t Y: {:8.6},".format(float(CFangleX), float(CFangleY)))
    print("Kalman angle               X: {:8.6} \t Y: {:8.6},".format(float(KFangleX), float(KFangleY)))
    print("Tilt Compensated Heading: {:8.6}".format(float(tiltCompensatedHeading)))
    # slow program down a bit, makes the output more readable
    time.sleep(1/10)


