#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2020 ewhite42.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

"""
This block provides necessary parameters to the
ATA control block to run a sequence of simple track
scans.
"""

from gnuradio import gr
import pmt

class trackscan(gr.sync_block):

    ''' The track scan block sends commands to the control
        block in order to point a set of ATA antennas '''

    def __init__(self, cfreq, ant_list, coord_type):
        gr.sync_block.__init__(self,
                               name="trackscan",
                               in_sig=None,
                               out_sig=None)

        self.message_port_register_out(pmt.intern("command"))
        self.message_port_register_in(pmt.intern("msg_in"))
        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)

        #set up dictionary of observing info which will be sent through
        #the message port

        obs_key = pmt.intern("obs_type")
        obs_val = pmt.intern("track")

        ant_key = pmt.intern("antennas_list")
        ant_val = pmt.intern(ant_list)

        freq_key = pmt.intern("freq")
        freq_val = pmt.from_double(cfreq)

        coord_key = pmt.intern("coord_type")
        coord_val = pmt.intern(coord_type)

        command = pmt.make_dict()
        command = pmt.dict_add(command, ant_key, ant_val)
        command = pmt.dict_add(command, freq_key, freq_val)
        command = pmt.dict_add(command, obs_key, obs_val)
        command = pmt.dict_add(command, coord_key, coord_val)

        self.command = command

    def handle_msg(self, msg):

        ''' This function handles messages from a
        text entry box like QT GUI Message Edit. '''

        self.command = pmt.dict_delete(self.command, pmt.intern("source_id"))
        self.command = pmt.dict_delete(self.command, pmt.intern("ra"))
        self.command = pmt.dict_delete(self.command, pmt.intern("dec"))
        self.command = pmt.dict_delete(self.command, pmt.intern("az"))
        self.command = pmt.dict_delete(self.command, pmt.intern("el"))

        key = pmt.car(msg)
        val = pmt.cdr(msg)

        str_key = pmt.symbol_to_string(key)
        
        if str_key == "source_id":
            self.command = pmt.dict_add(self.command, key, val)
            self.message_port_pub(pmt.intern("command"), self.command)

        elif str_key == "azel":
            azel_pair = pmt.symbol_to_string(val).split(',')
            az = pmt.from_double(float(azel_pair[0].strip()))
            el = pmt.from_double(float(azel_pair[1].strip()))

            self.command = pmt.dict_add(self.command, pmt.intern("az"), az)
            self.command = pmt.dict_add(self.command, pmt.intern("el"), el)

            self.message_port_pub(pmt.intern("command"), self.command)

        elif str_key == "radec":
            radec_pair = pmt.symbol_to_string(val).split(',')
            ra = pmt.from_double(float(radec_pair[0].strip()))
            dec = pmt.from_double(float(radec_pair[1].strip()))

            self.command = pmt.dict_add(self.command, pmt.intern("ra"), ra)
            self.command = pmt.dict_add(self.command, pmt.intern("dec"), dec)

            self.message_port_pub(pmt.intern("command"), self.command)

        else: 
            print("Wrong value in left-hand space of Message Edit box.\n"\
                  "Must be either source_id, radec, or azel. Try again.\n")


    def set_source(self, src):

        ''' This function sets the source's
            identifier string '''

        src_key = pmt.intern("source_id")
        src_val = pmt.intern(src)
        self.command = pmt.dict_add(self.command, src_key, src_val)

    def set_src_radec(self, ra, dec):

        ''' This function sets the target source's
            right ascension and declination '''

        ra_key = pmt.intern("ra")
        ra_val = pmt.from_double(ra)

        dec_key = pmt.intern("dec")
        dec_val = pmt.from_double(dec)

        self.command = pmt.dict_add(self.command, ra_key, ra_val)
        self.command = pmt.dict_add(self.command, dec_key, dec_val)

    def set_src_azel(self, az, el):

        ''' This function sets the target source's
            azimuth and elevation '''

        az_key = pmt.intern("az")
        az_val = pmt.from_double(az)

        el_key = pmt.intern("el")
        el_val = pmt.from_double(el)

        self.command = pmt.dict_add(self.command, az_key, az_val)
        self.command = pmt.dict_add(self.command, el_key, el_val)

    def stop(self):
        return True

    def start(self):
        ''' publish the observation info to the output message port '''

        self.message_port_pub(pmt.intern("command"), self.command)
        return super().start()
