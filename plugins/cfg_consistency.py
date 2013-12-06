#!/pkg/bin/python
import os
import sys
import commands


class IPlugin:
    """
    ASR9k Post-upgrade check
    This pluging checks states of all nodes
    """
    plugin_name = "Config consistency check"
    plugin_type = "PostUpgrade"
    plugin_version     = "1.0.0"

    def start(self, **kwargs):
        """
        Start the plugin
        Return -1 if the plugin has found a fatal error, 0 otherwise.
        """
        print "executing the checks" 
        #open a file to save output
        my_logfile = "/tmp/output.txt"
        fd_log = open(my_logfile,"w")
        host = kwargs['session']
 
        #n_blank_count = 0
 
        #1. show platform
        #2. show redundancy
 
        #3. install commit
 
        host.sendline("run instcmd install commit -A")
        try :
            status = host.expect_exact( [INVALID_INPUT, MORE, PROMPT,LOGIN_PROMPT_ERR, EOF], timeout=20)
            print "..status",status
        except :
            #print " Timed out ...",host.before
            print " success"
            #print " After .....shiv",host.after
        output=""
        output = host.before.split("\n")

        print output
        #fd_log.write(output) 
        fd_log.close()
        return 0
        #4. show install active/inactive/committed summary
 
        #5. Show configuration failed startup
 
        cmd = "cfgmgr_show_failed -a"
        status,output = commands.getstatusoutput(cmd)
        if status != 0:
            return -1
        #fd_log = open(my_logfile,"w")
        #fd_log.write(output);
 
        #with open('/tmp/output.txt') as infp:
            #for line in infp:
               #if line.strip():
                  #non_blank_count += 1
        #if (non_blank_count > 1):
            #return -1
        #fd_log.close()

        #6. Clear config inconsistency

        #7. install verify package / install verify package repair

        #8. Cfs check

        cmd = "cfgmgr_cfs_check -a"
        status,output = commands.getstatusoutput(cmd)
        if status != 0:
            return -1
        #9. mirror location 0/RSP0/CPU0 disk0:disk1:
        return 0

    def stop(self):
        """
        Stops the plugin (and prepares for deallocation)
        """
        pass

def main():
    print "started executing ...pre_upgrade_checks_45 ... "
    up = IPlugin()
    up.start()
if __name__ == '__main__':
    main()

