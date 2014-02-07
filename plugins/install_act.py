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
    install_oper_id = 0
    prompt = "#"
    def watch_operation(self,host):
        """
        function to keep watch on progress of operation
        """
        retval = INSTALL_METHOD_PROCESS_RESTART
        chars = '\\'
        pat = r'There are no install requests in operation'
        cpat = re.compile(pat)
        cmd = " admin show install request \r"
        pat1 = r'The operation is \d+% complete'
        cpat1 = re.compile(pat1)
        cpat2 = re.compile(r'\d+,*\w* downloaded: Download in progress')
        count = 0

        #expecting install method
        host.sendline()
        try:
            index = host.expect(['Install Method: Parallel Process Restart','This operation will reload the following node:'],searchwindowsize=1000,timeout=30)
        except Exception,e:
            output = str(type(e))
            aulog.error("Exception occured while expecting install method\n%s,\n%s"%(host.before,output))
        if index == 1 : 
            retval = SYSTEM_RELOADED

        retry_count = 0
        while 1:
            host.sendline(cmd)
            try:
                index = host.expect(['The operation is \d+% complete','There are no install requests in operation',self.prompt],timeout=90)
                if (index == 1 or index == 2):
                    stdout.write("\n%c 100%% complete \r"%(chars))
                    break
                elif (index == 0):
                    display_string = ""
                    txt = host.after
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
                aulog.error("EOF occurred when expecting result of show install req \n")
                break
            except pexpect.TIMEOUT:
                aulog.debug(cmd)
                aulog.error("TIMEOUT occurred when expecting result of show install req")
                break  
        
        host.sendline()
        try:
            host.expect_exact(['#'],searchwindowsize=1000,timeout=30)
        except Exception,e:
            aulog.error("ERROR: in watch_operation\n")
            aulog.error("exception occured while expecting # for the second time\n")
            output = str(type(e))
            aulog.error(output + "\n")

        cmd = "admin show install log %d"%(int(self.install_oper_id))
    
        host.sendline(cmd)
        try:
            index = host.expect_exact(['successfully','failed'],searchwindowsize=1000,timeout=30)
            aulog.info(host.after)
            aulog.info(host.before)
            if ((index == 1)):
                aulog.error("install act failed\n")
            elif (index == 0):
                act_id = open(XML_ADD_RESPONSE_FILE,"w")
                act_id.write(self.install_oper_id)
                act_id.close()
  
        except pexpect.EOF:
            aulog.error("Cannot parse show install log detail output\n")
        except pexpect.TIMEOUT:
            if retry_count > 5 :
                aulog.error("%s\n%s\nTIMEOUT encountered when expecting for other input\n"%(cmd,host.before))
            else :
                aulog.debug("%s\n%s\nTIMEOUT encountered when expecting for other input\n"%(cmd,host.before))
                retry_count = retry_count + 1
            

        return int(retval)




    def get_active_pkgs(self,host):

        cmd = "admin show install active summary"
        host.sendline(cmd)
        try :
           status = host.expect_exact( [INVALID_INPUT,self.prompt, MORE, PROMPT, EOF],
               timeout = 20)
        except :
           return None
        aulog.debug("%s\n%s"%(cmd,host.before))
        return host.before

    def get_inactive_pkgs(self,host):
        cmd = "admin show install inactive summary"
        host.sendline(cmd)
        try :
            status = host.expect_exact( [INVALID_INPUT,self.prompt, MORE, PROMPT, EOF], timeout = 30)
        except :
            return None
        aulog.debug("%s\n%s"%(cmd,host.before))
        return host.before

    def get_tobe_activated_pkglist(self,host,kwargs):
        pkg_list = kwargs['pkg-file-list']
        added_pkgs = pkgutils.NewPackage(pkg_list)
        added_pkgs_raw = open(pkg_list,'r').read()
        inactive_pkgs_raw = self.get_inactive_pkgs(host)
        active_pkgs_raw = self.get_active_pkgs(host)

        inactive_pkgs = pkgutils.OnboxPackage(inactive_pkgs_raw,"inactive")  
        active_pkgs = pkgutils.OnboxPackage(active_pkgs_raw,"install active")  
        package_to_activate  = pkgutils.extra_pkgs(active_pkgs.pkg_list,added_pkgs.pkg_list)

        # Test If there is anything to activate
        if not package_to_activate :
            return 
        else :
            pkg_to_activate  = pkgutils.pkg_tobe_activated(added_pkgs.pkg_list,inactive_pkgs.pkg_list,active_pkgs.pkg_list)
            if not pkg_to_activate :
                state_of_packages = "To be added :\n%s\n%s%s"%(added_pkgs_raw,inactive_pkgs_raw,active_pkgs_raw)
                aulog.error("One or more package to be activated is not in inactive state.\n%s"%(state_of_packages))
            else :
                return " ".join(pkg_to_activate)


    def install_act(self,host,kwargs):
        """
        it performs install activate operation
        """
        retval = 0
        #get install operation ID of add operation which
        #added packages to be executed
        tobe_activated = self.get_tobe_activated_pkglist(host,kwargs)
        if not tobe_activated :
            aulog.warning( "The package is already active, nothing to be activated.")
            return SKIPPED
        cmd = " admin install activate %s prompt-level none"%(tobe_activated)
        aulog.info(cmd)
        number = r'\d+'
        cnumber = re.compile(number)
        sleep(2)
        host.sendline()
        try:
            host.expect_exact(['#'],searchwindowsize=1000)
        except Exception,e:
            aulog.error("ERROR:failed when expecting # before doing act operation\n")
            output = str(type(e))
            aulog.error(output + "\n")


        host.sendline(cmd)
        try:
            index = host.expect(['Install operation \d+',],timeout=90,searchwindowsize=1000)
            string = host.after
            is_number = re.findall(cnumber,string)
            if is_number:
                self.install_oper_id = is_number[0]
                aulog.debug("Started install operation %s "%(is_number))
        except pexpect.EOF:
            aulog.error("EOF occurred while expecting LOGIN PROMPT\n %s"%host.before)
            retval = -1

        except pexpect.TIMEOUT:
            aulog.debug(cmd)
            aulog.error("TIMEOUT occurred while expecting LOGIN PROMPT\n %s"%host.before)
            retval = -1

        return int(retval)


    def start(self,**kwargs):
        """
        Start the plugin

        Return False if the plugin has found a fatal error, True otherwise.
        """
        retval = 0
        self.prompt = kwargs['prompt']
        if (kwargs.has_key('session')):
            host = kwargs['session']
        else:
            aulog.error("FATAL ERROR: session details not provided\n")
            retval = -1

        #  Be at # prompt in begining
        try :
            status = host.expect_exact( [INVALID_INPUT,self.prompt, MORE, PROMPT, EOF], timeout = 5)
        except :
            aulog.debug("Timed out in install_act plugin, while expecting prompt at entry")

        if (retval == 0):
            retval = self.install_act(host,kwargs)
            if retval == SKIPPED :
                return SUCCESS 
        if (retval == 0):
            restart_type = self.watch_operation(host)
        return int(restart_type )

    def stop(self):
        """
        Stops the plugin (and prepares for deallocation)
        """
        pass



