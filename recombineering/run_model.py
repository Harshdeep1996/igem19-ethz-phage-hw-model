#!/usr/bin/env python3
# encoding: utf-8

"""
    Copyright (C) 2019-2020  Andreas Kuster

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = "Andreas Kuster"
__copyright__ = "Copyright 2019-2020"
__license__ = "GPL"

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import odeint

from host import Host


# simulation time and resolution of samples
xs = np.linspace(0, 1200, 100)

f= 0.02

#Reactor A
# lb influx profile of reactor A
def in_a_lb(t):
    """
    :param t: time t
    :return: lb influx to reactor a at time t
    """
    return f
    
# biomass outflux profile of reactor A
def out_a(t):
    """
    :param t: time t
    :return: biomass outflux of reactor a at time t
    """
    return f
    
# temperature profile of reactor A
def temperature_a(t):
    """
    :param t: time t
    :return: temperature at time t
    """
    return 39.7


def temperature_dependency_new_host(x):
    """
    :param x: temperature
    :return: growth rate factor
    """
    mu = 39.7
    sigma_l = 120.0
    sigma_r = 10.0
    if x < mu:
        return np.exp(-0.5*(np.square(x-mu)/sigma_l)) # gaussian l: ~(39.7, 120)
    else:
        return np.exp(-0.5*(np.square(x-mu)/sigma_r)) # gaussian r: ~(39.7, 10)


new_host = Host( 
    c0 = 10**5,
    g_max = 0.036, #lit: 0.012
    yield_coeff = 0.000000000001,
    half_sat = 0.00000125,
    death_rate = 0.00005,
    t_dep = temperature_dependency_new_host,
)


s0 = 0.0005 #stock concentration of nutrient (g/mL)#0.0000025

# define system of differential equations
def dXa_dt(X, t):
    [c_host_a, c_nutr_a] = X
    return np.array([
        0 if c_host_a <= 0 else new_host.per_cell_growth_rate(c_nutr_a,temperature_a(t))*c_host_a - out_a(t)*c_host_a - new_host.death_rate*c_host_a,  # new host concentration reactor A
        0 if c_nutr_a <= 0 else - new_host.yield_coeff*new_host.per_cell_growth_rate(c_nutr_a,temperature_a(t))*c_host_a
        + s0*in_a_lb(t) - c_nutr_a*out_a(t)  # nutrient concentration reactor A
    ])


ys = odeint(dXa_dt, [
    new_host.c0,  # initial new host concentration [cell/mL]
    s0  # initial nutrient concentration [g/mL]
], xs)


c_new_host_a = [y[0] for y in ys]
c_nutrient_a = [y[1] for y in ys]
print(c_new_host_a)
print(xs)

def predict_conc(ini_host, ini_nutr, host, temperature, in_a, out_a, tao):
    """
    :param : initial cond., param., ...
    :return: concentration after tao minutes
    """

    def dX_dt(X, t):
        [c_host_a, c_nutr_a] = X
        return np.array([
                0 if c_host_a <= 0 else host.per_cell_growth_rate(c_nutr_a,temperature)*c_host_a - out_a*c_host_a - host.death_rate*c_host_a,  # new host concentration reactor A
                0 if c_nutr_a <= 0 else - host.yield_coeff*host.per_cell_growth_rate(c_nutr_a,temperature)*c_host_a
                + s0*in_a - c_nutr_a*out_a  # nutrient concentration reactor A
        ])
    steps = 100
    time = np.linspace(0, tao, steps)
    y = odeint(dX_dt, [
        ini_host,  # initial new host concentration [cell/mL]
        ini_nutr  # initial nutrient concentration [g/mL]
    ], time)
    print(y)

    return y[steps-1][0]

tao = 20
temperature = 39.6
flux = 0.007
print(predict_conc(new_host.c0, s0, new_host, temperature, flux, flux, tao))


plt.figure(figsize=(16, 16))


plt.subplot(3, 3, 1)
plt.plot(xs, [temperature_a(t) for t in xs], label="reactor A")
plt.xlabel('time [min]')
plt.ylabel('temperature [°C]')
plt.title('Temperature over Time')
plt.legend()


plt.subplot(3, 3, 2)
plt.plot(xs, [in_a_lb(t) for t in xs], label="reactor A")
plt.xlabel('time [min]')
plt.ylabel('LB influx [ml]')
plt.title('LB influx over Time')
plt.legend()


plt.subplot(3, 3, 3)
plt.plot(xs, [out_a(t) for t in xs], label="reactor A")
plt.xlabel('time [min]')
plt.ylabel('biomass outflux [ml]')
plt.title('Biomass Outflux over Time')
plt.legend()


plt.subplot(3, 3, 4)
plt.plot(xs, [y[0] for y in ys], label="new host")
plt.xlabel('time [min]')
plt.ylabel('concentration [#bacteria/mL]')
plt.title('Host Concentration over Time')
plt.legend()


plt.subplot(3, 3, 5)
plt.plot(xs, [new_host.per_cell_growth_rate(c_nutrient_a[x],temperature_a(x)) for x in np.arange(0, len(xs))], label="new host")
plt.xlabel('time [min]')
plt.ylabel('rate')
plt.title('Actual Growth Rate over Time')
plt.legend()


plt.subplot(3, 3, 6)
plt.plot(xs, c_nutrient_a, label="reactor A")
plt.xlabel('time [min]')
plt.ylabel('nutrient concentration [g/mL]')
plt.title('Nutrient Concentration over Time')
plt.legend()


plt.subplot(3, 3, 7)
nutrient_x = np.linspace(0, 0.0001)
plt.plot(nutrient_x, [new_host.per_cell_growth_rate(x,37) for x in nutrient_x], label="new host")
plt.ylim([0,0.015])
plt.xlim([0,0.000002])
plt.xlabel('nutrient concentration [g/mL]')
plt.ylabel('per cell growth rate')
plt.title('Growth Rate at low conc. of nutrient')
plt.legend()


plt.subplot(3, 3, 8)
nutrient_x = np.linspace(0, 0.0001)
plt.plot(nutrient_x, [new_host.per_cell_growth_rate(x,37) for x in nutrient_x])
plt.ylim([0,0.04])
plt.xlabel('nutrient concentration [g/mL]')
plt.ylabel('per cell growth rate')
plt.title('Growth Rate (nutrient)')
plt.legend()


plt.subplot(3, 3, 9)
nutrient_x = np.linspace(0.1, 1)
lin = [new_host.per_cell_growth_rate(x,37) for x in nutrient_x]
plt.plot(nutrient_x, lin, label="new host")
plt.ylim([0,0.04])
plt.xlabel('nutrient concentration [g/mL]')
plt.ylabel('per cell growth rate')
plt.title('Growth Rate at high conc. of nutrient')
plt.legend()

plt.subplots_adjust(wspace=0.4, hspace=0.4)

plt.show()
