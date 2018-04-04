import curses
import json, logging, os
import platform

import time, sys, gc

import asyncio

from Fusion_Filter import Fusion
from LIS3MDL import LIS3MDL
from LSM6DS33 import LSM6DS33


class magnetometer:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class gyroscope:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class accelerometer:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class imu_data_obj:
    def __init__(self, magn, gyro, accel):
        self.magnetometer = magn
        self.gyroscope = gyro
        self.accelerometer = accel


log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
root_logger = logging.getLogger()

file_handler = logging.FileHandler("log.log")
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)

config_file = "calibration_data.json"
octave_script_dir = "./octave_scripts"

imu_data = imu_data_obj(magnetometer(0, 0, 0), gyroscope(0, 0, 0), accelerometer(0, 0, 0))
lsm6ds33 = LSM6DS33()
lis3mdl = LIS3MDL()
poll_rate = 50  # type: int
display_rate = 10  # type: int


def poll_imu():
    global imu_data

    if lsm6ds33 is not None and lis3mdl is not None:
        gyro = lsm6ds33.get_gyroscope_data()
        accel = lsm6ds33.get_accelerometer_data()
        magn = lis3mdl.get_magnetometer_data()
        imu_data = imu_data_obj(magnetometer(magn.x, magn.y, magn.z),
                                gyroscope(gyro.x, gyro.y, gyro.z),
                                accelerometer(accel.x, accel.y, accel.z))


async def read_coro():
    poll_imu()
    await asyncio.sleep(1 / poll_rate)
    return (imu_data.accelerometer.x, imu_data.accelerometer.y, imu_data.accelerometer.z), (
        imu_data.gyroscope.x, imu_data.gyroscope.y, imu_data.gyroscope.z), (
               imu_data.magnetometer.x, imu_data.magnetometer.y, imu_data.magnetometer.z)


async def save_calibration(fuse):
    mag_cal = fuse.get_mag_bias()
    calibration = {
        "x": mag_cal[0],
        "y": mag_cal[1],
        "z": mag_cal[2]
    }
    with open(config_file, 'w') as file:
        json.dump(calibration, file)


async def get_calibration():
    with open(config_file, 'r') as file:
        calibration = json.load(file)
        mag_cal = (
            calibration["x"],
            calibration["y"],
            calibration["z"]
        )
        return mag_cal


async def mem_manage():  # Necessary for long term stability
    while True:
        await asyncio.sleep(100 / 1000)
        gc.collect()


async def display():
    fs = 'Yaw: {:4.0f}\tPitch: {:4.0f}\tRoll: {:4.0f}'
    mg = 'Magnetometer:\t\tx: {:4.0f}\t\ty: {:4.0f}\t\tz: {:4.0f}'
    ac = 'Accelerometer:\t\tx: {:4.0f}\t\ty: {:4.0f}\t\tz: {:4.0f}'
    gy = 'Gyroscope:\t\tx: {:4.0f}\t\ty: {:4.0f}\t\tz: {:4.0f}'
    while True:
        os.system("clear")
        print(fs.format(fuse.heading, fuse.pitch, fuse.roll))
        print(mg.format(imu_data.magnetometer.x, imu_data.magnetometer.y, imu_data.magnetometer.z))
        print(ac.format(imu_data.accelerometer.x, imu_data.accelerometer.y, imu_data.accelerometer.z))
        print(gy.format(imu_data.gyroscope.x, imu_data.gyroscope.y, imu_data.gyroscope.z))
        await asyncio.sleep(1 / display_rate)


async def test():
    screen = curses.initscr()
    screen.clear()
    screen.addstr(0, 0, "Calibrate the IMU, press sny key when done.")
    screen.nodelay(False)
    try:
        calibration = get_calibration()
        fuse.set_mag_bias(calibration)
    except:
        await fuse.calibrate(lambda: screen.getch() is not None)
        save_calibration(fuse)
    screen.nodelay(True)
    curses.endwin()
    await fuse.start()
    loop = asyncio.get_event_loop()
    loop.create_task(display())


fuse = Fusion(read_coro)


def testt():
    print("Starting...")
    time.sleep(1)
    loop = asyncio.get_event_loop()
    loop.create_task(mem_manage())
    loop.create_task(test())
    loop.run_forever()


testt()
