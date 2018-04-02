import curses
import json, logging, os
import platform

import time

import sys

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

gyro_min = gyroscope(9999999, 9999999, 9999999)
gyro_max = gyroscope(0, 0, 0)
accel_min = accelerometer(9999999, 9999999, 9999999)
accel_max = accelerometer(0, 0, 0)
magn_min = magnetometer(9999999, 9999999, 9999999)
magn_max = magnetometer(0, 0, 0)
ellipsoid_coeff = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
imu_data = imu_data_obj(magnetometer(0, 0, 0), gyroscope(0, 0, 0), accelerometer(0, 0, 0))
lsm6ds33 = LSM6DS33()
lis3mdl = LIS3MDL()
poll_rate = 25  # type: int


def poll_imu():
    global imu_data

    if lsm6ds33 is not None and lis3mdl is not None:
        gyro = lsm6ds33.get_gyroscope_data()
        accel = lsm6ds33.get_accelerometer_data()
        magn = lis3mdl.get_magnetometer_data()
        imu_data = imu_data_obj(magnetometer(magn.x, magn.y, magn.z),
                                gyroscope(gyro.x, gyro.y, gyro.z),
                                accelerometer(accel.x, accel.y, accel.z))


def save_calibration():
    config = {
        "gyro_x_max": gyro_max.x, "gyro_x_min": gyro_min.x, "gyro_y_max": gyro_max.y,
        "gyro_y_min": gyro_min.y, "gyro_z_max": gyro_max.z, "gyro_z_min": gyro_min.z,
        "accel_x_max": accel_max.x, "accel_x_min": accel_min.x, "accel_y_max": accel_max.y,
        "accel_y_min": accel_min.y, "accel_z_max": accel_max.z, "accel_z_min": accel_min.z,
        "magn_x_max": magn_max.x, "magn_x_min": magn_min.x, "magn_y_max": magn_max.y,
        "magn_y_min": magn_min.y, "magn_z_max": magn_max.z, "magn_z_min": magn_min.z,
        "ellip_coeff_1": ellipsoid_coeff[0], "ellip_coeff_2": ellipsoid_coeff[1],
        "ellip_coeff_3": ellipsoid_coeff[2], "ellip_coeff_4": ellipsoid_coeff[3],
        "ellip_coeff_5": ellipsoid_coeff[4], "ellip_coeff_6": ellipsoid_coeff[5],
        "ellip_coeff_7": ellipsoid_coeff[6], "ellip_coeff_8": ellipsoid_coeff[7]
    }
    with open(config_file, 'w') as file:
        json.dump(config, file)


def check_min_max_data():
    if gyro_max.x <= gyro_min.x or gyro_max.x <= 0 or gyro_min.x >= 9999999:
        return False
    if gyro_max.y <= gyro_min.y or gyro_max.y <= 0 or gyro_min.y >= 9999999:
        return False
    if gyro_max.z <= gyro_min.z or gyro_max.z <= 0 or gyro_min.z >= 9999999:
        return False
    if magn_max.x <= magn_min.x or magn_max.x <= 0 or magn_min.x >= 9999999:
        return False
    if magn_max.y <= magn_min.y or magn_max.y <= 0 or magn_min.y >= 9999999:
        return False
    if magn_max.z <= magn_min.z or magn_max.z <= 0 or magn_min.z >= 9999999:
        return False
    if accel_max.x <= accel_min.x or accel_max.x <= 0 or accel_min.x >= 9999999:
        return False
    if accel_max.y <= accel_min.y or accel_max.y <= 0 or accel_min.y >= 9999999:
        return False
    if accel_max.z <= accel_min.z or accel_max.z <= 0 or accel_min.z >= 9999999:
        return False


def check_ellipse_data():
    if (ellipsoid_coeff[3] ** 2 >= 4 * ellipsoid_coeff[0] * ellipsoid_coeff[2]) \
            or (ellipsoid_coeff[4] ** 2 >= 4 * ellipsoid_coeff[0] * ellipsoid_coeff[2]) \
            or (ellipsoid_coeff[4] ** 2 >= 4 * ellipsoid_coeff[0] * ellipsoid_coeff[2]):
        # must be true: D^2 < 4*A*B, E^2 < 4*A*C, F^2 < 4*B*C
        return False
    return True


def do_min_max_config():
    global gyro_max, gyro_min, accel_max, accel_min, magn_max, magn_min
    print("Move the IMU in each directiontoget min & max values, then press stosave the values")

    stdscr = curses.initscr()
    key = ''

    while 1:
        key = stdscr.getch()
        if key == 115 and check_min_max_data():
            save_calibration()
            print("min/max calibration saved")
            break

        poll_imu()
        if imu_data.gyroscope.x > gyro_max.x:
            gyro_max.x = imu_data.gyroscope.x
        if imu_data.gyroscope.y > gyro_max.y:
            gyro_max.y = imu_data.gyroscope.y
        if imu_data.gyroscope.z > gyro_max.z:
            gyro_max.z = imu_data.gyroscope.z

        if imu_data.magnetometer.x > magn_max.x:
            magn_max.x = imu_data.magnetometer.x
        if imu_data.magnetometer.y > magn_max.y:
            magn_max.y = imu_data.magnetometer.y
        if imu_data.magnetometer.z > magn_max.z:
            magn_max.z = imu_data.magnetometer.z

        if imu_data.accelerometer.x > accel_max.x:
            accel_max.x = imu_data.accelerometer.x
        if imu_data.accelerometer.y > accel_max.y:
            accel_max.y = imu_data.accelerometer.y
        if imu_data.accelerometer.z > accel_max.z:
            accel_max.z = imu_data.accelerometer.z

        if platform.system() == "Windows":
            os.system("cls")
        elif platform.system() is "Linux" or platform.system() is "Darwin":
            os.system("clear")

        print(
            "Gyroscope: " + str(gyro_min.x) + "to" + str(gyro_max.x) + "\t" + str(gyro_min.y) + "to" + str(
                gyro_max.y) + "\t" + str(gyro_min.z) + "to" + str(gyro_max.z) + "\n" +
            "Accelerometer: " + str(accel_min.x) + "to" + str(accel_max.x) + "\t" + str(accel_min.y) + "to" + str(
                accel_max.y) + "\t" + str(accel_min.z) + "to" + str(accel_max.z) + "\n" +
            "Magnetometer: " + str(magn_min.x) + "to" + str(magn_max.x) + "\t" + str(magn_min.y) + "to" + str(
                magn_max.y) + "\t" + str(magn_min.z) + "to" + str(magn_max.z) + "\n")
        time.sleep(1 / poll_rate)


# logger.debug("Starting min/max calibration!")
# do_min_max_config()
def test(screen):
    # logger.debug("Starting test loop")
    # curses.cbreak()
    screen.nodelay(True)
    while 1:
        key = screen.getch()
        root_logger.debug("Key Pressed: " + str(key))
        if key == 115:
            curses.endwin()
            break
        poll_imu()

        screen.clear()

        #        print(
        #            "Magnetometer: " + str(imu_data.magnetometer.x) + ", " + str(imu_data.magnetometer.y) + ", " + str(imu_data.magnetometer.z) + "\n"
        #            "Gyroscope: " + str(imu_data.gyroscope.x) + ", " + str(imu_data.gyroscope.y) + ", " + str(imu_data.gyroscope.z) + "\n"
        #            "Accelerometer: " + str(imu_data.accelerometer.x) + ", " + str(imu_data.accelerometer.y) + ", " + str(imu_data.accelerometer.z)
        #        )

        screen.addstr(0, 0, "Magnetometer: \t" + str(imu_data.magnetometer.x) + ",\t" + str(
            imu_data.magnetometer.y) + ",\t" + str(imu_data.magnetometer.z))
        screen.addstr(1, 0, "Gyroscope: \t" + str(imu_data.gyroscope.x) + ",\t" + str(imu_data.gyroscope.y) + ",\t" + str(
            imu_data.gyroscope.z))
        screen.addstr(2, 0, "Accelerometer: \t" + str(imu_data.accelerometer.x) + ",\t" + str(
            imu_data.accelerometer.y) + ",\t" + str(imu_data.accelerometer.z))

        time.sleep(1 / poll_rate)


curses.wrapper(test)
# test(curses.initscr())
