#!/usr/bin/env python3

# imports
import camera
import cmd_line
import config
import gpio
import logging
import threading

from constants import *

# globals
trigger_timer = None

# classes


# functions
def trigger_set_timer():
    global trigger_timer
    logging.debug('Trigger detected.')
    if trigger_timer is not None:
        trigger_timer.cancel()
    trigger_timer = threading.Timer(TRIGGER_DELAY, trigger_fired)
    trigger_timer.start()
    

def trigger_fired():
    logging.debug('Trigger timer fired, polling camera')
    cam.poll_once()
    

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
    cam = None
    try:
        leds = gpio.leds()
        try:
            leds[gpio.LED_UP].on()
        except Exception:
            pass
        trigger = gpio.trigger()
        trigger.when_released = trigger_set_timer
        cam = camera.camera(args.output, leds,
                            copy_all=args.copyall,
                            overwrite=args.overwrite,
                            wait_for_camera=args.nowait,
                            sync=args.sync)
##        cam.poll_once()
##        cam.poll_every(15)
        while True:
            pass
    except Exception:
        logging.exception('Unhandled exception')
        raise
    finally:
            if cam:
                cam.exit()
            for k in leds.keys():
                if leds[k]:
                    leds[k].off()
            print('\nByeBye\n')
