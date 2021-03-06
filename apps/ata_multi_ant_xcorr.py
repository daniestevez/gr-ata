#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: ATA Multi Antenna XEngine
# Author: ghostop14
# GNU Radio version: 3.8.2.0

from datetime import datetime
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import ata
import clenabled
import os
import numa

class ata_12ant_xcorr(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "ATA Multi-Antenna XEngine")

        ##################################################
        # Variables
        ##################################################
        self.now = now = datetime.now()
        self.starting_channel = starting_channel = clparam_starting_channel
        self.num_channels = num_channels = clparam_num_channels
        self.file_timestamp = file_timestamp = now.strftime("%Y_%m_%d_%H_%M")
        self.output_file = output_file = clparam_output_directory + '/' + clparam_output_prefix + '_' + file_timestamp
        self.ending_channel = ending_channel = starting_channel+num_channels-1

        ##################################################
        # Blocks
        ##################################################
        self.clenabled_clXEngine_0 = clenabled.clXEngine(1,2,0,0,False, 6, 2, clparam_num_antennas, 1, starting_channel, num_channels, 
                                                                                            clparam_integration_frames, clparam_antenna_list, True,output_file,0,True, 
                                                                                            clparam_snap_sync, clparam_object_name, clparam_starting_chan_freq, clparam_channel_width, 
                                                                                            clparam_no_output,  clparam_cpu_integration)
        
        if clparam_enable_affinity:
            # So with affinity here, we're just trying to ensure NUMA doesn't move us off
            # where our memory was allocated.  So we're going to try to be smart about 
            # allocating here.  We'll set affinity to all of the cores on each processor till
            # we've "recommended" a full set.
            num_nodes=numa.get_max_node() + 1
            
            # core_pairs = []
            cpu_core_list = []
            cores_per_cpu = 0
            cores_per_cpu_2 = 0
            
            for cur_node in range(0, num_nodes):
                cpu_to_node=list(numa.node_to_cpus(cur_node))
                cpu_core_list.append(cpu_to_node)
                if cores_per_cpu == 0:
                    cores_per_cpu = len(cpu_to_node)
                    cores_per_cpu_2 = cores_per_cpu // 2
                print("CPU" + str(cur_node) + " has " + str(len(cpu_to_node)) + " cores: " + str(cpu_to_node))
                #i = 0
                
                #for cur_cpu in cpu_to_node:
                #   if i % 2 == 0:
                #        cpu_pair = [cur_cpu]
                #    else:
                #        cpu_pair.append(cur_cpu)
                #        core_pairs.append(cpu_pair)
                #        
                #    i += 1
            
            #print("Setting xEngine affinity to cores " + str(core_pairs[0]))
            #self.clenabled_clXEngine_0.set_processor_affinity(core_pairs[0])
            #core_pairs = core_pairs[1:]
            # or to all cores on CPU0
            if num_nodes > 1:
                self.clenabled_clXEngine_0.set_processor_affinity(cpu_core_list[0])

        self.antenna_list = []
        for i in range(0, clparam_num_antennas):
            cur_port = clparam_base_port +i
            new_ant = ata.snap_source(cur_port, 1, True, False, False,starting_channel,ending_channel,1, '', False, True, '224.1.1.10',  False, clparam_bind_ip)
            # if clparam_enable_affinity and len(core_pairs) > 0:
            #    print("Setting SNAP UDP " + str(clparam_base_port+i) + " to affinity to cores " + str(core_pairs[0]))
            #    new_ant.set_processor_affinity(core_pairs[0])
            #    core_pairs = core_pairs[1:]
                
            # or:
            if clparam_enable_affinity and num_nodes > 1:
                cpu2 = cores_per_cpu_2 -2 + cores_per_cpu_2
                if i < cores_per_cpu_2 -2:
                    # Subtract 2 for the xengine on the first node.
                    print("Setting affinity for UDP " + str(cur_port) + " to CPU0")
                    new_ant.set_processor_affinity(cpu_core_list[0])
                elif i < cpu2:
                    print("Setting affinity for UDP " + str(cur_port) + " to CPU1")
                    new_ant.set_processor_affinity(cpu_core_list[1])
                else:
                    #   just balance
                    index = i % 2
                    print("Setting affinity for UDP " + str(cur_port) + " to CPU" + str(index))
                    new_ant.set_processor_affinity(cpu_core_list[index])
                
            ##################################################
            # Connections
            ##################################################
            self.msg_connect((self.clenabled_clXEngine_0, 'sync'), (new_ant, 'sync'))
            self.connect((new_ant, 0), (self.clenabled_clXEngine_0, i))
            self.antenna_list.append(new_ant)

    def get_now(self):
        return self.now

    def set_now(self, now):
        self.now = now

    def get_starting_channel(self):
        return self.starting_channel

    def set_starting_channel(self, starting_channel):
        self.starting_channel = starting_channel
        self.set_ending_channel(self.starting_channel+self.num_channels-1)

    def get_num_channels(self):
        return self.num_channels

    def set_num_channels(self, num_channels):
        self.num_channels = num_channels
        self.set_ending_channel(self.starting_channel+self.num_channels-1)

    def get_file_timestamp(self):
        return self.file_timestamp

    def set_file_timestamp(self, file_timestamp):
        self.file_timestamp = file_timestamp
        self.set_output_file('/home/mpiscopo/xengine_output/staging/ata_' + self.file_timestamp)

    def get_output_file(self):
        return self.output_file

    def set_output_file(self, output_file):
        self.output_file = output_file

    def get_ending_channel(self):
        return self.ending_channel

    def set_ending_channel(self, ending_channel):
        self.ending_channel = ending_channel

def main(top_block_cls=ata_12ant_xcorr, options=None):
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print("Error: failed to enable real-time scheduling.")
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    tb.wait()


if __name__ == '__main__':
    parser = ArgumentParser(description='ATA Multi-Antenna X-Engine')
    parser.add_argument('--snap-sync', '-s', type=int, default='ata', help="The unix timestamp when the SNAPs started and were synchronized", required=True)
    parser.add_argument('--object-name', '-o', type=str, help="Name of viewing object.  E.g. 3C84 or 3C461 for CasA", required=True)
    parser.add_argument('--antenna-list', '-a', type=str, help="Comma-separated list of antennas used (no spaces).  This will be used to also define num_antennas.", required=True)
    parser.add_argument('--num-channels', '-c', type=int, help="Number of channels being received from SNAP (should be a multiple of 256)", required=True)
    parser.add_argument('--starting-channel', '-t', type=int, help="Starting channel number being received from the SNAP", required=True)
    parser.add_argument('--starting-chan-freq', '-f', type=float, help="Center frequency (in Hz) of the first channel (e.g. for 3 GHz sky freq and 256 channels, first channel would be 2968000000.0", required=True)
    parser.add_argument('--channel-width', '-w', type=float, default=250000.0,  help="[Optional] Channel width.  For now for the ATA, this number should be 250000.0", required=False)
    parser.add_argument('--integration-frames', '-i', type=int, help="Number of Frames to integrate in the correlator.  Note this should be a multiple of 16 to optimize the way the SNAP outputs frames (e.g. 10000, 20000, or 24000 but not 25000). Each frame is 4 microseconds so an integration of 10000 equates to a time of 0.04 seconds.", required=True)
    parser.add_argument('--cpu-integration',  type=int, default=0, help="If set to a value > 1, each GPU correlated frame will be further accumulated in a CPU buffer.  This allows for integrations beyond the amount of memory available on a GPU.  This figure is a multiplier, so if integration-time=20000, and cpu-integration=2, total integration time will be 40000", required=False)
    parser.add_argument('--output-directory', '-d', type=str, help="Directory path to where correlation outputs should be written. If set to the word 'none', no output will be generated (useful for performance testing).", required=True)
    parser.add_argument('--output-prefix', '-p', type=str, default='ata', help="If specified, this prefix will be prepended to the output files.  Otherwise 'ata' will be used.", required=False)
    parser.add_argument('--base-port', '-b', type=int, default=10000, help="The first UDP port number for the listeners.  The first antenna will be assigned to this port and each subsequent antenna to the next number up (e.g. 10000, 10001, 10002,...)", required=False)
    parser.add_argument('--no-output', '-n', help="Used for performance tuning.  Disables disk IO.", action='store_true', required=False)
    parser.add_argument('--enable-affinity', '-e', help="Enable CPU affiniity", action='store_true', required=False)
    parser.add_argument('--bind-ip', type=str, default='', help="Specific IP to bind to.  Default is 0.0.0.0 (all)", required=False)

    args = parser.parse_args()
    clparam_snap_sync = args.snap_sync
    clparam_object_name = args.object_name
    clparam_antenna_list = args.antenna_list.replace(' ', '').split(',')
    clparam_num_antennas = len(clparam_antenna_list)
    clparam_starting_channel = args.starting_channel
    clparam_starting_chan_freq = args.starting_chan_freq
    clparam_num_channels = args.num_channels
    clparam_integration_frames = args.integration_frames
    clparam_cpu_integration = args.cpu_integration
    clparam_no_output = args.no_output
    clparam_output_directory = args.output_directory
    clparam_output_prefix = args.output_prefix
    clparam_channel_width = args.channel_width
    clparam_base_port = args.base_port
    clparam_bind_ip = args.bind_ip
    
    clparam_enable_affinity = args.enable_affinity
    
    if clparam_num_antennas < 2:
        print("ERROR: Please provide at least 2 antennas")
        exit(1)
        
    if (clparam_num_channels % 256) > 0 or clparam_num_channels < 256 or clparam_num_channels > 4096:
        print("ERROR: The number of channels must be a multiple of 256 from 256 to 4096")
        exit(1)
        
    if (clparam_integration_frames % 16) > 0:
        print("ERROR: The number of integration frames should be a multiple of 16 to optimize the SNAP->xengine pipeline")
        exit(1)

    if not os.path.exists(clparam_output_directory):
        print("ERROR: The specified output directory does not exist.")
        exit(1)
    
    main()
