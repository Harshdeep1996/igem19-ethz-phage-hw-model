import os
import time


class DS18B20:

    @staticmethod
    def init():
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')

    @staticmethod
    def raw_sensor_data(socket_path: str) -> str:
        with open(socket_path, 'r') as socket:
            lines = socket.readlines()
        return lines

    @staticmethod
    def extract_temperature(raw_sensor_data: str) -> float:
        position = raw_sensor_data[1].find('t=')
        if position != -1:
            temperature = raw_sensor_data[1].strip()[position + 2:]
        return float(temperature) / 1000.0

    @staticmethod
    def get_temperature(sensor_mac_addr: str) -> float:
        return DS18B20.extract_temperature(
            DS18B20.raw_sensor_data("/sys/bus/w1/devices/" + sensor_mac_addr + "/w1_slave"))


if __name__ == "__main__":
    while True:
        for sensor in [("Reactor0:", "28-0114536b03aa"),
                       ("Reactor1:", "28-80000026f3d8"),
                       ("Reactor2:", "28-0114534081aa")]:
            print("{}: {}°C".format(sensor[0], DS18B20.get_temperature(sensor[1])))
        time.sleep(10)

# credits: https://thepihut.com/blogs/raspberry-pi-tutorials/ds18b20-one-wire-digital-temperature-sensor-and-the-raspberry-pi
