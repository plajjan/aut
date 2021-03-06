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
import os

def get_pie_size(host, path, line):
          size = 0

          try :
              host.expect_exact("#")
          except:
              pass

          cmd = "admin show install pie-info "+ os.path.join(path,line)
          aulog.info(cmd)
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
             print host.before + host.after

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
    plugin_type = PRE_UPGRADE
    plugin_version     = "1.0.0"


    def start(self, **kwargs):
        host     = kwargs['session']
        pkg_path = kwargs['repository']
        pkg_list = kwargs['pkg-file-list']
        status = 0
        dt = kwargs['results']

        if kwargs['options'].turboboot :
           aulog.info("Disk space check is ignored for TURBOBOOT option")
           return 0  
        if not pkg_list:
           aulog.info("Pkg list file is not provided Ignoring this job")
           return 0
           
        aulog.info("Checking for free diskspace on boot device")

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
            aulog.warning("Disk space check failed, could not determine space available on disk")
            return 0

        #print "Avilable disk space is %s MB "%(available_size/(1024*1024))
        #print host.before
        disk_rp0 = get_free_space(host.before.split("\n")) 

        host.sendline('\r')
        try :
            host.expect_exact("#", timeout=30)
        except :
            pass

        # Get the package size
        fd = open(pkg_list,'r')
        total_req_size = 0
        try :
            for line in fd:
                total_req_size = total_req_size + get_pie_size(host, pkg_path, line.strip())
                sleep(10)
        except: 
           aulog.warning("Pkg not found or Repository is not rechable couldn't get size of packages")

        fd.close()

        print "Active  : required bytes:%d available bytes:%d"%(total_req_size, disk_rp0) 

        if (disk_rp0 >= total_req_size):
           return 0

        return -1


