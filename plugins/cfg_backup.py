#!/router/bin/python-2.7.4

# =============================================================================
# cfg_backup.py  - Plugin to capture(show running)
# configurations present on the system.
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


import re;
from time import sleep
from lib.global_constants import *

class IPlugin(object):

	"""
	Pre-upgrade check
	This pluging checks and record active packages
	"""
	plugin_name = "Configuration backup."
	plugin_type = "PreUpgrade"
	version     = "1.0.0"

	def save_configs (self, str, outfile):

		fo = open(outfile, "w");	
		fo.write(str);
		fo.close();
		return;



	def start(self, **kwargs):
                # Get the session
                host = kwargs['session']
		print "Backing up configurations..."
                try :
                   host.expect_exact("#")
                except:
                   pass
		# Pass CLI's to box
                host.sendline("show running")
                try :
                    status = host.expect_exact( [INVALID_INPUT, MORE, "#", EOF], timeout = tout_cmd)
                except :
                    print "Command: Timed out, before considering this as failure"
                    print "Please check following log file for details\n%s"%(host.logfile)
                    return -1;
		self.save_configs(host.before, '.configuration_backup_file');
		return 0
        def stop(self):
            """
            """
            pass

