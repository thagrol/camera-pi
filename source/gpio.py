#!/usr/bin/env python3

# imports
import gpiozero
import logging

# globals
# led names
LED_BUSY = 'busy'
LED_ERROR = 'error'
LED_UP = 'up'

#   pin defaults
__BUSY_LED = 6
__ERROR_LED = None
__UP_LED = None
__TRIGGER = 12


# classes    
##class gpio(object):
##    def __init__(self,
####                 error_led=_ERROR_LED,
##                 busy_led=_BUSY_LED,
##                 trigger=_TRIGGER,
##                 callback=None):
####        if error_led is None:
####            self.__error_led = None
####        else:
####            self.__error_led = gpiozero.LED(error_led)
##        self.__busy_led = gpiozero.LED(busy_led)
##        self.__busy = False
##        self.__error = False
##        # external trigger
##        self.__trigger = gpiozero.Button(trigger)
##        if callback is None:
##            callback = self.__dummy
##        self.__trigger.when_pressed = callback
##        
##    def __dummy(self, pin):
##        # dummy trigger event callback
##        # just logs event
##        logging.debug('Trigger event on %s' % pin.pin)
##        
##    @property
##    def busy_led(self):
##        return self.__busy
##    
##    @busy_led.setter
##    def busy_led(self, value):
##        if self.__busy_led is None or self.__busy == bool(value):
##            return
##        if value:
##            self.__busy == True
##            self.__busy_led.blink()
##        else:
##            self.__busy == False
##            self.__busy_led.off()
##    
##    @property
##    def error_led(self):
##        return self.__error
##    
##    @error_led.setter
##    def error_led(self, value):
##        if self.__error_led is None or self.__error == bool(value):
##            return
##        if value:
##            self.__error == True
##            self.__error_led.blink()
##        else:
##            self.__error == False
##            self.__error_led.off()


# functions
def leds(error_led=__ERROR_LED,
         busy_led=__BUSY_LED,
         up_led=__UP_LED ):
    """
    Create and return set of gpio zero LED objects
    """
    leds = {}
    try:
        leds[LED_ERROR] = gpiozero.LED(error_led)
    except gpiozero.GPIOZeroError:
        leds[LED_ERROR] = None
    try:
        leds[LED_BUSY] = gpiozero.LED(busy_led)
    except gpiozero.GPIOZeroError:
        leds[LED_BUSY] = None
    try:
        leds[LED_UP] = gpiozero.LED(up_led)
    except gpiozero.GPIOZeroError:
        leds[LED_UP] = None
    return leds


def trigger(pin=__TRIGGER,
            active_low=True):
    """Create and retrun gpio zero button object"""
    return gpiozero.Button(pin,pull_up=active_low)

# main
if __name__ == '__main__':
    print('Nothing to see here, move along.')