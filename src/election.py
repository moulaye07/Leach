#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from src.init import *

def zeros(row, column):
    re_list = []
    for x in range(row):
        temp_list = [0 for _ in range(column)]
        if row == 1:
            re_list.extend(temp_list)
        else:
            re_list.append(temp_list)

    return re_list

def start(sensors: list[Sensor], my_model, round_number: int, state: int):
    CH = []
    n = my_model.n

    for sensor in sensors[:-1]:

        if sensor.E > 0 and sensor.G <= 0:
            a=sensor.E/sensor.Eo
            b=round(sensor.rs/(1/my_model.p))
            c=a+b*(1-a)

            # Election of Cluster Heads
            temp_rand = random.uniform(0, 1)

            if(state==1):
                value = (my_model.p / (1 - my_model.p * (round_number % (1 / my_model.p))))*c
            if(state==2):
                value = (my_model.p / (1 - my_model.p * (round_number % (1 / my_model.p))))*a
            if(state==3):
                value = (my_model.p / (1 - my_model.p * (round_number % (1 / my_model.p))))

            if temp_rand <= value:
                CH.append(sensor.id)
                sensor.type = 'C'
                sensor.rs=0
                sensor.G = round(1 / my_model.p) - 1
            else:
                sensor.rs=sensor.rs+1

    return CH
