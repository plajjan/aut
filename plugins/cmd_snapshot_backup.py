# =============================================================================
# cmd_snapshot_backup.py - Plugin for taking command backups.
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
INVALID='% Invalid input detected at'

class IPlugin(object):

	"""
	Pre-upgrade check
	This pluging collects all CLI provided in file 
	"""
	plugin_name = "Backup CLI snapshots.."
	plugin_type = PRE_UPGRADE
	plugin_version     = "1.0.0"

	def save_packages (self, str, outfile):
		fo = open(outfile, "a");	
		fo.write(str);
		fo.close();
		return;



	def start(self, **kwargs):
                # Get the session
                host = kwargs['session']
                clis = kwargs['cmd_file']
                if (not clis):
                    aulog.info(bcolors.WARNING + 
                        """Input file missing(-c option): 
                           Plugin expects file having list of CLI's to dump,
                           Ignoring"""+ bcolors.ENDC)
                    return 0 

                fo = open('.CLI_backups', "w")
                aulog.info("The cli file provided is ", clis)
                cli = open(clis, "r"); 
                for cmd in cli:
                   if (len(cmd.strip()) == 0):
                      #print "Not a command"
                       pass
                   else: 

                      try :
                         host.expect_exact("#", timeout=1)
                      except :
                          pass
                      try :
                          host.expect_exact("#", timeout=1)
                      except :
                          pass

                      host.sendline(cmd)
                      try :
                       status = host.expect_exact( [INVALID_INPUT, MORE,"#",INVALID,'\'^\'',  EOF], timeout = tout_cmd)
                       #print "Success", status
                      except :
                         pass
                      #print host.before,status
                      if status == 3 or status == 0 or status == 4:
                         aulog.info("Couldn't get %s(probably feature not enabled) "%(cmd.strip('\n')))
                      else:
                         sleep(2)
                         str="++++++++"+cmd.strip('\n')+"++++++++\n#"
                      #host.before = '\n'+str+host.before+'\n'
                         fo.write('\n'+str+host.before+'\n');
                         print bcolors.OKGREEN + "++++++++ done with %s ++++"%(cmd.strip('\n')) + bcolors.ENDC

                fo.close()
                cli.close()
                
                try :
                    host.expect_exact("#", timeout=1)
                except :
                    pass
		return 0

