
import logging
import sys
import time
import os
import shutil
import glob




# Implements the functions for logging and error messaging from AU.
# Its completely based upon python logging module.

# Toplevel program should call aulog.initialize_logging()
# after that each AULog.<function> writes the corresponding message
# in to the log file.

# By default a message in the log file looks like 
# ERROR:AU:AU_ERROR_2: nova-infra target is not defined for arch=ppc varaint=None
# DEBUG:AU:build-nova-base-ppc: removing config-nova-base-ppc from dependency list


# Logging levels... 
DEBUG    = 'debug'
INFO     = 'info'
WARNING  = 'warning'
ERROR    = 'error'
CRITICAL = 'critical'


# default logfile
AULOG = "au.log"
SAVEDLOGDIR = 'oldlogs'

# start time, 
start_time = time.time()

# Mbs logging object.
au_logger      = None

# print colored messages if the output goes to a termianl.
# if we are writing to a file its just normal.
term = None

def initialize_logging(logfile=AULOG, verbose=DEBUG, cmd=sys.argv, color=True, logger_name=None):
    """ Function to intialize logging for AU. 
        This function should be called first before using any function of
        aulog """

    global au_logger
    save(logfile)
    if au_logger is not None:
        debug("Ignoring re-initialize the logging %s" % cmd)
        return

    # we will have only two logging levels. with -v option we log all messages
    # without -v option, we dont log debugging messages.
    if verbose or os.environ.get(auenv.AU_DEBUG):
        s_level = DEBUG
    else:   
        s_level = INFO

    LEVELS = { 
              DEBUG    : logging.DEBUG,
              INFO     : logging.INFO,
              WARNING  : logging.WARNING,
              ERROR    : logging.ERROR,
              CRITICAL : logging.CRITICAL
            }

    if not LEVELS.has_key(s_level):
        error("%s: Invalid AU logging level option" % s_level ,
                     AUError.INVALID_AU_LOGGING_LEVEL)

    if logger_name is None:
        logger_name=get_auid()

    level = LEVELS[s_level]
    logging.basicConfig(filename=logfile,level=level)
    au_logger  = logging.getLogger(logger_name)

    if au_logger and cmd:
        au_logger.info("COMMAND: %s" % ' '.join(cmd) )



def end_logging(msg):
    """ print the end time and msg user given """

    info("Execution time: %s secs"%(elapsed_time()))
    marker = "--------------------- End of execution ------------------------\n"
    au_logger.info("\n" + marker + marker )



  

# There are five logging functions (logging levels).
# 1. debug
# 2. info
# 3. warning
# 4. error
# 5. internal_error

# user can set the level of logging in intialize_logging function. 
# debug > info > warning > error > internal_error
# if logging level is set to debug all the messages will go to au.log
# if the logging level is set to warning only, warning, error, internal_error
# messages go to the log.


# Note: warning, error, internal_error messages always goes to STDERR 
# irrespective of whether they are going to be logged to au.log to or not.
# info messages always goes to STDOUT whether they are not going be logged/not.


def internal_error(str):
    """ internal error causes the AU to exit """ 

    # When internal error is caused the message AU_INTERNAL_ERROR goes
    # to the STDERR 
    # then an exception AUInternalError is raised and the stack trace is
    # copied to the au.log for the debugging. 
    # If there is no logging then stack trace is printed on to the screen.

    errmsg = "AU_INTERNAL_ERROR: %s" % str
    if term:
        print >> sys.stderr, term.RED + errmsg + term.NORMAL
    else:
        print errmsg

    end_logging("Exiting because of the internal error in AU code.. ")


# error function takes two arguments 
# str: err description and
# err: AUError object. 
#      Each error from AU must be defined AUError module

# An AU error message looks like this
# ERROR: No au sub-command passed
# AU_ERROR_3: Invalid AU sub command
# ERROR: is the actuall error reported (str)
# AU_ERROR_3: id for the au error databse
# followed by a help message on the AU error.

def error(str):
    """ AU Error, makes the au to exit. """

    errmsg = "ERROR: %s\n" % (str)
    if term:
        print >> sys.stderr, term.RED + errmsg + term.NORMAL
    else:
        print >> sys.stderr, str

    if au_logger is not None:
        au_logger.error(str)

    end_logging("Failed: %s" % (str))
    sys.exit(str)


def warning(str):
    """ AU Warning, prints the message on STDERR but wont abort AU """

    errmsg = "WARNING: %s\n" % (str)

    if term:
        print >> sys.stderr, term.MAGENTA + errmsg + term.NORMAL
    else:
        print >> sys.stderr, errmsg

    if au_logger is not None:
        au_logger.warning(errmsg)


def info(infomsg, color=None):
    """ info messages, messages that goes to STDOUT and au.log depending
        upon the logging """

    if term and color:
        print getattr(term, color) + infomsg + term.NORMAL
    else:
        print infomsg

    if au_logger is not None:
        au_logger.info(infomsg)


def debug(debugmsg):
    """ By default debug messages only goes to the au.log 
        except logging is not enabled. """

    if au_logger is not None:
        au_logger.debug(debugmsg)
    else:
        print "DEBUG: %s" % debugmsg
    

def save(logname, savedir=SAVEDLOGDIR):
    """ actually sets a symlink between 
            savedir/logname.AUPID -> logname
        when ever user is over writing the logname, 
        written in savedir/logname.AUPID
        if another process overwrites the log, we will always have the
        copy saved """


    logname = os.path.abspath(logname)
    savedir = os.path.abspath(savedir)

    try:
        if not os.path.isdir(savedir):
            os.makedirs(savedir)
    except OSError:
        error("%s: Cannot create the directory" % (savedir))

    # see first if we have old symlink in the savedir for this logname
    # if so copy the log to the symlink we kept
    for sym_link in glob.glob("%s/.%s.*" % (savedir, os.path.basename(logname))):
        if os.path.islink(sym_link):
            os.remove(sym_link)
            # Allow to save samelog file multiple times
            if os.path.exists(logname):
                log_no = 1
                savelogname = os.path.basename(sym_link).replace('.', '', 1)
                savelog     = os.path.join(savedir, savelogname)
                while os.path.exists(savelog):
                    savelog = os.path.join(savedir, "%s.%s" % (savelogname,log_no))
                    log_no = log_no + 1
                shutil.move(logname, savelog)

    # when ever we are creating a log we also a keep a backup_link symlink  
    # from saved logs dir which identifies which AU proces created that
    # symlink.

    backup_link_name = os.path.join(".%s.%s" % (os.path.basename(logname), get_auid()))
    backup_link = os.path.join(savedir, backup_link_name)
    debug("logname %s backup link %s " % (logname, backup_link))

    # Now set the symlink
    try:
        os.symlink(logname, backup_link)
        debug("Created symlink %s -> %s" % (backup_link, logname))
    except OSError:
        warning("%s -> %s: cannot create the symlink" % (backup_link, logname), 
                            auerror.FILE_IO_ERROR)
        


def elapsed_time():
    """ Report the time taken for execution of AU """
    global start_time

    time_str = ""
    seconds = int(time.time() - start_time)
    hrs   = seconds/3600
    
    if hrs > 0:
        seconds = seconds - 3600 * hrs
        time_str += "%dh " % (hrs)

    mins = seconds/60
    if mins > 0:
        seconds = seconds - 60 * mins
        time_str += "%dm " % (mins)

    time_str += "%d" % (seconds)
    return time_str

   
 
def get_auid():
    """ Returns the unique au id for the process """

    AUID = time.strftime("%Y%m%d-%H%M%S")
    AUID = "%s.%s" % (AUID, os.getpid())
    return AUID


if __name__ == "__main__":
    print "Start"
    initialize_logging('thislog')
    internal_error("Internal error str")
    #error("Fatal error str")
    warning("Warning str")
    info("This is infomsg")
    debug("This is debug debugmsg")
    save("lognamei")
    print elapsed_time()
    print get_auid()
    print "Test Pass"
    end_logging("msg")

