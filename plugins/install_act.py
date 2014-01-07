import re
import sys
import commands
from time import *
import pexpect
from sys import stdout
from lib.global_constants import *
import lib.pkg_utils

#few macros/constants used in the code
XML_ADD_RESPONSE_FILE   = "/tmp/accel_upgrade_add_response.xml"
LOG_FILE                = "/tmp/acc_log.txt"
ERROR_LOG_FILE          = "/tmp/acc_err_log.txt"
XML_ACT_FILE            = "/tmp/accel_upgrade_act.xml"
XML_ACT_RESPONSE_FILE   = "/tmp/accel_upgrade_act_response.xml"
pkgutils = lib.pkg_utils

class IPlugin:
    """
    A plugin for act operation
    it will create xml equivalent for
    act operation.
    Arguments:
    1.options
    """
    plugin_name = "Install Act"
    plugin_type = UPGRADE
    plugin_version = "1.0.0"

    def watch_operation(self):
        """
        function to keep watch on progress of operation
        """
        retval = SYSTEM_RELOADED
        chars = '\\'
        pat = r'There are no install requests in operation'
        cpat = re.compile(pat)
        cmd = " admin show install request \r"
        pat1 = r'The operation is \d+% complete'
        cpat1 = re.compile(pat1)
        cpat2 = re.compile(r'\d+,*\w* downloaded: Download in progress')
        count = 0

        #expecting shell before sending any commands
        try:
            self.command_exec.expect(['#'],searchwindowsize=1000,timeout=30)
        except Exception,e:
            self.error_log_file.write("ERROR: in watch_operation\n")
            self.error_log_file.write("exception occured while expecting # for the first time\n")
            output = str(type(e))
            self.error_log_file.write(output + "\n")

        while 1:
            self.command_exec.sendline(cmd)
            try:
                index = self.command_exec.expect(['The operation is \d+% complete','There are no install requests in operation'],searchwindowsize=1000,timeout=30)
                if (index == 1):
                    stdout.write("\n%c 100%% complete \r"%(chars))
                    break
                elif (index == 0):
                    display_string = ""
                    txt = self.command_exec.after
                    match_str = re.findall(cpat1,txt)
                    if match_str:
                        display_string = display_string + str.strip(str(match_str[0]))
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
                self.error_log_file.write("EOF occurred when expecting result of show install req \n")
                retval = -1
                break
            except pexpect.TIMEOUT:
                self.error_log_file.write("TIMEOUT occurred when expecting result of show install req \n")
                print "\ntimeout",self.command_exec.before
                #retval = -1
                break  
        
        try:
            self.command_exec.expect(['#'],searchwindowsize=1000,timeout=30)
        except Exception,e:
            self.error_log_file.write("ERROR: in watch_operation\n")
            self.error_log_file.write("exception occured while expecting # for the second time\n")
            output = str(type(e))
            self.error_log_file.write(output + "\n")
  
        cmd = "admin show install log %d"%(int(self.id))
    
        self.command_exec.sendline(cmd)
        try:
            index = self.command_exec.expect(['successfully','failed'],searchwindowsize=1000,timeout=30)
            aulog.info(self.command_exec.after)
            aulog.info(self.command_exec.before)
            if ((index == 1)):
                self.error_log_file.write("install act failed\n")
                retval = -1
            elif (index == 0):
                act_id = open(XML_ADD_RESPONSE_FILE,"w")
                act_id.write(self.id)
                act_id.close()
  
        except pexpect.EOF:
            self.error_log_file.write("EOF encountered when expecting for other input\n")
            self.error_log_file.write("ERROR:cannot parse show install log detail output\n")
            retval = SYSTEM_RELOADED
        except pexpect.TIMEOUT:
            self.error_log_file.write("TIMEOUT encountered when expecting for other input\n")
            self.error_log_file.write("ERROR:cannot parse show install log detail output\n")
            retval = SYSTEM_RELOADED

        return int(retval)




    def install_getID(self):
        """
        get the install id of add operation
        """
        self.id = -1

    def get_active_pkgs(self):

        self.command_exec.sendline()
        sleep(5)
        status = self.command_exec.expect_exact( [INVALID_INPUT,"#", MORE, PROMPT, EOF],
               timeout = 10)
        self.command_exec.sendline("admin show install active summary")
        sleep(5)
        try :
           status = self.command_exec.expect_exact( [INVALID_INPUT,"#", MORE, PROMPT, EOF],
               timeout = 10)
        except :
           return None
        return self.command_exec.before

    def get_inactive_pkgs(self):

        self.command_exec.sendline()
        sleep(5)
        status = self.command_exec.expect_exact( [INVALID_INPUT,"#", MORE, PROMPT, EOF],
               timeout = 10)
        self.command_exec.sendline("admin show install inactive summary")
        sleep(5)
        try :
           status = self.command_exec.expect_exact( [INVALID_INPUT,"#", MORE, PROMPT, EOF],
               timeout = 10)
        except :
           return None
        return self.command_exec.before

    def get_tobe_activated_pkglist(self,kwargs):
        pkg_list = kwargs['pkg-file-list']
        added_pkgs = pkgutils.NewPackage(pkg_list)
        inactive_pkgs = self.get_inactive_pkgs()
        active_pkgs = self.get_active_pkgs()
        inactive_pkgs = pkgutils.OnboxPackage(inactive_pkgs,"inactive")  
        active_pkgs = pkgutils.OnboxPackage(active_pkgs,"install active")  
        pkg_to_activate  = pkgutils.pkg_tobe_activated(added_pkgs.pkg_list,inactive_pkgs.pkg_list,active_pkgs.pkg_list)
        return " ".join(pkg_to_activate)


    def install_act(self,kwargs):
        """
        it performs activate operation
        """
        retval = 0
        
        #get install operation ID of add operation which
        #added packages to be executed
        self.install_getID()
        if (self.id > 0) :
            self.get_pkg_list()
            #log the activity
            log_msg = "install operation ID to be executed is %d\n"%(self.id)
            self.log_file.write(log_msg)
            cmd = " admin install activate id %d prompt-level none"%(int(self.id))
        else :
            tobe_activated = self.get_tobe_activated_pkglist(kwargs)
            if not tobe_activated :
                aulog.error( """
                Package list is empty or all package are not in inactive state""")
                return -1
            cmd = " admin install activate %s prompt-level none"%(tobe_activated)
        aulog.info(cmd)
        number = r'\d+'
        cnumber = re.compile(number)
        sleep(2)

        try:
            self.command_exec.expect(['#'],searchwindowsize=1000)
        except Exception,e:
            self.error_log_file.write("ERROR:failed when expecting # before doing act operation\n")
            output = str(type(e))
            self.error_log_file.write(output + "\n")


        self.command_exec.sendline(cmd)
        try:
            index = self.command_exec.expect(['Install operation \d+'],timeout=30,searchwindowsize=1000)
            string = self.command_exec.after
            is_number = re.findall(cnumber,string)
            if is_number:
                self.id = is_number[0]
            #print self.id

        except pexpect.EOF:
            self.error_log_file.write("EOF occurred while expecting LOGIN PROMPT\n")
            self.error_log_file.write("activate operation didnt execute properly\n")
            retval = -1

        except pexpect.TIMEOUT:
            self.error_log_file.write("TIMEOUT occurred while expecting LOGIN PROMPT\n")
            self.error_log_file.write("activate operation didnt execute properly\n")
            retval = -1

        return int(retval)


    def start(self,**kwargs):
        """
        Start the plugin

        Return False if the plugin has found a fatal error, True otherwise.
        """
        retval = 0
        #opening log files for logging error messages
        self.log_file        = open(LOG_FILE, "a")
        self.error_log_file  = open(ERROR_LOG_FILE,"a")

        if (kwargs.has_key('session')):
            self.command_exec = kwargs['session']
            del kwargs['session']
        else:
            error_log_file.write("FATAL ERROR: session details not provided\n")
            retval = -1
        
        if (retval == 0):
            retval = self.install_act(kwargs)
        if (retval == 0):
            retval = self.watch_operation()
        return int(retval)

    def stop(self):
        """
        Stops the plugin (and prepares for deallocation)
        """
        #closing file opened for logging purposes
        self.log_file.close()
        self.error_log_file.close()

        pass



