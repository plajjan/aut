#! /usr/bin/python
# Copyright (c) 2011 by cisco Systems, Inc.
# All rights reserved.

"""
 Installation script for accelerated upgrade
"""
import os
from distutils.core import setup
from lib import version
import sys

NAME = 'acceleratedupgrade'


def main():
    setup(name=NAME,
        version=version.version,
        description='Accelerated Upgrade tool distribution',
        author='Cisco Systems',
        py_modules = ['lib',
                      'lib.parser',
                      'lib.global_constants',
                      'lib.plugins_manager',
                      'lib.version',
                      'plugins', 
                      'plugins.cfg_backup', 
                      'plugins.cfg_consistency', 
                      'plugins.cmd_snapshot_backup', 
                      'plugins.disk_space_plugin', 
                      'plugins.install_act', 
                      'plugins.install_add', 
                      'plugins.node_status', 
                      'plugins.package_check_plugin_act', 
                      'plugins.package_check_plugin_commited', 
                      'plugins.package_check_plugin_inact', 
                      'plugins.ping_test', 
                      'plugins.redundancy_check', 
                      'plugins.version_check', 
                     ],
        url = 'https://sourceforge.net/p/acceleratedupgrade',
        scripts=['accelerated_upgrade'],
        data_files=['./README',],
    )
    

if __name__ == '__main__':
    main()

