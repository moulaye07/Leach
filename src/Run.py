#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from src import init
from src import election
from src import find
from src import join
import copy

def zeros(row, column):
    re_list = []
    for x in range(row):
        temp_list = [0 for _ in range(column)]
        if row == 1:
            re_list.extend(temp_list)
        else:
            re_list.append(temp_list)
    return re_list


class Simulation:

    def __init__(self, n=100,p=0.1,Eo=5.0,No=10, state=1):
        self.n = n  # Number of Nodes in the field
        self.p=p
        self.Eo=Eo
        self.No=No
        self.state=state

        # For set_init_param_for_nodes 
        self.dead_num = 0  # Number of dead nodes
        self.no_of_ch = 0  # counter for CHs
        self.flag_first_dead = 0  # flag_first_dead
        self.initEnergy = 0  # Initial Energy

        # Create sensor nodes, Set Parameters and Create Energy Model
        self.my_model = init.Model(self.n,self.p,self.Eo)  # Set Parameters self.Sensors and Network

        # Below will be of length(Max_rounds) so each element will store the total packets in each round
        # the length is rmax + 1 since we take one initialization round also.
        self.SRP = zeros(1, self.my_model.rmax + 1)  # number of sent routing packets
        self.RRP = zeros(1, self.my_model.rmax + 1)  # number of receive routing packets
        self.SDP = zeros(1, self.my_model.rmax + 1)  # number of sent data packets
        self.RDP = zeros(1, self.my_model.rmax + 1)  # number of receive data packets

        # For start_sim 
        # counter for bit transmitted to Bases Station and Cluster Heads
        self.srp = 0  # counter number of sent routing packets
        self.rrp = 0  # counter number of receive routing packets
        self.sdp = 0  # counter number of sent data packets to sink
        self.rdp = 0  # counter number of receive data packets by sink

        # For initialization_main_loop 
        self.dead_num = []
        self.packets_to_base_station = 0
        self.first_dead_in = -1
        
        # For statistics 
        self.alive = self.n

        self.sum_dead_nodes = zeros(1, self.my_model.rmax + 1)
        self.ch_per_round = zeros(1, self.my_model.rmax + 1)

        # all sensors should be alive in start
        self.alive_sensors = zeros(1, self.my_model.rmax + 1)
        self.alive_sensors[0] = self.n

        self.sum_energy_left_all_nodes = zeros(1, self.my_model.rmax + 1)
        self.avg_energy_All_sensor = zeros(1, self.my_model.rmax + 1)
        self.consumed_energy = zeros(1, self.my_model.rmax + 1)
        self.Enheraf = zeros(1, self.my_model.rmax + 1)


    def start(self):

        # Create Sensors 
        self.__create_sen()

        # Start Simulation 
        self.__start_simulation()

        # Main loop program 
        noeuds,model,tour = self.__main_loop()

        return self.n,self.my_model,self.alive_sensors,self.sum_energy_left_all_nodes,noeuds,model,tour
        # END of simulation 
        

    def __check_dead_num(self, round_number):
        # if sensor is dead
        for sensor in self.Sensors:
            if sensor.E <= 0 and sensor not in self.dead_num:
                sensor.df = 1
                self.dead_num.append(sensor)

        # flag it as dead
        if len(self.dead_num) > 0 and self.flag_first_dead == 0:
            # Save the period in which the first node died
            self.first_dead_in = round_number
            self.flag_first_dead = 1

    def __create_sen(self):

        # Create a random scenario & Load sensor Location
        # configure sensors
        self.Sensors = init.create_sensors(self.my_model)

        for sensor in self.Sensors[:-1]:
            self.initEnergy += sensor.E

        # We will have full energy in start
        self.sum_energy_left_all_nodes[0] = self.initEnergy
        self.avg_energy_All_sensor[0] = self.initEnergy / self.n


    def __start_simulation(self):

        # Sink broadcast 'Hello' message to all nodes 
        self.sender = [self.n]  # List of senders, for start_sim, sink will send hello packet to all
        self.receivers = [_ for _ in range(self.n)]  # List of senders, for start_sim, All nodes will receive from sink

        self.srp, self.rrp, self.sdp, self.rdp = find.start(
            self.Sensors, self.my_model, self.sender, self.receivers, self.srp, self.rrp, self.sdp, self.rdp,
            packet_type='Hello'
        )

        
        # Save metrics, Round 0 is initialization phase where all nodes send routing packets (hello) to Sink as above
        self.SRP[0] = self.srp
        self.RRP[0] = self.rrp
        self.SDP[0] = self.sdp
        self.RDP[0] = self.rdp


    def __main_loop(self):

        for round_number in range(1, self.my_model.rmax + 1):

            # Initialization 
            self.srp, self.rrp, self.sdp, self.rdp = init.reset(self.Sensors, self.my_model, round_number)
 
            # cluster head election 
            self.__cluster_head_selection_phase(round_number)
            self.no_of_ch = len(self.list_CH)  # Number of CH in per period

            if(round_number==self.No):                
                noeuds,model,tour = copy.deepcopy(self.Sensors),copy.deepcopy(self.my_model),round_number
                
            # steady-state phase 
            self.__steady_state_phase()

            # if sensor is dead
            self.__check_dead_num(round_number)

            # STATISTICS 
            self.__statistics(round_number)

            # if all nodes are dead or only sink is left, exit
            if len(self.dead_num) >= self.n:
                self.lastPeriod = round_number
                break
        
        return noeuds,model,tour

    def __cluster_head_selection_phase(self, round_number):

        # Selection Candidate Cluster Head Based on LEACH Set-up Phase
        # self.list_CH stores the id of all CH in current round
        self.list_CH = election.start(self.Sensors, self.my_model, round_number, self.state)
        self.no_of_ch = len(self.list_CH)

        # Broadcasting CHs to All Sensors that are in Radio Range of CH
        self.__broadcast_cluster_head()

        # Sensors join to nearest CH 
        # updates dist2ch & MCH in node
        join.start(self.Sensors, self.my_model, self.list_CH)

    def __broadcast_cluster_head(self):

        # Broadcasting CH x to All Sensors that are in Radio Rage of x. (dont broadcast to sink)
        # Doing this for all CH
        for ch_id in self.list_CH:
            self.receivers: list = find.findReceivers(self.Sensors, self.my_model, sender=ch_id,
                                                      sender_rr=self.Sensors[ch_id].RR)

            # we require the sender parameter of sendReceivePackets.start to be a list.
            self.srp, self.rrp, self.sdp, self.rdp = find.start(
                self.Sensors, self.my_model, [ch_id], self.receivers, self.srp, self.rrp, self.sdp, self.rdp,
                packet_type='Hello'
            )


    def __steady_state_phase(self):

        for i in range(self.my_model.NumPacket):  # Number of Packets to be sent in steady-state phase

            # All sensor send data packet to CH 
            for receiver in self.list_CH:
                sender = find.findSenders(self.Sensors, receiver)

                self.srp, self.rrp, self.sdp, self.rdp = find.start(
                    self.Sensors, self.my_model, sender, [receiver], self.srp, self.rrp, self.sdp, self.rdp,
                    packet_type='Data'
                )

        # send Data packet directly from nodes(that aren't in any cluster) to Sink 
        for sender in self.Sensors:
            # if the node has sink as its CH but it's not sink itself and the node is not dead
            if sender.MCH == self.n and sender.id != self.n and sender.E > 0:
                self.receivers = [self.n]  # Sink
                sender = [sender.id]

                self.srp, self.rrp, self.sdp, self.rdp = find.start(
                    self.Sensors, self.my_model, sender, self.receivers, self.srp, self.rrp, self.sdp, self.rdp,
                    packet_type='Data'
                )

        # Send Data packet from CH to Sink after Data aggregation 
        for sender in self.list_CH:
            self.receivers = [self.n]  # Sink

            self.srp, self.rrp, self.sdp, self.rdp = find.start(
                self.Sensors, self.my_model, [sender], self.receivers, self.srp, self.rrp, self.sdp, self.rdp,
                packet_type='Data'
            )

    def __statistics(self, round_number):

        self.sum_dead_nodes[round_number] = len(self.dead_num)
        self.ch_per_round[round_number] = self.no_of_ch
        self.SRP[round_number] = self.srp
        self.RRP[round_number] = self.rrp
        self.SDP[round_number] = self.sdp
        self.RDP[round_number] = self.rdp

        self.alive = 0
        sum_energy_left_all_nodes_in_curr_round = 0
        for sensor in self.Sensors[:-1]:
            if sensor.E > 0:
                self.alive += 1
                sum_energy_left_all_nodes_in_curr_round += sensor.E

        self.alive_sensors[round_number] = self.alive
        self.sum_energy_left_all_nodes[round_number] = sum_energy_left_all_nodes_in_curr_round
        if self.alive:
            self.avg_energy_All_sensor[round_number] = sum_energy_left_all_nodes_in_curr_round / self.alive
        else:
            self.avg_energy_All_sensor[round_number] = 0
        self.consumed_energy[round_number] = (self.initEnergy - self.sum_energy_left_all_nodes[round_number]) / self.n

        En = 0
        for sensor in self.Sensors:
            if sensor.E > 0:
                En += pow(sensor.E - self.avg_energy_All_sensor[round_number], 2)

        if self.alive:
            self.Enheraf[round_number] = En / self.alive
        else:
            self.Enheraf[round_number] = 0
        
