# =============================================================================
# version_check.py - Plugin for checking version of running
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
from time import sleep
import os 

class IPlugin(object):
    """
    ASR9k Pre-upgrade check
    This pluging checks if version of all inputs packages are same. 
    If input package contains SMUs only , ensure that box is running same ver.
    """
    plugin_name = "Software Version check"
    plugin_type = PRE_UPGRADE
    plugin_version     = "1.0.0"
 
 
    def start(self, **kwargs):
        """
        """
        host = kwargs['session']
        host.sendline("\r")
        try :
            host.expect_exact("#", timeout=30)
        except :
            pass

        # Get 'show version brief output
        host.sendline("show version brief")
        try :
            status = host.expect( [INVALID_INPUT, MORE, PROMPT,"#", EOF], timeout=30)
        except :
         pass

        #TB implented 
        try :
            host.expect_exact("#", timeout=30)
        except :
            pass
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
   
