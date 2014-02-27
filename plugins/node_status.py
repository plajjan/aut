#==============================================================
# node_status.py  - Plugin for checking Node states.
#
# Copyright (c)  2013, Cisco Systems
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice, this list of conditions
# and the following disclaimer in the documentation and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ==============================================================================

import lib.global_constants
from lib.global_constants import *
from time import sleep
import os 

class IPlugin(object):
    """
    ASR9k Pre-upgrade check
    This pluging checks states of all nodes
    """
    plugin_name = "Node Status Check.."
    plugin_type = PRE_UPGRADE_AND_POST_UPGRADE
    plugin_version     = "1.0.0"
 
    def get_standby_node(self, cmd_op):
        list=[]
        str=""
        srp=""
        standby=""
        for line in cmd_op:
            if line.find("Standby") != -1:
               standby=line
        for c in standby:
            srp=srp+c
            if c == " ":
               break
        return srp

 
 
    def start(self, **kwargs):
        """
        """
        host = kwargs['session']
        print ""
        print "Checking states of all nodes..."
        print "Node should be in one of the following state:"
        print "     a) IOS XR RUN"
        print "     b) PRESENT"
        print "     c) UNPOWERED"
        print "     d) READY"
        print "     e) FAILED"
        print "     f) OK"
        print "     g) NOT ALLOW ONLIN"
        print "     h) DISABLED"

        # Get 'show platform status o/p
        try :
            host.expect_exact("#", timeout=30)
        except :
            pass

        host.sendline("admin show platform")
        try :
            status = host.expect_exact( [INVALID_INPUT, MORE, PROMPT,"#", EOF], timeout=tout_cmd)
        except :
            print bcolors.WARNING+"Command: Timed out, before considering this as failure"
            print "Please check following log file for details\n%s"%(host.logfile)+bcolors.ENDC
            return -1;

        # Parse string based on newline
        newstring = host.before.split("\n",50)
        lib.global_constants.srp=self.get_standby_node(host.before.split('\n'))
        valid_state = ['IOS XR RUN', 'PRESENT','READY', 'UNPOWERED', 'FAILED', 'OK', 'NOT ALLOW ONLIN', 'DISABLED']
        try :
            host.expect_exact("#", timeout=30)
        except :
            pass

        for i in newstring:
            if i and i[0][:1]:
               first_char = i[0][:1]
               ## Check if first char is digit
               if first_char.isdigit() :
                    status = 1
                    for state in valid_state :
                        if i.find(state) >= 0:
                            status = 0
                    if status :
                       print bcolors.WARNING + "Please wait for following Nodes to come up" 
                       print "     %r" % i
                       print ""
                       print "ALL nodes are not Up; Upgrade can not proceed." + bcolors.ENDC
                       print ""
                       return -1
    
        print "All nodes are in correct state..."
        return 0 

