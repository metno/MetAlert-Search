import os
import sys
import getopt

from ma_search.data import Data


def ingestCap(sysArgs):
    """Parse command line, parse CAP files given in folder or as single
    file
    """

    # Valid Input Options
    shortOpt = "hro"
    longOpt  = [
        "help",
        "recursive",
        "overwrite",
    ]

    helpMsg = (
        "Usage:\n"
        " -h, --help      Print this message.\n"
        " -r, --recursive Toggles wether to parse sub-directories\n"
        " -o, --overwrite Overwrite entries with matching identifier\n"
    )

    try:
        inOpts, inRemain = getopt.getopt(sysArgs, shortOpt, longOpt)
    except getopt.GetoptError as E:
        print(helpMsg)
        print("ERROR: %s" % str(E))
        sys.exit(1)

    data = Data()
    recursive = False
    replace = False

    for inOpt, _ in inOpts:
        if inOpt in ("-h", "--help"):
            print(helpMsg)
            sys.exit()
        elif inOpt in ("-r", "--recursive"):
            recursive = True
        elif inOpt in ("-o", "--overwrite"):
            replace = True

    def ingestFile(fileName):
        if os.path.isfile(fileName) and fileName.endswith(".xml"):
            data.ingestAlertFile(fileName, doReplace=replace)

    for pathArg in inRemain:
        if os.path.isdir(pathArg):
            if recursive:
                for root, _, filenames in os.walk(pathArg):
                    for fileName in filenames:
                        ingestFile(os.path.join(root, fileName))
            elif not recursive:
                for fileName in os.listdir(pathArg):
                    ingestFile(os.path.join(pathArg, fileName))
        else:
            ingestFile(pathArg)
