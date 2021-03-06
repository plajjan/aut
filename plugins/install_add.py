# =============================================================================
# install_add.py - plugin for adding packages
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
import commands
import os
import re
import pexpect
from sys import stdout
from time import *
import lib.global_constants
from lib.global_constants import *


STAGING_DEVICE        = "."
TFTP_COPY_CMD         = "cp"
XML_ADD_FILE          = "/tmp/accel_upgrade_add.xml"
XML_ADD_RESPONSE_FILE = "/tmp/accel_upgrade_add_response.xml"
TMP_LOG_FILE          = "/tmp/ms_log_file.txt"

class IPlugin(object):
    """
    A plugin for add operation
    it will create xml equivalent for
    add operation. 
    Arguments:
    1.one argument of type dictionary
    """
    plugin_name     = "Install Add"
    plugin_type     = PRE_UPGRADE_AND_UPGRADE
    plugin_version  = "1.0.0"
    install_oper_id = 0
    
    def watch_operation(self):
        """
        function to keep watch on progress of operation
        """
        retval = 0
	i = -1
        chars = '\\'
        pat = r'There are no install requests in operation'
        cpat = re.compile(pat)
        cmd = " admin show install request "
        pat1 = r'The operation is \d+% complete'
        cpat1 = re.compile(pat1)
        cpat2 = re.compile(r'\d+,*\w* downloaded: Download in progress')
        count = 0

        #expecting shell before sending any commands
        try:
            self.command_exec.expect(['#'],searchwindowsize=1000)
        except Exception,e:
            aulog.debug("Failure during watch operation of install add ") 

        while 1:
            self.command_exec.sendline(cmd)
            try:
                index = self.command_exec.expect(['The operation is \d+% complete','There are no install requests in operation'],timeout=300,searchwindowsize=1000)
                if (index == 1):
                    #we reach here when there is no install operation in progress.
                    #that means either operation completed successfully or failed 
                    stdout.write("\n%c 100%% complete \r"%(chars))
                    break
                elif (index == 0):
                    #operation still in progress, add progress bar
                    display_string = ""
                    txt = self.command_exec.after
                    try:
                        i = self.command_exec.expect([r'\b\d+,*\w* downloaded: Download in progress'],timeout=60,searchwindowsize=1000)
                    except Exception,e:
                        aulog.debug("failed in getting download progress\n")
                        err_msg = "%s"%(str(type(e)))
                        aulog.debug(err_msg + "\n")

                    match_str = re.findall(cpat1,txt)
                    if match_str:
                        display_string = display_string + str.strip(str(match_str[0]))
                    if (i == 0):
                        download = re.search(cpat2,str(self.command_exec.after))
                        if download:
                            display_string = display_string + "." + str.strip(str(download.group(0)))
 
                    res = count % 4
                    if (res == 0):
                        chars = "|"
                    elif (res == 1):
                        chars = "/"
                    elif (res == 2):
                        chars = "-"
                    elif (res == 3):
                        chars = "\\"
                count += 1
                stdout.write("%c  %s \r"%(chars,display_string))
                stdout.flush()

            except pexpect.EOF:
                aulog.error("EOF occurred when expecting result of show install req \n")
                retval = -1
                break
            except pexpect.TIMEOUT:
                aulog.debug("\nTimeout :%s"%(self.command_exec.before))
                aulog.error("TIMEOUT occurred when expecting result of show install req \n")
                #retval = -1
                break  
        
        try:
            self.command_exec.expect(['#'],searchwindowsize=1000,timeout=30)
        except Exception,e:
            aulog.debug("ERROR: in watch_operation\n")
            aulog.debug("exception occured while expecting # for the second time\n")
            output = str(type(e))
            aulog.debug(output + "\n")
  
        cmd = "admin show install log %d"%(int(self.install_oper_id))
    
        self.command_exec.sendline(cmd)
        try:
            index = self.command_exec.expect(['successfully','failed'],searchwindowsize=1000,timeout=30)
            #print "index in watch %s"%(index)
            if ((index == 1)):
                aulog.debug("install add failed\n")
                retval = -1
            elif (index == 0):
                lib.global_constants.add_id = self.install_oper_id 
   
        except pexpect.EOF:
            aulog.debug("EOF encountered when expecting for other input\n")
            aulog.debug("ERROR:cannot parse show install log detail output\n")
            retval = -1
        except pexpect.TIMEOUT:
            aulog.debug("TIMEOUT encountered when expecting for other input\n")
            aulog.debug("ERROR:cannot parse show install log detail output\n")
            retval = -1

        return int(retval)


    def install_add(self,kwargs):
        """
        it performs add operation of the pies listed in given file
        """
        retval = 0
        options = kwargs['options']
        if (kwargs.has_key('repository')):
            repo_str = kwargs['repository']
        else:
            aulog.debug("FATAL ERROR:repository not provided\n")
            retval = -1
        if (retval == 0):
            if (kwargs.has_key('pkg-file-list')):
                pkg_list = kwargs['pkg-file-list']
            else:
                aulog.debug("FATAL ERROR:pkg-file-list not provided\n")
                retval = -1
        if (retval == 0):
            #copy file to local directory
            src_file = pkg_list
            pkg_list = os.path.join(STAGING_DEVICE,kwargs['pkg-file-list'])
            if os.path.abspath(src_file) != os.path.abspath(pkg_list) :
                cmd           = "%s %s %s"%(TFTP_COPY_CMD,src_file,pkg_list)
                status,output = commands.getstatusoutput(cmd)
                print output
                if (not(status == 0)):
                    aulog.debug(output + "\n")
                    aulog.debug("failed in copying pkg_list file to the box\n")
                    retval = -1
        if (retval == 0):
            file_opened = open(pkg_list,"r")
            file_list = ""
            while 1:
                tmp = file_opened.readline()
                if (len(tmp) == 0):
                    break
                # skip vm image for turbo boot
                if tmp.find('.vm-') >= 0:
                    continue
                # Ignore empty lines
                elif not str.strip(tmp) :
                    continue
                
                file_list = file_list + " " + str.strip(tmp)
       
            #print file_list 
            number = r'\d+'
            cnumber = re.compile(number)
            #pat = r'Install operation \d+'
            #cpat = re.compile(pat)
            if not file_list and options.turboboot : 
                aulog.warning("There are no additional packages to be added after Turbo boot")
                return SKIPPED
                
            cmd = "admin install add source %s %s"%(repo_str,file_list)
            aulog.info(cmd) 
            #expecting terminal
#            try:
#                self.command_exec.expect(['#'],timeout=60,searchwindowsize=1000)
                #print "+"*20,"printing before add",self.command_exec.before
                #print "+"*20,"printinf after add",self.command_exec.after
#            except Exception,e:
#                aulog.debug("ERROR:failed when expecting # before doing add operation\n")
#                output = str(type(e))
#                aulog.debug(output + "\n")
            
            self.command_exec.sendline(cmd)
            try:
                index = self.command_exec.expect([r'Install operation \d+','#'],timeout=60,searchwindowsize=1000)
                #print index
                #print "printing after %s"%(self.command_exec.after)
                #print "printing before %s"%(self.command_exec.before)
                if (index == 0):
                    string = self.command_exec.after
                    is_number = re.findall(cnumber,string)
                    if is_number:
                        self.install_oper_id = is_number[0]
                    else:
                        retval = -1
                elif (index == 1):
                    cmd = "admin show install request"
                    self.command_exec.sendline(cmd)
                    try:
                        self.command_exec.expect([r'Install operation \d+'],timeout=60,searchwindowsize=1000)
                    except pexpect.EOF:
                        aulog.debug("cannot get install operation id.EOF encountered\n")
                        retval = -1
                    except pexpect.TIMEOUT:
                        aulog.debug("cannot get install operation id. TIMEOUT encountered\n")
                        retval = -1

                
                    #print install_oper_id
                #print "index is %s"%(str(index))
                #if (index == 0):
                #print "I m here"
                #string = self.command_exec.after
                #print string #for debugging purpose
                #install_oper_id = re.findall(cnumber,string)[0]
                #print type(install_oper_id)
            except pexpect.EOF:
                aulog.debug("EOF occured while expecting install operation id\n")
                retval = -1
            except pexpect.TIMEOUT:
                aulog.debug("TIMEOUT occured while expecting install operation id\n")
                retval = -1

            #print "*************",self.command_exec.after 
            #print "+++++++++++++",self.command_exec.before

            #print index
#           print self.command_exec.after
#           print self.command_exec.before
        return (int(retval))
    


    def start(self ,**kwargs):
        """
        Start the plugin

        Return False if the plugin has found a fatal error, True otherwise.
        """
        #opening log files for logging error messages
        #self.log_file        = open(LOG_FILE, "a")
        #self.error_log_file  = open(ERROR_LOG_FILE,"a")
        retval = 0
        if (kwargs.has_key('session')):
            self.command_exec = kwargs['session']
            del kwargs['session']
        else:
            aulog.debug("FATAL ERROR: session details not provided\n") 
            retval = -1

        if (retval == 0):
            retval = self.install_add(kwargs)
        if (retval == SKIPPED ):
            # Install operation is skipped
            return 0 
        if (retval == 0):
            retval = self.watch_operation()
        return int(retval)
        pass



