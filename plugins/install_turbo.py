# =============================================================================
# install_turbo.py - plugin for install IOS-XR images by turbo boot
#
# Copyright (c)  2014, Cisco Systems
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
import datetime

# wainting long time (5 minutes)
LONG_WAIT = 300

class IPlugin(object):
    """
    A plugin for turbo boot
    This plugin accesses rommon and set rommon variables.
    A router is reloaded a few times.
    Console access is needed.
    This plugin does not work on telnet connection.
    Arguments:
    T.B.D.
    """
    plugin_name     = "Install Turbo"
    plugin_type     = "TURBOBOOT"
    plugin_version  = "1.0.0"
    prompt = "#"

    def get_vm_image(self, pkg_list):
        vm_image = None
        func_name = sys._getframe().f_code.co_name

        status = os.path.exists(pkg_list)
        if not status:
            aulog.error("pkg-file-list not exists")
            return None

        file = open(pkg_list, 'r')

        count = 0
        for line in file:
            match = re.match(r'.+\.vm-.+$|.+\.vm$', line)
            if match:
                count += 1
                vm_image = match.group()

        if count == 0:
            aulog.error("pkg-file-list does not include a vm image name for turbo boot")
        elif count > 1:
            aulog.error("pkg-file-list include more than one vm image name for turbo boot")
            vm_image = None

        return vm_image


    # get the standby rp into rommon mode from the active console
    #
    # This utility does not have Standby RP console access.
    # We can shutdown Standby RP from Active RP console but we cannot restart Standby RP.
    # An operator has to restart Standby RP manually after all processes done
 
    def shutdown_standby_rp(self, host):

        try:
            # get Standby RP
            host.sendline('show platform')
            host.expect(self.prompt)
            lines = host.before.split('\r\n')
            srp = ''
            status = -1
            for line in lines:
                if line.find('Standby') >= 0:
                    match = re.search('\d+/(RSP|RP)\d+/CPU\d+', line)
                    srp = match.group()
                    status = line.find('IOS XR RUN')

            if srp == '':  # No Standby RP, nothing to do
                retval = 0
                return retval, srp

            # check Standby RP state

            if status >= 0:    # Standby RP is in IOS XR RUN state
                cmd = 'admin config-register 0x0 location ' + srp
                host.sendline(cmd)
                host.expect(self.prompt)

                # reload Standby RP
                cmd = 'admin reload location ' + srp
                host.sendline(cmd)
                status = 0
                while status == 0:
                    status = host.expect(['confirm',self.prompt])
                    if status == 0:
                        host.send('\r')

                aulog.info("Standby RP" + srp + "has been shut down for Turboboot.")
                aulog.info("This script cannot restart Standby RP automatically.")
                aulog.info("Please restart Standby RP as follows after all processes done.")
                aulog.info("rommon 1> unset BOOT")
                aulog.info("rommon 2> confreg 0x102")
                aulog.info("rommon 3> sync")
                aulog.info("rommon 4> reset")
                aulog.info(" ")

            else:
                aulog.info("Stabdby RP is not in IOS XR RUN state.")
                aulog.info("You may need to update IOS-XR of Standby RP manually.")
                aulog.info("Besides that, this could interrupt the Turboboot process.")
                aulog.info(" ")

            retval = 0

        except Exception as e:
            aulog.debug(str(e))
            retval = -1

        return retval, srp

    # set 0x0 to confreg and reload the device
    def reload(self, host):
        retval = 0

        host.sendline("admin config-register 0x0")
        try:
            host.expect(self.prompt)
            host.sendline('reload')
            host.expect('confirm')
            host.send('\r')

            # wait for rommon prompt
            # in some cases, multiple confirmations are needed

            status = host.expect(['rommon \w+ >', 'confirm'], timeout = 60)
            if status == 1:
                host.send('\r')
                status = host.expect(['rommon \w+ >', 'confirm'], timeout = 60)
            if status == 1:
                host.send('\r')
                host.expect(['rommon \w+ >'], timeout = 60)

        except Exception as e:
            aulog.debug(str(e))
            retval = -1

        return retval

    # execute turbo boot
    def turbo_boot(self, host, repository, vm_image):
        retval = 0
        PROMPT = 'rommon \w+ >'
        boot_cmd = "boot " + repository + vm_image

        try:
            host.sendline('set')
            status = host.expect(['IP_ADDRESS=(\d+\.\d+\.\d+\.\d+)', PROMPT])
            if status == 1:
                aulog.error("IP_ADDRESS is not set")
                aulog.error("turbo boot needs IP_ADDRESS set at rommon")
                retval = -1
                return retval
            else:
                host.expect(PROMPT)

            host.sendline('unset BOOT')
            host.expect(PROMPT)
            host.sendline('TURBOBOOT=on,disk0')
            host.expect(PROMPT)
            host.sendline('sync')
            host.expect(PROMPT)
            host.sendline('set')
            host.expect(PROMPT)
            sleep(10)
            host.sendline(boot_cmd)

            # waiting for the start of file download
            status = host.expect(['![!\.][!\.][!\.][!\.]',PROMPT], timeout = 180)
            if status == 1:
                # retry once more
                host.sendline(boot_cmd)
                host.expect('![!\.][!\.][!\.][!\.]', timeout = 180)

        except Exception as e:
            aulog.debug(str(e))
            retval = -1

        return retval

    # count the number of cards in valid state
    def count_valid_cards(self, host):
        valid_state = 'IOS XR RUN|PRESENT|READY|UNPOWERED|FAILED|OK|DISABLED'
        retval = 0

        try:
            cmd  = "admin show platform"
            host.sendline(cmd)
            # status = 1 means to hit the line of RP or LC
            status = 1
            card_num = 0
            valid_card_num = 0
            while status == 1:
                status = host.expect([self.prompt, '\d+/\w+/\w+ .+\r'])
                if status == 1:
                    card_num += 1
                    if re.search(valid_state, host.after):
                        valid_card_num += 1
        except Exception as e:
            aulog.debug(cmd)
            aulog.debug(host.before + str(e))
            retval = -1
        return retval, card_num, valid_card_num

    # watch all cards status by show platform command
    def watch_platform(self, host, pre_valid_card_num):
        try:
            # this loop will be existed when all cards are in valid states
            counter = 0
            while counter < 60:
                retval, card_num, valid_card_num = self.count_valid_cards(host)
                if retval == -1:
                    return retval
                elif valid_card_num >= pre_valid_card_num:
                     break
                sleep(60) # wait for one minutes
                counter += 1
            
            if  valid_card_num >= pre_valid_card_num: 
                retval = 0
                aulog.info("All cards seem to reach the valid status")
            else:
                retval = -1
                aulog.error(
                """The number of cars in valid state is less than the number before turboboot.
                   Something woring happens on cards still in invalid state.
                   The number of original valid cards was %s
                   The number of current valid cards is %s
                """%(str(pre_valid_card_num),str(valid_card_num)))
        except Exception as e:
            aulog.debug("In watch_platform : %s "%(str(e)))
            retval = -1

        return retval

    # watch the progress of turbo boot
    def watch_operation(self, host, login, passwd, pre_valid_card_num):
        # pre_valid_card_num is the number of cards in valide state before truboboot
        retval = 0
        TIMEOUT = pexpect.TIMEOUT

        try: 
            while 1:
                status = host.expect(['Press RETURN to get started', TIMEOUT], timeout = LONG_WAIT)
                if status == 1:
                    if len(host.before) > 0:
                        continue
                    else:
                        retval = -1
                        return retval
                else:
                    break

            while 1:
                status = host.expect(['Turboboot completed successfully', TIMEOUT], timeout = LONG_WAIT)
                if status == 1:
                    if len(host.before) > 0:
                        continue
                    else:
                        retval = -1
                        return retval
                else:
                    aulog.info("Turboboot completed successfully")
                    break

            while 1:
                status = host.expect(['Press RETURN to get started', TIMEOUT], timeout = LONG_WAIT)
                if status == 1:
                    if len(host.before) > 0:
                        continue
                    else:
                        retval = -1
                        return retval
                else:
                    aulog.info("2nd boot is in progress")
                    aulog.debug("host.before")
                    break

            # login console
            retry_count = 20
            while retry_count :
                try :
                    host.send('\r')
                    sleep(1)
                    host.expect(USERNAME,timeout=3)
                    host.sendline(login)
                    host.expect(PASS,timeout=3)
                    host.sendline(passwd)
                    status = -1
                    status = host.expect([self.prompt, ':ios#'], timeout=3)
                    break
                except : 
                    aulog.info(host.before)
                    host.expect(".*")
                    retry_count = retry_count - 1

            if status == -1:
                aulog.info("Cannot login after turboboot")
                aulog.debug(host.before)
                retval = -1
                return retval

            elif status == 0:
                aulog.info("Login after turboboot successful..")

            else:
                aulog.info("Login after turboboot successful..")
                aulog.info("But CLI prompt does not chage to " + self.prompt +", yet.")

                # wait for prompt chaging to location:hostname# 
                retry_count = 30
                while retry_count :
                    host.send('\r')
                    status = host.expect([self.prompt, pexpect.TIMEOUT], timeout=60)
                    if status == 0:
                        aulog.info("CLI prompt has chaged to " + self.prompt)
                        break
                    else:
                        aulog.info(host.before[-100:])
                        retry_count -= 1

                if retry_count == 0:
                    aulog.info("CLI prompt does not become " + self.promt)
                    aulog.info("active RP does not avaliable, yet.")
                    retval = -1
                    return retval

            # watch all cards status
            retval = self.watch_platform(host, pre_valid_card_num)
            
        except Exception as e:
            aulog.debug("During watch operation :%s %s"%(host.before,str(e)))
            retval = -1

        return retval

    def start(self, **kwargs):
        # check if Turboboot is requested
        options = kwargs['options']
        self.prompt = kwargs['prompt']
        if (kwargs.has_key('session')):
            host = kwargs['session']
        retval = 0
        if options.turboboot:
            aulog.info("Turboboot is requested and start processing.")
        else:
            aulog.info("Turboboot is not reqested and do nothing.")
            return retval

        # get the image vm name from the package list
        if (kwargs.has_key('pkg-file-list')):
            pkg_list = kwargs['pkg-file-list']
        else:
            aulog.error("List of packages is not provided with -f option")
            retval = -1
            return retval

        vm_image = self.get_vm_image(pkg_list)

        # vm image is a must for turboboot 
        if not vm_image:
            retval = -1
            return retval

        host.sendline()
        # get the session and clear pexpcet buffer       
        try:
            host.expect([self.prompt, pexpect.TIMEOUT], timeout = 3)
        except Exception as e:
            aulog.debug("While buffer cleanup\n%s %s"%(host.before,str(e)))
            retval = -1
            return

        # count the number of cards
        retval, card_num, valid_card_num = self.count_valid_cards(host)
        if retval == -1:
            aulog.error("connot get the number of cards in valid state before turboboot.")
            return retval

        # get the standby rp in rommon
        retval, srp = self.shutdown_standby_rp(host)
        if retval == -1:
            aulog.error("connot get the standby rp into rommon mode before turboboot.")
            return retval        

        # wait for standby becomes rommon mode
        # it may take more than 10 seconds
        sleep(60)

        # reload the devince and get it into rommon mode
        retval = self.reload(host)
        if retval == -1:
            return retval
        aulog.info("Reload the router and get into ROMMON mode.")

        # execute turbo boot
        repository = kwargs['repository']
        retval = self.turbo_boot(host, repository, vm_image)
        if retval == -1:
            return retval
        aulog.info("Start Turboboot.")

        # after tuboboot, standby RP may not be in valid state 
        # because it is in rommon mode.
        # the number of valid cards should be decrement
        if srp != '':
            valid_card_num -= 1

        # monitor the preogress of turbo boot
        login = options.login2
        passwd = options.password2
        if login == None:
            login = options.login
            passwd = options.password
       
        retval = self.watch_operation(host, login, passwd, valid_card_num)

        return retval 

    def stop(self):
        """
        """
        pass

