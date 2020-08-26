#!/usr/bin/env python3

# imports
import argparse

# globals


# classes


# functions
def arguments():
    parser = argparse.ArgumentParser()
##    parser.add_argument('-c', '--config',
##                        action='store',
##                        default='./my.cfg',
##                        help='config file')
    parser.add_argument('-d', '--directory',
                        action='store',
                        default='.',
                        help='folder to copy files to.')
    parser.add_argument('-a','--copy-all',
                        action='store_true',
                        dest='copyall',
                        help='copy all files not just new ones. May delay startup')
    parser.add_argument('-o','--overwrite',
                        action='store_true',
                        help='overwrite local files')
    parser.add_argument('-n', '--no-wait',
                        action='store_false',
                        dest='nowait',
                        help='do not wait for camera connection.')
    parser.add_argument('-v','--verbose',
                        action='store_true')
    parser.add_argument('-D','--debug',
                        action='store_true',
                        help='enable debug output. Imples -v')
    return parser.parse_args()
                        

# main
if __name__ == '__main__':
    print('Nothing to see here, move along.')