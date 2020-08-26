#!/usr/bin/env python3

# imports
import camera
import cmd_line
import config
import gpio
import logging

from constants import *

# globals


# classes


# functions


# main

if __name__ == '__main__':
##    print('Nothing to see here, move along.')
    args = cmd_line.arguments()
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level=logging.WARNING
    logging.basicConfig(level=log_level)
    logging.debug('Command line args: %s' % args)
    try:
        leds = gpio.leds()
        try:
            leds[gpio.LED_UP].on()
        except AttributeError, gpio.GPIOZeroError:
            pass
        cam = None
##        camera = camera.camera(args.directory, leds,
##                               copy_all=args.copyall,
##                               overwrite=args.overwrite,
##                               wait_for_camera=args.nowait)
##        camera.poll_every(15)
    except Exception:
        logging.exception('Unhandled exception')
        raise
    finally:
            if cam:
                cam.exit()
            for k in leds.keys():
                if leds[k]:
                    leds[k].off()
