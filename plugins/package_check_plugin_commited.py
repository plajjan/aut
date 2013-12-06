#!/router/bin/python-2.7.4

# =============================================================================
# package_check_plugin_commited.py  - Plugin to capture 
# committed packages on the system.
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
from lib.global_constants import *
from time import sleep

class IPlugin(object):

	"""
	ASR9k Pre-upgrade check
	This pluging checks the packages state
	"""
	plugin_name = "Committed Package Check.."
	plugin_type = "PreUpgrade"
	version     = "1.0.0"

	def save_packages (self, str, outfile):
		fo = open(outfile, "w");	
	        fo.write(str);
		fo.close();
		return;

	def start(self, **kwargs):
                host = kwargs['session']
		try :
            	    host.expect_exact("#", timeout=1)
        	except :
                    pass
		print "Saving the list of Committed  packages"
                host.sendline("admin show install commit")
                try :
                    status = host.expect_exact( [INVALID_INPUT, MORE, "#",PROMPT, EOF], timeout = tout_cmd)
                except :
                    print "Command: Timed out, before considering this as failure"
                    print "Please check following log file for details\n%s"%(host.logfile)
                    return -1;

                self.save_packages(host.before, '.commit_file' );
		sleep(5)
		return 0;
        def stop(self):
         """
         """
         pass

