#==============================================================================
# parser.py -- parser for accelerated upgrade CLI
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

import sys
import os
import commands
import optparse
import shutil
from   global_constants import *
from lib import aulog

"""
Coments diff
"""
class parse_inputs:
    """ A basic class to hold packaging requirements (inputs)
        which is used in packaging process
    """
    def __init__(self, options) :
        self.options = options



def usage():
    print "usage: %s [OPTIONS]" % sys.argv[0]

def parsecli():
    oparser = optparse.OptionParser()
    oparser.add_option("-l", "--login", dest="login", default=None, metavar='LOGIN',
        help="User name to login to the device. e.g.: -l admin.")

    oparser.add_option("-p", "--passwd", dest="password", default=None, metavar='PASSWORD', 
        help="Login password for the device. e.g.: -p passwd'.")

    oparser.add_option("-T", "--tunnel", dest="tunnel", default=None, metavar="'NAME'",
        help="List of inetremediate serevers to reach the device. e.g.: -T server-1,server-2")

    oparser.add_option("-D", "--dlist",  type="string", dest="devices", 
        default=None, metavar='FILE',
        help="A file containing list of devices to upgrade. e.g.:-D filename'")

    oparser.add_option("-d", "--device", dest="device", default=None, metavar="'x.x.x.x'",
        help="The device you want to run this script against. Example below..\n"
              "-d '192.168.101.1', --device='192.168.101.1'")
    oparser.add_option("-t", "--term", dest="terminal", default="both", metavar="Protocol", 
        help="What terminal you are going to use (ssh or telnet or both) The default is to use both."
             " Example below.. -t 'ssh', --term='ssh'")
    oparser.add_option("-r", "--repository", type="string", dest="repository_path", 
        default=None, metavar="PATH", help="Path where packages are stored[Mandatory]") 
    oparser.add_option("-f", "--pkg_file_list", type="string", dest="pkg_file",default=None, 
        metavar="FILE", help="File which contains list of packages needs to be add/activate[Mandatory]")
    oparser.add_option("-c", "--commands", dest="cli_file", default=None, 
        metavar="FILE", help="File which contains list of commands to backup")
    oparser.add_option("-k", "--continue", action="store_true", dest="ignore_fail", default=False, 
        metavar=' ', help="Continue with all pre-upgrade plugins by ignoring failures")
    oparser.add_option("--pre-upgrade-checks-only", action="store_const", const=1, dest="preupgradeset",
        default=0, metavar=" ", help="Run only Pre-upgrade checks")
    oparser.add_option("--post-upgrade-checks-only", action="store_const", const=3, dest="postupgradeset", 
        default=0, metavar=" ", help="Run only Post-upgrade checks, Note : Plugins which depend on data collected during pre upgrade checks to verify will fail , but execution will not be blocked")
    oparser.add_option("--upgrade-only", action="store_const", const=2, dest="upgradeset", default=0,
        metavar=" ", help="do an upgrade without running pre and post upgrade checks")
    oparser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
        metavar=" ", help="execute with verbose")
    #oparser.add_option('-z', dest='optimize',action='store_true', default=False,
    #    metavar='Optimize',
    #    help='Optimize to not recreate packages if they exist in Package Repository')

    if len(sys.argv) < 2 : 
        usage()
        sys.argv.extend("-h")
    options, args = oparser.parse_args()
    if len(sys.argv) < 2 :
        usage()
        sys.exit(-1)
    check_options(options)
    
    return options,args

def check_options(options):
    status = True
    if not options.login:
        print_failure("Mandatory option 'Login' is missing")
        status = False
    if not (options.device or options.devices):
        print_failure("Mandatory option 'Device' is missing")
        status = False
    if not options.password:
        print_failure("Mandatory option 'Password' is missing")
        status = False
    if not options.repository_path and not options.postupgradeset :
        print_failure("Mandatory option 'Repository path' is  missing")
        status = False
    if not options.pkg_file and not options.postupgradeset :
        print_failure("Mandatory option 'Package list file' is  missing")
        status = False
    if options.preupgradeset and options.postupgradeset:
       print_failure("--pre-upgrade-checks-only and --post-upgrade-checks-only options\n"
                     "  are mutually exclusive")
    if not status :
       sys.exit(-1)
    return 0


