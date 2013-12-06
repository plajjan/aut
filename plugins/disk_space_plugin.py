#!/router/bin/python-2.7.4

#==============================================================================
# disk_space_plugin.py - Plugin for checking available disk space.
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
import pexpect
from lib.global_constants import *
from time import sleep

def get_pie_size(host, path, line):
          size = 0

          try :
              host.expect_exact("#")
          except:
              pass

          cmd = "admin show install pie-info "+path+line
          host.sendline(cmd)
          try :
             status = host.expect( [INVALID_INPUT, "Error:    Failed to verify pie file",
                      "Compressed size", '#', LOGIN_PROMPT_ERR, EOF],searchwindowsize=1000, timeout=tout_cmd)
          except:
             pass

          output = host.before.split('\n')
          if status == 3 or status ==2:
             try :
                size = int(output[5].split(':')[1])
             except:
                 try:
                   size = int(output[6].split(':')[1])
                 except:
                   size = int(output[7].split(':')[1])

          if status != 2: 
             print bcolors.WARNING + line.strip('\n'),"Package not found in repository ",path + bcolors.ENDC

          try :
              host.expect_exact("#")
          except:
              pass

          return size

def get_free_space(disk_lines):
    i=0 
    available_size = 0

    while(i<len(disk_lines)):
                # disk0 - is assumed as boot device;
                if(re.search("\ disk0:", disk_lines[i])):
                        expr = re.compile(r'(?P<USED>\d+)\W+(?P<AVAIL_SIZE>\d+)\W+');
                        s = expr.search(disk_lines[i]);
                        available_size =long(s.group('AVAIL_SIZE'));
                        break
                i+=1;

    return available_size

class IPlugin(object):
    """
    Pre-upgrade check
    This pluging checks the available disk space
    """
    plugin_name = "Disk Space check.."
    plugin_type = "PreUpgrade"
    version     = "1.0.0"


    def start(self, **kwargs):
        host     = kwargs['session']
        pkg_path = kwargs['repository']
        pkg_list = kwargs['pkg-file-list']
        status = 0
        dt = kwargs['results']
        
        if not pkg_list:
           print bcolors.WARNING + "Pkg list file is not provided Ignoring this job" + bcolors.ENDC
           return 0
           
        print "Checking for free diskspace on boot device"

        host.sendline('\r')
        try :
            host.expect_exact("#", timeout=30)
        except :
            pass

        try :
            host.expect_exact("#", timeout=30)
        except :
            pass

        #Read output of "show filesystem"
        host.sendline("show filesystem")
        try :
            status = host.expect_exact( [INVALID_INPUT, MORE, "#",
                                         LOGIN_PROMPT_ERR, EOF], timeout = tout_cmd)
        except :
            print "Command: Timed out, before considering this as failure"
            print "Please check following log file for details\n%s"%(host.logfile)
            return -1;

        #print "Avilable disk space is %s MB "%(available_size/(1024*1024))
        #print host.before
        disk_rp0 = get_free_space(host.before.split("\n")) 

        host.sendline('\r')
        try :
            host.expect_exact("#", timeout=30)
        except :
            pass

        host.sendline("show filesystem location  0/RP1/CPU0")        
        try :
            status = host.expect_exact( [INVALID_INPUT, MORE,"show filesystem location", "No such node","% Invalid input detected at",
                                          LOGIN_PROMPT_ERR, EOF], timeout=180)
        except :
            if status == 3:
               pass # Fix me

        if status != 2 and status != 3 and status !=4:
           disk_rp1 = get_free_space(host.before.split("\n"))
        else:
           disk_rp1 = 0
           print bcolors.WARNING + "No Standby(0/RP1/CPU0) node found .." + bcolors.ENDC

        try :
            host.expect_exact("#", timeout=30)
        except :
            pass
        # Get the package size
        fd = open(pkg_list,'r')
        total_req_size = 0
        try :
            for line in fd:
                total_req_size = total_req_size + get_pie_size(host, pkg_path, line)
                sleep(10)
        except: 
           print bcolors.WARNING + "Pkg not found or Repository is not rechable couldn't get size of packages"

        fd.close()

        print "Active  : required bytes:%d available bytes:%d"%(total_req_size, disk_rp0) 
        if (status != 3) and (status !=2) and (status!=4):
           print "Standby : required bytes:%d available bytes:%d"%(total_req_size, disk_rp1)

        if (disk_rp0 >= total_req_size) and ((status == 3 or status == 2 or status ==4) or (disk_rp1 >= total_req_size)) :
           return 0

        return -1


    def stop(self):
        """
        """
        pass
