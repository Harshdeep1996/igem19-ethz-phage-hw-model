from __future__ import annotations

import threading
import time
import warnings

import numpy as np
from drivers.ESC import ESC
from drivers.WaterPump import WaterPump
from drivers.WaterTemperatureSensor import WaterTemperatureSensor
from simple_pid import PID


class ReactorTemperatureControl:

    def __init__(self,
                 id: int,
                 i2c_lock: threading.Lock = None,
                 one_wire_lock: threading.Lock = None,
                 target_temperature: float = 25.0,
                 enabled: bool = True,
                 verbose: bool = True):
        self.id = id
        self.water_pump = WaterPump(id=id,
                                    i2c_lock=i2c_lock)
        self.temperature_sensor = WaterTemperatureSensor(id=id,
                                                         one_wire_lock=one_wire_lock)
        self.output = ESC(id=id,
                          i2c_lock=i2c_lock)
        self.target_setpoint = target_temperature

        self.Kp = 80.0
        self.Ki = 0.2
        self.Kd = 10.0

        # instantiate PID controller
        self.pid = PID(Kp=self.Kp,
                       Ki=self.Ki,
                       Kd=self.Kd,
                       setpoint=target_temperature,
                       sample_time=1.0,  # 1.0 s
                       output_limits=(-100, 100),
                       auto_mode=True,
                       proportional_on_measurement=False)

        # initialize log arrays
        self.temp_log = list()
        self.kp_log = list()
        self.ki_log = list()
        self.kd_log = list()
        self.control_val_log = list()

        self.enabled = enabled
        if not self.enabled:
            self.output.stop()
        self.verbose = verbose

    def set_target_temperature(self,
                               temperature: float):
        self.target_setpoint = temperature
        self.pid.setpoint = self.target_setpoint

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False
        self.output.stop()

    def finalize(self):
        self.disable()

    def control_loop(self):

        if self.enabled:
            # get current temperature
            actual_temperature = self.temperature_sensor.get_temperature()

            print("current temperature: {}".format(actual_temperature))

            # anti wind-up procedure
            (kp, ki, kd) = self.pid.components
            if (kp + ki + kd) > 100 or (kp + ki + kd) < -100:
                self.pid.Ki = 0.0
            else:
                self.pid.Ki = self.Ki

            # compute new ouput from the PID according to the systems current value
            control_value = int(self.pid(actual_temperature))

            # do custom control_value heuristics: peltier elements should not change polarity too often
            # control_value = control_value if abs(control_value) > 10 else 0.0

            if self.verbose:
                print("control value: {}".format(control_value))
                print("pid components: {}".format(self.pid.components))

            # feed the PID output to the system
            self.output.set_value(control_value)

            # append log
            self.temp_log.append(actual_temperature)
            self.control_val_log.append(control_value)
            (kp, ki, kd) = self.pid.components
            self.kp_log.append(kp)
            self.ki_log.append(ki)
            self.kd_log.append(kd)
        else:
            warnings.warn("Control loop called, but device is disabled.")


if __name__ == "__main__":

    reactor0 = ReactorTemperatureControl(0, threading.Lock(), threading.Lock(), 39.0)

    # run control loop till keyboard interrupt (Ctrl + C)
    while True:
        try:
            reactor0.control_loop()
            time.sleep(1.0)
        except KeyboardInterrupt:
            print("Exiting...but first put device into a safe state...")
        finally:
            # save log files
            timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")
            np.savetxt(fname="log/{}_temperature.csv".format(timestamp), delimiter=",", X=reactor0.temp_log)
            np.savetxt(fname="log/{}_control_value.csv".format(timestamp), delimiter=",", X=reactor0.control_val_log)
            np.savetxt(fname="log/{}_kp.csv".format(timestamp), delimiter=",", X=reactor0.kp_log)
            np.savetxt(fname="log/{}_ki.csv".format(timestamp), delimiter=",", X=reactor0.ki_log)
            np.savetxt(fname="log/{}_kd.csv".format(timestamp), delimiter=",", X=reactor0.kd_log)
