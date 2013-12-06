# =============================================================================
# redundancy_check.py -- plugin to parse and check show redundancy 
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


from lib.global_constants import *

class IPlugin(object):
    """
    ASR9k Pre-upgrade check
    This pluging checks Standby state
    """
    plugin_name = "Redundancy Node Check.."
    plugin_type = "PreUpgrade"
    version     = "1.0.0"
 
 
    def start(self, **kwargs):
        """
        """
        host = kwargs['session']
        print ""
        print "Pre-upgradge checks..."
        print "Checking Standby RP State..."

        try :
            host.expect_exact("#", timeout=1)
        except :
            pass
        # Get 'show platform status o/p
        host.sendline("admin show redundancy location all")
        try :
            status = host.expect_exact( [INVALID_INPUT, MORE, PROMPT,"#", EOF], timeout = tout_cmd)
            #print "Success",status
        except :
            print "Command: Timed out, before considering this as failure"
            print "Please check following log file for details\n%s"%(host.logfile)
            return -1;

        newstring = host.before.split("\n",50)
        if len(newstring) < 6:
           print "show redundacny o/p is insufficient"
           return -1
        
        if "is in STANDBY role" in newstring[4]:
            print "Standby node exists. Checking state ...."
            if "is ready" in newstring[5]:
                print "Standby is ready. Upgrade can proceed"
                print ""
                return 0
            else:
                print newstring[5]
                print "Standby is not ready. Upgradge can not proceed "
                print ""
                return -1
        else:
            print "No standby node found. Upgrade can proceed"
            print ""
            return 0
     
    def stop(self):
        """
        """
        pass
def main():
    var1 = IPlugin()
    var1.start()
 
if __name__ == '__main__':
    main()
 
