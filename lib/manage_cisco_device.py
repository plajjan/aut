#!/router/bin/python-2.7.4
"""
This is a simple script to connect the ssh tunnel.

"""
import sys
import pexpect
import optparse
import os
import getpass

MAXREAD = 100000
IOS = 'IOS'
IOS_XR = "IOS XR"
WINDOWSIZE = -1
LOGIN_PROMPT = "#"
HOP_LOGIN_PROMPT = "$"
NEWSSHKEY = (r'Are you sure you want to continue connecting (yes/no)?')
PROMPT = (r"\>(\s{0,2})?$|\%(\s{0,2})?$|\$(\s{0,2})?$|\#(\s{0,2})?$")
ROOT_PROMPT = (r"\#")
PERMISSION_DENIED = ".*enied|.*nvalid|.*ailed"
MODULUS_TO_SMALL = "modulus too small"
PROTOCOL_DIFFER = "Protocol major versions differ"
INVALID_INPUT = "Invalid input detected"
HOST_KEY_FAILED = "verification failed"
CONNECTION_REFUSED = "Connection refused"
RESET_BY_PEER = "reset by peer|closed by foreign host"
PASS = "Password:"
PASSWORD = "password:"
FIRST_LOGIN = (r"^]")
USERNAME = "Username: "
MORE = (r"--more--|--More--|^\!")
EOF = pexpect.EOF

def main():
    """
    Main function .
    """
    options = parse_cli()
    if options.login and options.device :
        passwd = get_password(options.login, options.device) 
        command_exec(options.device, options, passwd)
    else:
        print "usage: %s [OPTIONS]" % sys.argv[0]
        os.system("%s --help"%sys.argv[0])

def get_password (user, device): 
    """
    Get the passwrod from user without re-printing .
    """
    pwd = getpass.getpass("Enter password for %s@%s :" % (user, device))
    return pwd

def ssh_login ( host, tunnel, options, passwd ):
    """ Login to linux server using SSH 
    """
    status = 0
    session = "ssh -o PubkeyAuthentication=no -v " + options.login +"@"+host

    print "*******     %s   %s  ****"%(host,session)
    if not tunnel :
        command = pexpect.spawn( session, maxread=MAXREAD, 
            searchwindowsize=WINDOWSIZE )
    else :
        command = tunnel
        command.sendline(session)
    try:
        status = command.expect_exact( [NEWSSHKEY, PASSWORD, 
          MODULUS_TO_SMALL, PROTOCOL_DIFFER, LOGIN_PROMPT, EOF, 
          HOST_KEY_FAILED, CONNECTION_REFUSED, RESET_BY_PEER,], timeout=10)
    except pexpect.TIMEOUT:
        status = -1
        return( status, command )
    print status,command.after,'<=====1' 

    if status == 2:
        session = "ssh -o PubkeyAuthentication=no -1 " + options.login+"@"+host
        command = pexpect.spawn( session, maxread=MAXREAD, 
            searchwindowsize=WINDOWSIZE )
        status = command.expect_exact( [NEWSSHKEY, PASS, MODULUS_TO_SMALL,
            PROTOCOL_DIFFER,  EOF], timeout=10)
    elif status == 0:
        command.sendline("yes")
        status = command.expect_exact( [PASS, PASSWORD, LOGIN_PROMPT, EOF],timeout = 10 )
        if status == 0:
            command.sendline( passwd )
            status = command.expect_exact( [USERNAME, PASS, 
                PERMISSION_DENIED, LOGIN_PROMPT, EOF], timeout = 10)
        if status == 1:
            status = 0
    elif status == 1:
        print "+"*50
        if status == 1:
            command.sendline( passwd )
            try :
                status = command.expect_exact( [USERNAME, PASS,
                    PERMISSION_DENIED, HOP_LOGIN_PROMPT, EOF], timeout = 10)
            except pexpect.TIMEOUT:
                sys.exit(-1)
    return status, command 

def fix_lf_cr(str_in):
    """ OK will fill it in """
    # In general
    return str_in


def command_exec(device_list, options, passwd):
    """ 
    ssh to the device and if there is command specified execute that on all linux devices. 

    """
    auth = 0
    tunnel = None

    device_list = device_list.split(",")
    for dline in device_list :
        auth, host = ssh_login(dline, tunnel, options, passwd)
        tunnel = host 
        print auth,dline
        if auth < 0:
            sys.exit("Authentication failed on host %s , %s" % (dline,tunnel))

    command_list = options.command.split(',')
    for cline in command_list:
        print cline
        if options.command:
            host.sendline( cline )
        try :
            status = host.expect_exact( [INVALID_INPUT, '$', MORE, 
                PROMPT, EOF], timeout = 10)
        except pexpect.TIMEOUT :
            print "Command did not run correctly: %s After = %s , \
                before = %s" % (cline, host.before, host.after)
            sys.exit("o"*80)
        if status == 0:
            print "Invalid input: ", host.before, host.after
            sys.exit(1)
    print host.before #host.before

    host.sendline('quit')
    host.close()

def parse_cli() :           
    """ 
    Parse the CLI options 
    """
    oparser = optparse.OptionParser()
    oparser.add_option('-l', '--login', dest='login', default=None, 
        metavar='Login', help='Your user name to the device')
    oparser.add_option('-d', '--device', dest='device', default=None, 
        metavar='Device', help='The devices through which to create the tunnel')
    oparser.add_option('-c', '--command', dest="command", default=None,
        metavar='DebugCommand', help='Specify command to be executed on device')

    opts, arguments = oparser.parse_args()
    if arguments :
        print arguments 
    return opts

if __name__ == '__main__':
    main()

