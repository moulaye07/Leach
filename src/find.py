#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from src.init import *

def zeros(row, column):
    re_list = []
    for x in range(row):
        temp_list = [float(0) for _ in range(column)]
        if row == 1:
            re_list.extend(temp_list)
        else:
            re_list.append(temp_list)

    return re_list

def findReceivers(sensors: list[Sensor], my_model: Model, sender, sender_rr):
    receiver = []
    # Calculate Distance All Sensor With Sender
    n = my_model.n
    distance = zeros(1, n)

    for i, sensor in enumerate(sensors[:-1]):
        distance[i] = sqrt(
            pow(sensor.xd - sensors[sender].xd, 2) + pow(sensor.yd - sensors[sender].yd, 2)
        )
        
        # node should be in RR
        if distance[i] <= sender_rr and sender != sensor.id:
            receiver.append(sensor.id)

    return receiver

def findSenders(Sensors: list[Sensor], receiver):
    sender = []

    for sensor in Sensors[:-1]:
        if sensor.MCH == receiver and sensor.id != receiver:
            sender.append(sensor.id)

    return sender

def send_rec(sensors: list[Sensor], sender, sap):
    if sensors[sender].E > 0:
        sap += 1
    else:
        sensors[sender].df = 1

    return sap

def start(sensors: list[Sensor], my_model: Model, senders: list, receivers: list, srp, rrp, sdp, rdp, packet_type: str):
    sent_packets = 0  # Number of sent packets
    rec_packets = 0  # Number of received packets

    PacketSize = my_model.hello_packet_len if packet_type == 'Hello' else my_model.data_packet_len

    # Energy dissipated from Sensors for Sending a packet
    # Each sender will send to each receiver
    for sender in senders:
        for receiver in receivers:
            distance = sqrt(
                pow(sensors[sender].xd - sensors[receiver].xd, 2) +
                pow(sensors[sender].yd - sensors[receiver].yd, 2)
            )

            if distance > my_model.do:
                sensors[sender].E -= my_model.ETX * PacketSize + my_model.Emp * PacketSize * pow(distance, 4)
                sent_packets = send_rec(sensors, sender, sent_packets)

            else:
                sensors[sender].E -= my_model.ETX * PacketSize + my_model.Efs * PacketSize * pow(distance, 2)
                sent_packets = send_rec(sensors, sender, sent_packets)

    for receiver in receivers:
        sensors[receiver].E -= (my_model.ERX + my_model.EDA) * PacketSize

    # for receivers
    # Energy dissipated from receivers for Receiving a packet, if the sender died during transmission,
    # the energy of receiver will be wasted but it will not receive any packet
    for sender in senders:
        for receiver in receivers:
            if sensors[receiver].E > 0 and sensors[sender].E > 0:
                # Received a Packet
                rec_packets += 1
            elif sensors[receiver].E < 0:
                sensors[receiver].df = 1

    if packet_type == 'Hello':
        srp += sent_packets
        rrp += rec_packets
    elif packet_type == 'Data':
        sdp += sent_packets
        rdp += rec_packets

    return srp, rrp, sdp, rdp
