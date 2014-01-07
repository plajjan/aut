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
from lib import aulog
import inspect

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
   "plugins/install_turbo.py",
   "plugins/install_add.py",
#### Upgrade plugins #### 
   "plugins/install_act.py"
#### Post Upgrade plugins ####
]

# This is basic class and all plugins should have 
# start() functions will be called  to invoke this plugin will all the options 
# received on CLI , which can be used by plugins if needed.
KeyPluginClass = "IPlugin" 

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


class PluginsManager(object):
    """
    The plugins manager keeps a list of plugins instances
    """

    plugins = []
    active  = []

    def __init__(self, directory = None):
        self.directory = directory

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
        members_a = [ a[0] for a in inspect.getmembers(class_a) if a[0][0] != '_' ]
        members_b = [ a[0] for a in inspect.getmembers(class_b) if a[0][0] != '_' ]
        not_in_b  = [ a for a in members_a if a not in members_b ] 

        if not_in_b :
            aulog.error("Mandatory attribute %s not found"%("_".join(not_in_b)))
        return 

    def load_plugins(self, **kwargs):

        aulog.debug("Checking plugins :")
        for p in plugins_list :
            aulog.debug("\t%s" % (p))
        plugins =  [os.path.abspath(p) for p in plugins_list if p]

        # Stop execution of any plugins of running 
        self.stop()
        del self.plugins[:]
        del self.active[:]    

        for p in plugins:
            loaded = False
            directory = os.path.dirname(p)
            if not directory in sys.path:
                sys.path.append(directory)


            name = p.split("/")[-1].split(".py")[0]
            aulog.debug("... inspecting '%s'"% name)
            f, file, desc = imp.find_module(name, [directory])
            plugin = __import__(name)


            try:
                name = p.split("/")[-1].split(".py")[0]
                aulog.debug("... inspecting '%s'"% name)
                f, file, desc = imp.find_module(name, [directory])
                plugin = __import__(name)

                for k,v in inspect.getmembers(plugin):
                    if k == KeyPluginClass :
                        try:
                            assert (not self.VerifyClass(IPlugin, v))
                        except NotImplementedError, e:
                            aulog.warning("Broken implementation of : %s" % name)
                            continue
                        instance = v()
                        aulog.debug("Adding an instance of %s" % (k,))
                        self.plugins.append((k, instance))
                        loaded = True
                #instance = plugin.IPlugin()
                #self.plugins.append((IPlugin, instance))
                #loaded = True
           
                if not loaded :
                    aulog.debug("Plugin %s is not loaded due to error(s) in its format.", name)

            except Exception as e:
                aulog.error("failed to load: %s" % str(p))
                aulog.error("error: %s " % str(e))

        return len(self.plugins)

    def check_and_run(self, ptype, option):
    
        # upported_plugin_types is defined in global_constants
        if option.preupgradeset:
           if ptype == PRE_UPGRADE or ptype == PRE_UPGRADE_AND_POST_UPGRADE:
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
           elif ptype == POST_UPGRADE :
                return 0
           else:
               return 1
        p=ptype[0]
        if len(p)> 1:
           if upported_plugin_types.find(ptype[0]) == -1:
              return 1 
        else:
            p=ptype
            if p in supported_plugin_types :
               return 0;
            else:
               return 1
        
    def sequence_plugins(self, option):
        i = 0 
        preupgrade_plugins = []
        upgrade_plugins = []
        postupgrade_plugins = []

        for (name,plugin) in self.plugins :
            if self.check_and_run(plugin.plugin_type, option) == UPGRADE :
                 upgrade_plugins.append((name,plugin))
            elif self.check_and_run(plugin.plugin_type, option) == PRE_UPGRADE :
                 preupgrade_plugins.append((name,plugin))
            if self.check_and_run(plugin.plugin_type, option) == POST_UPGRADE :
                 postupgrade_plugins.append((name,plugin))
            if self.check_and_run(plugin.plugin_type, option) == PRE_UPGRADE_AND_UPGRADE :
                 preupgrade_plugins.append((name,plugin))
                 upgrade_plugins.append((name,plugin))
            if self.check_and_run(plugin.plugin_type, option) == PRE_UPGRADE_AND_POST_UPGRADE :
                 upgrade_plugins.append((name,plugin))

    def start(self, **kwargs):
        """
        Starts all the plugins in order

        @throw PluginError when a plugin could not be initialized
        """
        # holds status of all plugins we run
        results={}

        # common parameters we pass to all plugins
        host = kwargs['session']
        option = kwargs['options']
        kwargs['results']= results
        plugin_type =""

        if len(self.plugins) != 0:
            self.sequence_plugins(option)
            #self.load_plugins()



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
            aulog.info("++++"*5+ bcolors.HEADER +" (%d) (%s) Check "%(pno, i.plugin_type)+ bcolors.ENDC+"++++"*5)
            aulog.info("\nStarting => %s...."%(i.plugin_name))
            status = i.start(**kwargs)
            return_status = {i.plugin_name:status}
            results.update(return_status)
             
            if status == SUCCESS or status == SYSTEM_RELOADED or status == INSTALL_METHOD_PROCESS_RESTART :
                aulog.info(bcolors.OKGREEN +"\nPassed => %s\n"%(i.plugin_name)+ bcolors.ENDC)
            elif status == IGNORE:
                aulog.info(bcolors.WARNING +"\nIgnoring => %s\n"%(i.plugin_name)+ bcolors.ENDC)
            else :
                if not option.ignore_fail:
                    aulog.error(bcolors.FAIL+"\nFailed => %s\n"%(i.plugin_name)+ bcolors.ENDC)
                else :
                    aulog.ignore_error(bcolors.FAIL+"\nFailed => %s\n"%(i.plugin_name)+ bcolors.ENDC)

            self.active.append((name, i))
            pno = pno + 1
            sleep(1)

        if pno == 1:
              aulog.info(bcolors.HEADER + "++++"*5+" Notice "+"++++"*5 + bcolors.ENDC)
              aulog.info(bcolors.WARNING +"Didn't find any plugins of type ** %s **"%(plugin_type))

        aulog.info(bcolors.HEADER + "++++"*5+" Done "+"++++"*5 + bcolors.ENDC)
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

