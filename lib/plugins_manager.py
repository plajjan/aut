#!/router/bin/python-2.7.4

#import logging
#import logging.handlers

#==============================================================
# plugins_manager.py - plugin manager
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
import imp
from time import sleep
import sys
from lib.global_constants import *

LOAD_AFTER_PLUGIN = 'load_after_plugin'
PLUGIN_PATH=""
SUCCESS = 0
IGNORE  = 2

plugins_list = [
#### Pre upgrade plugins ####
   "plugins/node_status.py",
   "plugins/ping_test.py",
   "plugins/disk_space_plugin.py",
   "plugins/package_check_plugin_act.py",
   "plugins/package_check_plugin_inact.py",
   "plugins/package_check_plugin_commited.py",
   "plugins/redundancy_check.py",
   "plugins/cfg_backup.py",
   "plugins/cmd_snapshot_backup.py",
   "plugins/install_add.py",
#### Upgrade plugins #### 
   "plugins/install_act.py"
#### Post Upgrade plugins ####
]

class PluginError(Exception):
    pass


class IPlugin(object):
    """
    A plugin template 
    """
    plugin_name       = "Plugin_Name"
    plugin_type       = "PreUpgrade|PostUpgrade|Upgrade"
    plugin_version    = "0.1"
    def start(self,**kwargs):
        """
        Start the plugin

        Return False if the plugin has found a fatal error, True otherwise.
        """
        pass

    def stop(self):
        """
        Stops the plugin (and prepares for deallocation)
        """
        pass

# This is basic class and all plugins should have 
# start() functions will be called  to invoke this plugin will all the options 
# received on CLI , which can be used by plugins if needed.
KeyPluginClass = "IPlugin" 


class PluginsManager(object):
    """
    The plugins manager keeps a list of plugins instances
    """

    plugins = []
    active  = []

    def __init__(self,
                 directory = None):
        self.directory = directory
        #self.acc_upgrade_logger = init_logging()

    def VerifyClass(self,class_a,class_b):
        """ Ensure that all plugins have Iplugin class and  have defined minimum attribute 

        Al attributes / methos in IPlugin class above are mandatory for each plugins
        e.g. :
            name       = " Name of the Plugin " 
            short_name = "ShortName" # this name will be used in logs to identify from where a log is comming
            version    = "Version" # A X.Y format version used
            method "start" # This will be starting point of this plugin.

        Optional Attributes :    
            load_after_plugin  = "ShortName of another Plugin" # This Plugin to be started after the given plugin 
                                                          # If the given plugin does not exist , this attribute 
                                                          # is ignored

        """
        #members_a = [ a[0] for a in inspect.getmembers(class_a) if a[0][0] != '_' ]
        #members_b = [ a[0] for a in inspect.getmembers(class_b) if a[0][0] != '_' ]
        #not_in_b  = [ a for a in members_a if a not in members_b ] 

        #if not_in_b :
        #    #self.acc_upgrade_logger.error("Mandatory attribute %s not found"%("_".join(not_in_b)))
        #    print >> sys.stderr,"Mandatory attribute %s not found"%("_".join(not_in_b))
        #    return -1
        return 

    def load_plugins(self,
                     **kwargs):

        #self.acc_upgrade_logger.info("Checking plugins %s" % " ".join(plugins_list))
        #print >> sys.stdout,"Checking plugins %s" % " ".join(plugins_list)
        plugins =  [os.path.abspath(p) for p in plugins_list if p]
        self.stop()
        del self.plugins[:]
        del self.active[:]    

        for p in plugins:
            loaded = False
            directory = os.path.dirname(p)
            if not directory in sys.path:
                sys.path.append(directory)
            try:
                name = p.split("/")[-1].split(".py")[0]
                #self.acc_upgrade_logger.debug("... inspecting '%s'", name)
                #print >> sys.stdout,"... inspecting '%s'", name
                f, file, desc = imp.find_module(name, [directory])
                plugin = __import__(name)

                #for k,v in inspect.getmembers(plugin):
                #    if k == KeyPluginClass :
                #        try:
                #            assert (not self.VerifyClass(IPlugin, v))
                #        except NotImplementedError, e:
                #            #self.acc_upgrade_logger.error("Broken implementation of : %s" % name)
                #            print >> sys.stdout,"Broken implementation of : %s" % name
                #            continue
                #        instance = v()
                #        #self.acc_upgrade_logger.info("Adding an instance of %s" % k)
                #        print >> sys.stdout,"Adding an instance of %s" % k
                #        self.plugins.append((k, instance))
                #        loaded = True
                instance = plugin.IPlugin()
                self.plugins.append((IPlugin, instance))
                loaded = True
           
                if not loaded :
                    self.acc_upgrade_logger.debug("Plugin %s is not loaded due to error(s) in its format.", name)

            except Exception as e:
                #self.acc_upgrade_logger.error("failed to load: %s" % str(p))
                print >> sys.stderr,"failed to load: %s" % str(p)
                #self.acc_upgrade_logger.error("error: %s " % str(e))
                print >> sys.stderr,"error: %s " % str(e)

        return len(self.plugins)

    def check_and_run(self, ptype, option):

        valid_plugins="PreUpgrade Upgrade PostUpgrade"

        if option.preupgradeset:
           if ptype[0] == "PreUpgrade" or ptype[1] == "PreUpgrade":
              return 0
           elif ptype == "PreUpgrade":
                return 0
           else:
               return 1
        if option.upgradeset:
           if ptype[0] == "Upgrade" or ptype[1] == "Upgrade":
              return 0
           elif ptype == "Upgrade":
                return 0
           else:
               return 1
        if option.postupgradeset:
           if ptype[0] == "PostUpgrade" or ptype[1] == "PostUpgrade":
              return 0
           elif ptype =="PostUpgrade":
                return 0
           else:
               return 1
        p=""
        p=ptype[0]
        if len(p)> 1:
           if valid_plugins.find(ptype[0]) == -1:
              return 1 
        else:
            p=ptype
            if valid_plugins.find(p) == -1:
               return 1;
            else:
               return 0
        
    def start(self, **kwargs):
        """
        Starts all the plugins in order

        @throw PluginError when a plugin could not be initialized
        """
        if len(self.plugins) == 0:
            self.sequence_plugins()
            self.load_plugins()
        # holds status of all plugins we run
        results={}
        # common parameters we pass to all plugins
        host = kwargs['session']
        option = kwargs['options']
        kwargs['results']= results
        plugin_type =""

        if option.preupgradeset:
           plugin_type = "PreUpgrade"
           if option.upgradeset:
               plugin_type =""
        elif option.postupgradeset:
              plugin_type="PostUpgrade"
        elif option.upgradeset:
              plugin_type="Upgrade"
            

        host.sendline("terminal len 0")
        try :
           status = host.expect_exact( [INVALID_INPUT, MORE, "#",
                                         LOGIN_PROMPT_ERR, EOF], timeout=20) 
        except:
           pass
        try :
          status=1
          status = host.expect_exact( ['#'], timeout=20)
        except:
          pass

        #print "Setting term len to zero", status 
        pno = 1;
        for (name, i) in self.plugins:
            if self.check_and_run(i.plugin_type, option):
               continue
            print "++++"*5+ bcolors.HEADER +" (%d) (%s) Check "%(pno, i.plugin_type)+ bcolors.ENDC+"++++"*5
            print >> sys.stdout,"\nStarting => %s...."%(i.plugin_name)
            status = i.start(**kwargs)
            return_status = {i.plugin_name:status}
            results.update(return_status)
             
            if status == SUCCESS or status == SYSTEM_RELOADED or status == INSTALL_METHOD_PROCESS_RESTART :
                print >> sys.stdout,bcolors.OKGREEN +"\nPassed => %s\n"%(i.plugin_name)+ bcolors.ENDC
            elif status == IGNORE:
                  print >> sys.stdout,bcolors.WARNING +"\nIgnoring => %s\n"%(i.plugin_name)+ bcolors.ENDC
            else :
                print >> sys.stderr,bcolors.FAIL+"\nFailed => %s\n"%(i.plugin_name)+ bcolors.ENDC
                if not option.ignore_fail:
                    sys.exit(0)

            self.active.append((name, i))
            pno = pno + 1
            sleep(1)

        if pno == 1:
              print bcolors.HEADER + "++++"*5+" Notice "+"++++"*5 + bcolors.ENDC
              print bcolors.WARNING +"Didn't find any plugins of type ** %s **"%(plugin_type)

        print bcolors.HEADER + "++++"*5+" Done "+"++++"*5 + bcolors.ENDC
        return status
        

    def stop(self):
        for (name, i) in self.active:
            i.stop()


def main(args):
   #sys.exit(args)
   kwargs = {}
   if len(args) > 0 :
       kwargs['repository'] = args[0]
   if len(args) > 1 :
       kwargs['pkg-file-list'] = args[1]
   if len(args) > 2 :
       kwargs['pre_upgrade_check'] = args[2]
   if len(args) > 3 :
       kwargs['post_upgrade_check'] = args[3]
   PluginManager = PluginsManager()
   plugins = PluginManager.load_plugins()
   if plugins :
       PluginManager.start(**kwargs)


if __name__ == '__main__':
    args = ['tftp://202.153.144.25/auto/tftp-blr-users3/mahessin/temp','tmp']
    main(args)

