import os
import re
import inspect
import pprint
import sys
from lib import aulog

PIE = "pie"
ACTIVE = "active"
INACTIVE = "inactive"
COMMITTED = "committed"
ACTIVE_STR = "Active Packages:"
INACTIVE_STR = "Inactive Packages:"

pkg_name = "asr9k-mgbl-px.pie-4.2.3"
nn = "disk0:asr9k-mini-px-4.2.3"

class PackageClass(object):
    def __init__(self):
        # Platform or domain
        self.platform = None
        # Packge name
        self.pkg = None
        # Architecture
        self.arch = None
        # Release version
        self.version = None
        self.subversion = None
        # Package format
        self.format = None
        #Patch/maintenece version
        self.patch_ver = None
        #Requires or depends on
        self.requires = None
        #Supersedes or overrides
        self.supersedes = None
        #Partition where package exists
        self.partition= None
        

class NewPackage():
    def __init__(self, pkg_lst_file=None):
        self.inputfile = pkg_lst_file
        self.pkg_list = []
        if pkg_lst_file :
            self.inputfile = pkg_lst_file
            self.update_pkgs()
  
    def update_pkgs(self):
        if os.path.exists(self.inputfile):
            fd = open(self.inputfile,"r")

            for line in fd.readlines() :
                pkg_name = line.strip()
                pkg = self.validate_offbox_xrpie_pkg(pkg_name)
                if not pkg :
                    pkg = self.validate_xrrpm_pkg(pkg_name)
                if not pkg:
                    #Skip comments and unsupported pkg types
                    pass
                if pkg :
                    self.pkg_list.append(pkg)
        fd.close()
      
    def validate_offbox_xrpie_pkg(self,pkg):
        #asr9k-px-4.3.2.CSCuj61599.pie
        #asr9k-mpls-px.pie-4.3.2
        pkg_expr_2pkg = re.compile(r'(?P<PLATFORM>\w+)-(?P<PKGNAME>\w+)-(?P<SUBPKGNAME>\w+)-(?P<ARCH>p\w+)\.(?P<PKGFORMAT>\w+)-(?P<VERSION>\d+\.\d+\.\d+)')
        pkg_expr = re.compile(r'(?P<PLATFORM>\w+)-(?P<PKGNAME>\w+)-(?P<ARCH>p\w+)\.(?P<PKGFORMAT>\w+)-(?P<VERSION>\d+\.\d+\.\d+)')
        smu_expr = re.compile(r'(?P<PLATFORM>\w+)-(?P<ARCH>\w+)-(?P<VERSION>\d+\.\d+\.\d+)\.(?P<PKGNAME>\w+)\.(?P<PKGFORMAT>\w+)')
        smu_expr2 = re.compile(r'(?P<PLATFORM>\w+)-(?P<ARCH>\w+)-(?P<VERSION>\d+\.\d+\.\d+)\.(?P<PKGNAME>\w+)-(?P<SMUVERSION>\d+\.\d+\.\d+)\.(?P<PKGFORMAT>\w+)')
        pkgobj = PackageClass()
        p = pkg_expr_2pkg.search(pkg)
        if not p  :
            p = pkg_expr.search(pkg)
        if not p  :
            p = smu_expr.search(pkg)
        if not p  :
            p = smu_expr2.search(pkg)
        if p :
            if p.group("PKGFORMAT") == PIE :
                pkgobj.platform = p.group("PLATFORM")
                if p.groupdict().has_key("SUBPKGNAME"):
                    packagename = p.group("PKGNAME") + "-" + p.group("SUBPKGNAME")
                else :
                    packagename = p.group("PKGNAME")
                pkgobj.pkg = packagename
                pkgobj.arch = p.group("ARCH")
                pkgobj.format = p.group("PKGFORMAT")
                pkgobj.version = p.group("VERSION")
                return pkgobj

    def validate_xrrpm_pkg(self,pkg):
        pass
    

class OnboxPackage():
    def __init__(self, pkg_lst_file=None,pkg_state=None):
        self.inputfile = None
        self.pkg_list = []
        self.pkg_state = pkg_state
        if pkg_lst_file :
            self.inputfile = pkg_lst_file
            self.update_pkgs()
  
    def update_pkgs(self):
        if os.path.exists(self.inputfile):
            fd = open(self.inputfile,"r")
            data = fd.readlines()
            fd.close()
        else :
            data = self.inputfile.split("\n")


        start_pkg = False    
        for line in data:
            if line.find(self.pkg_state) < 0 and not start_pkg :
                continue
            elif not start_pkg :
                start_pkg = True

            pkg_name = line.strip()
            pkg = self.validate_xrpie_pkg(pkg_name)
            if not pkg :
                pkg = self.validate_xrrpm_pkg(pkg_name)
            if pkg :
                self.pkg_list.append(pkg)
      

    def validate_xrpie_pkg(self,pkg):
        #disk0:asr9k-mini-px-4.3.2
        #asr9k-px-4.2.3.CSCue60194-1.0.0
        pkg_expr_2pkg = re.compile(r'(?P<DISK>\w+):(?P<PLATFORM>\w+)-(?P<SUBPKGNAME>\w+)-(?P<PKGNAME>\w+)-(?P<ARCH>p\w+)-(?P<VERSION>\d+\.\d+\.\d+)')
        pkg_expr = re.compile(r'(?P<DISK>\w+):(?P<PLATFORM>\w+)-(?P<PKGNAME>\w+)-(?P<ARCH>p\w+)-(?P<VERSION>\d+\.\d+\.\d+)')
        smu_expr = re.compile(r'(?P<DISK>\w+):(?P<PLATFORM>\w+)-(?P<ARCH>p\w+)-(?P<VERSION>\d+\.\d+\.\d+)\.(?P<PKGNAME>\w+)-(?P<SUBVERSION>\d+\.\d+\.\d+)')
        pkgobj = PackageClass()

        p = pkg_expr_2pkg.search(pkg)
        if not p  :
            p = pkg_expr.search(pkg)
        if not p  :
            p = smu_expr.search(pkg)
        if p :
            pkgobj.platform = p.group("PLATFORM")
            if p.groupdict().has_key("SUBPKGNAME"):
                packagename = p.group("PKGNAME") + "-" + p.group("SUBPKGNAME")
            else :
                packagename = p.group("PKGNAME")
            pkgobj.pkg = packagename
            pkgobj.partition = p.group("DISK")
            pkgobj.arch = p.group("ARCH")
            pkgobj.version = p.group("VERSION")
            if p.groupdict().has_key("SUBVERSION"):
                pkgobj.subversion = p.group("SUBVERSION")
            return pkgobj

    def validate_xrrpm_pkg(self,pkg):
        pass

# Packages in list1 but not in list 2
def missing_pkgs(list1, list2) :
    missing_lst = []
    for pk1 in list1 :
        missing = True
        for pk2 in list2 :
            if pk1.pkg == pk2.pkg and pk1.version == pk2.version :
                missing = False
        if missing :
            missing_lst.append(pk1)
    return missing_lst

# Packages in list2 but not in list 1
def extra_pkgs(list1, list2) :
    extra_lst = []
    for pk2 in list2 :
        extra = True
        for pk1 in list1 :
            if pk1.pkg == pk2.pkg and pk1.version == pk2.version :
                extra = False
        if extra :
            extra_lst.append(pk2)
    return extra_lst

def pkg_tobe_activated(added_pkgs,inactive_pkgs,active_pkgs):
    tobe_added = []
    # All added packages should either be active or inactive
    
    # Get the added package which is not in inactive state
    missing_in_inactive = missing_pkgs(added_pkgs,inactive_pkgs)

    # If package to be activated is not in inactive state , see if that's already active
    if missing_in_inactive :
        missing_in_inactive = missing_pkgs(missing_in_inactive,active_pkgs)

    # For debug purpose only 
    aulog.debug("Package to be activated")
    for i in added_pkgs :
        aulog.debug(i.pkg)
    aulog.debug("Package inactive state")
    for i in inactive_pkgs :
        aulog.debug(i.pkg)
    aulog.debug("Package active state")
    for i in added_pkgs :
        aulog.debug(i.pkg)

    # End of debug

    if not missing_in_inactive :
        for pk1 in added_pkgs:
            for pk2 in inactive_pkgs:
                if pk1.pkg == pk2.pkg and pk1.version == pk2.version :
                    if len(pk2.pkg) == 10 and pk2.pkg[:3] == "CSC" or pk2.pkg[:2] == "sp" or pk2.pkg[:2] == 'fp':
                        # It's a SMU format is
                        #disk0:asr9k-px-4.3.2.CSCuj61599-1.0.0
                        pkg = "%s:%s-%s-%s.%s-%s"%(pk2.partition,pk2.platform,pk2.arch,
                            pk2.version,pk2.pkg,"1.0.0")
                    else :
                        pkg = "%s:%s-%s-%s-%s"%(pk2.partition,pk2.platform,pk2.pkg,pk2.arch,
                            pk2.version)
                    tobe_added.append(pkg)
    return tobe_added

def print_packages(list):
    for pkg in list :
        attr = inspect.getmembers(pkg, lambda a:not(inspect.isroutine(a)))
        return ([a for a in attr if not(a[0].startswith('__') \
            and a[0].endswith('__'))])



