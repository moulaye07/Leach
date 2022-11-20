#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from src.init import *
import matplotlib.pyplot as plt

def start(Sensors: list[Sensor], myModel: Model, round_number):

    n = myModel.n
    fig, axis = plt.subplots()
    axis.set_xlim(left=0, right=myModel.x)
    axis.set_ylim(bottom=0, top=myModel.y)

    n_flag = True
    c_flag = True
    d_flag = True
    for sensor in Sensors:
        if sensor.E > 0:
            if sensor.type == 'N':
                if n_flag:
                    axis.scatter([sensor.xd], [sensor.yd], c='k', edgecolors='k', label='Nodes')
                    n_flag = False
                else:
                    axis.scatter([sensor.xd], [sensor.yd], c='k', edgecolors='k')
            elif sensor.type == 'C':
                if c_flag:
                    axis.scatter([sensor.xd], [sensor.yd], c='r', edgecolors='k', label='Cluster Head')
                    c_flag = False
                else:
                    axis.scatter([sensor.xd], [sensor.yd], c='r', edgecolors='k')
        else:
            if d_flag:
                axis.scatter([sensor.xd], [sensor.yd], c='w', edgecolors='k', label='Dead')
                d_flag = False
            else:
                axis.scatter([sensor.xd], [sensor.yd], c='w', edgecolors='k')

    axis.scatter([Sensors[n].xd], [Sensors[n].yd], s=80, c='b', edgecolors='k', label="Sink")
    return axis
