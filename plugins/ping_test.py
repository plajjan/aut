#!/router/bin/python-2.7.4

#==============================================================================
# ping_test.py - Plugin for checking reability to tftp.
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


import os
import sys
import re
from lib.global_constants import *

class IPlugin(object):
    """
    A plugin to check reachability of tftp
    or repository IP address given

    """
    plugin_name    = "Ping Check.."
    plugin_type    = "PreUpgrade"
    plugin_version = "1.0.0"


    def start(self, **kwargs):
        """
        Start the plugin
        Return -1 if the plugin has found a fatal error, 0 otherwise.
        """
        host = kwargs['session']
        pkg_path = kwargs['repository']
        if (not pkg_path):
           print "Couldn't ping, package repository path is not provided"
           return -1 
        try :
            host.expect_exact("#", timeout=30)
        except :
            pass
        pat = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
        ipaddr = re.findall(pat, pkg_path)
        protocol =['tftp:', 'sftp:', 'ftp:']
        list = [' '];
        list = pkg_path.split('/');
        if ( len(list[0]) if list[0] else list[1] in protocol):
            #cmd="run ping -p 0xf -z 0xa "+ipaddr[0]
            cmd = "ping "+ipaddr[0]
            host.sendline(cmd)
            try :
                status = host.expect_exact( [INVALID_INPUT, MORE, "#", PROMPT, EOF], timeout = tout_cmd)
            except :
	        print "Command: Timed out, before considering this as failure"
                print "Please check following log file for details\n%s"%(host.logfile)
                return -1;

        out = host.before
        if (out.find('Success rate is 0') != -1 or
            out.find('Bad hostname or protocol not running') != -1 or 
            out.find('UUUUU') != -1):
            return -1
        return 0

    def stop(self):
        """
        Stops the plugin (and prepares for deallocation)
        """
        pass


