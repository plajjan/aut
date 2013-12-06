#!/router/bin/python-2.7.4

#==============================================================
# version_check.py - Plugin for checking version of running
# software.
#
# Jun 2013, syaragat
#
# Copyright (c) 2013 by Cisco Systems, Inc.
# All rights reserved.
#==============================================================
#

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
    plugin_type = "PreUpgrade"
    version     = "1.0.0"
 
 
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
   
