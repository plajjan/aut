# =============================================================================
# cfg_consistency.py plugin to check config consistency
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
import commands
from lib.global_constants import *


class IPlugin:
    """
    This pluging commits the upgraded software and checks config consistency
    """
    plugin_name = "Config consistency check"
    plugin_type = POST_UPGRADE
    plugin_version     = "1.0.0"

    def start(self, **kwargs):
        """
        Start the plugin
        Return -1 if the plugin has found a fatal error, 0 otherwise.
        """
        aulog.info("Executing the checks")
        dev_string = kwargs['options'].device.replace(" ","_")
        #CFG_CONS_FILE = ".cfg_consistancy." + dev_string
        #fd_log = open(CFG_CONS_FILE,"w")
        host = kwargs['session']
 
        #n_blank_count = 0
        #1. show platform
        #2. show redundancy
        #3. install commit
 
        COMMIT_CMD = "run instcmd install commit -A"
        host.sendline(COMMIT_CMD)
        aulog.debug(COMMIT_CMD)

        try :
            status = host.expect_exact( [INVALID_INPUT, MORE, PROMPT,LOGIN_PROMPT_ERR, EOF], timeout=20)
        except :
            aulog.debug("Software commit successful.")

        output=""
        output = host.before.split("\n")

        aulog.debug(output)
        #fd_log.write(output) 
        #fd_log.close()
        #4. show install active/inactive/committed summary
        #5. Show configuration failed startup
 
        cmd = "cfgmgr_show_failed -a"
        status,output = commands.getstatusoutput(cmd)
        if status != 0:
            return -1
        #fd_log = open(my_logfile,"w")
        #fd_log.write(output);
 
        #with open('/tmp/output.txt') as infp:
            #for line in infp:
               #if line.strip():
                  #non_blank_count += 1
        #if (non_blank_count > 1):
            #return -1
        #fd_log.close()
        #6. Clear config inconsistency
        #7. install verify package / install verify package repair
        #8. Cfs check

        cmd = "cfgmgr_cfs_check -a"
        aulog.debug(cmd)
        status,output = commands.getstatusoutput(cmd)
        aulog.debug(output)
        if status != 0:
            return -1
        #9. mirror location 0/RSP0/CPU0 disk0:disk1:
        return 0

    def stop(self):
        """
        Stops the plugin (and prepares for deallocation)
        """
        pass

