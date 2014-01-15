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


import re
from lib import aulog
from time import sleep
from lib.global_constants import *

class IPlugin(object):

	"""
	Pre-upgrade check
	This pluging checks and record active packages
	"""
	plugin_name = "Configuration backup."
	plugin_type = PRE_UPGRADE
	plugin_version     = "1.0.0"

	def save_configs (self, str, outfile):
		fo = open(outfile, "w");	
		fo.write(str);
		fo.close();
		return;



	def start(self, **kwargs):
                MORE = '--more--|--More--'

                # Get the session
                dev_string = kwargs['options'].device.replace(" ","_")
                CFG_BKP_FILE = ".cfg_bkup." + dev_string

                host = kwargs['session']
		aulog.debug("Backing up configurations in file %s..."%(CFG_BKP_FILE))
                try :
                   host.expect_exact("#", timeout = 15)
                except:
                   pass
                try: 
                    # Set terminal length
                    host.sendline("terminal length 0")
                    host.expect_exact("#")

	    	    # Pass CLI's to box
                    host.sendline("show running")

                    while 1:
                        status = host.expect_exact( [INVALID_INPUT, MORE, "end\r\n", EOF], timeout = tout_cmd)
		        self.save_configs(host.before, '.configuration_backup_file')
                        # match more
                        if status == 1:
                            host.send(" ")
                            continue
                        # match end
                        elif status == 2:
                            self.save_configs(host.after, '.configuration_backup_file')
                            break
                        else:
                            print "Unxpected statements"
                            print "Please check following log file for details\n%s"%(host.logfile)
                            return -1
                    # end of while

                    status = host.expect_exact( "#", timeout = tout_cmd)

                except :
		    aulog.debug(host.before)
                    aulog.debug("Command: Timed out, before considering this as failure")
                    return -1

                # reset terminal length
                host.sendline("terminal length 100")
                try: 
                    host.expect_exact("#")
                except :
		    aulog.debug(host.before)
                    aulog.debug("Command: Timed out, before considering this as failure")
                    return -1

		return 0
        def stop(self):
            """
            """
            pass

