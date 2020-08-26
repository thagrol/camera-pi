#!/usr/bin/env python3

# imports
import argparse
import logging
import os
import pyinotify
import shutil

# globals


# classes
class in_event_handler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        logging.debug('writeable file closed %s' % event)
        try:
            if args.move:
                logging.debug('moving %s to %s' %(event.pathname, args.destination))
                shutil.move(event.pathname, args.destination,
                            copy_function=shutil.copy)
            else:
                logging.debug('copying %s to %s' %(event.pathname, args.destination))
                shutil.copy(event.pathname, args.destination)
            if args.sync:
                os.sync()
        except Excption:
            logging.exception('Unable to move/copy %s' %
                              os.path.join(event.path, event.name))
    
    def process_default(self, event):
        logging.debug('Unhandled inotify event %s' % event)


# functions


# main
if __name__ == '__main__':
##    print('Nothing to see here, move along.')
    # commandline
    parser = parser = argparse.ArgumentParser()
    parser.add_argument('source',
                        help='source directory')
    parser.add_argument('destination',
                        help='destination directory')
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='enable debug output')
    parser.add_argument('-m','--move',
                        action='store_true',
                        help='move rather than copy files')
    parser.add_argument('-c','--create',
                        action='store_true',
                        help='create destination if it does not exist')
    parser.add_argument('-s','--sync',
                        action='store_true',
                        help='sync filesystem after each file is written. May impact performance.')
    args = parser.parse_args()
    # start logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()
    
    logging.debug(args)
    
    # additional argument validation
    if os.path.exists(args.source) == False:
        parser.error('%s does not exist' % args.source)
    if os.path.isdir(args.source) == False:
        parser.error('%s must be a directory' % args.source)
    if os.path.exists(args.destination):
        if os.path.isdir(args.destination) == False:
            parser.error('%s must be a directory' % args.destination)
        if os.path.samefile(args.source, args.destination):
            parser.error('source and destination must not be the same.')
    else:
        if args.create:
            os.makedirs(os.abspath(args.destination))
        else:
            if os.path.exists(args.destination) == False:
                parser.error('%s does not exist and -c not specified' % args.destination)
    logging.debug('Args are valid')
    
    # inotify setup
    mask = pyinotify.IN_CLOSE_WRITE
    my_handler = in_event_handler()
    try:
        wm = pyinotify.WatchManager()
##        notifier = pyinotify.Notifier(wm)
        notifier = pyinotify.Notifier(wm, my_handler)
        wm.add_watch(args.source, pyinotify.ALL_EVENTS)
        notifier.loop()
    except Exception:
        logging.exception('Unhandled exception')
