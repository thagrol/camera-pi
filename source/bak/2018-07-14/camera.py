#!/usr/bin/env python3

# imports
import gphoto2 as gp
import gpio
import logging
import os
import time

from collections import deque

# globals
_CAMERA_TIMEOUT = 1.0
_UPDATE_NEW_EVERY = 3
_EVENT_NAMES = {}
for name in ('GP_EVENT_UNKNOWN', 'GP_EVENT_TIMEOUT',
             'GP_EVENT_FILE_ADDED', 'GP_EVENT_FOLDER_ADDED',
             'GP_EVENT_CAPTURE_COMPLETE'):
    _EVENT_NAMES[getattr(gp, name)] = name


# classes
class camera(object):
    def __init__(self, target_dir, leds,
                 copy_all=False,
                 overwrite=False,
                 wait_for_camera=True,
                 timeout=_CAMERA_TIMEOUT,
                 update_new_every=_UPDATE_NEW_EVERY):
        self._target_dir = os.path.normpath(os.path.abspath(os.path.expanduser(os.path.expandvars(self._validate_dest(target_dir)))))
        self.__leds = leds
        self._copy_all = copy_all
        self._overwrite = overwrite
        self._wait_for_camera = wait_for_camera
        self._timeout = timeout
        self._update_new_every = update_new_every
        self._to_copy = deque()
        self._old_files = []
        self._poll_new = True
        self._poll_count = 0
##        gp.use_python_logging()
        
        self._camera=gp.Camera()
        self.__leds.busy_led = True
        self.__connect(self._wait_for_camera)
        self.__leds.busy_led = False
        
        logging.debug('Getting list of old files')
        self._old_files = self.list_files()
        logging.debug('\tDone. Found %i' % len(self._old_files))
        if self._copy_all and len(self._old_files) > 0:
##            self.__leds.busy_led = True
            logging.info('Copying existing files')
            # busy indicator code goes here
            copy_count = 0
            for f in self._old_files:
                copy_count += self.get_file(f, self._target_dir)
            logging.info('\t%i of %i copied' % (copy_count, len(self._old_files)))
##            self.__leds.busy_led = False
        
    def __connect(self, wait):
        # (re)connect to camera
        logging.info('Connecting to camera')
        self.exit()
        self._camera=gp.Camera()
        while True:
            try:
                self._camera.init()
            except gp.GPhoto2Error as e:
                if e.code == gp.GP_ERROR_MODEL_NOT_FOUND and wait:
                    logging.debug('\tnot found. Sleeping')
                    time.sleep(2)
                    continue
                raise
            logging.info('\tsuccessful')
            break
        
    def exit(self):
        try:
            self._camera.exit()
        except:
            logging.exception('Problem closing camera')
        
        
    def list_files(self, path='/'):
        result = []
        # get files
        for name, value in self._camera.folder_list_files(path):
            result.append(os.path.join(path, name))
        # read folders
        folders = []
        for name, value in self._camera.folder_list_folders(path):
            folders.append(name)
        # recurse over subfolders
        for name in folders:
            result.extend(self.list_files(os.path.join(path, name)))
        return result


    def list_new_files(self, path='/'):
        # not all cameras maintain the "downloaded" flag so doing this the hardway...
        new_files = []
        for f in self.list_files(path):
            if f in self._old_files:
                continue
            new_files.append(f)
        return new_files
    
    def get_file(self, source, dest=None):
        # attempt to copy sorce file from camera
        # return True if successful, False otherwise
        source_folder, source_file = os.path.split(source)
        if dest is None:
            dest = self._target_dir
        dest = os.path.join(self._validate_dest(dest), source_file)
        if os.path.exists(dest) and self._overwrite != True:
            logging.error('File not copied as destination file %s exists and overwrite not specified' %
                          dest)
            return False
        try:
            file = self._camera.file_get(source_folder, source_file,
                                         gp.GP_FILE_TYPE_NORMAL)
            gp.check_result(gp.gp_file_save(file, dest))
        except KeyboardInterrupt:
            raise
        except:
            logging.exception('Failed to get file from camera')
            return False
        return True
    
        
    def _validate_dest(self, dest):
        if os.path.exists(dest) and not os.path.isdir(dest):
            raise('%s must be a directory' % (dest,))
        elif os.path.isdir(dest):
            pass
        else:
            os.makedirs(dest)
        return dest
    
    
    def poll_events(self, timeout=1):
        if timeout is None:
            timeout = self._timeout
        timeout = timeout * 1000
        try:
            event, data = self._camera.wait_for_event(1000)
        except gp.GPhoto2Error as e:
            event = None
            data = None
            logging.exception('Problem communicating with camera. Attempting to reconnect')
            self.__connect(self._wait_for_camera)
            return
        # handles events
        logging.debug('gphoto2 event %s' % _EVENT_NAMES[event])
        if event == gp.GP_EVENT_FILE_ADDED:
            # assumes an ything with DCIM in the folder is on
            # the storage card.
            # no DCIM = internal memory so can't queue for download
            logging.debug('New file added event: %s' % os.path.join(data.folder, data.name))
##            if 'dcim' in data.folder.lower():
            logging.debug('\t added to "to_copy" list')
            self._to_copy.append(os.path.join(data.folder, data.name))
##            else:
##                logging.debug('\tScanning for new files')
##                self._to_copy.extend(self.list_new_files())
        elif event == gp.GP_EVENT_TIMEOUT:
            pass
##        else:
##            logging.debug('Unhandled gphoto2 event: %s %s' % (_EVENT_NAMES[event], data))
        self.exit()
    
    
    def poll_files(self):# update to_copy list
        if self._poll_count % _UPDATE_NEW_EVERY == 0:
            logging.debug('Scanning for new files')
            l = len(self._to_copy)
            self._to_copy.extend(self.list_new_files())
            logging.debug('\tFound %s' % (len(self._to_copy) - l))
            self._poll_count = 0
        else:
            self._poll_count += 1
        # do file copy stuff here
        while len(self._to_copy) > 0:
##            self.__leds.busy_led = True
            if self.get_file(self._to_copy[0], self._target_dir):
                logging.info('Copied %s to %s' %
                             (self._to_copy[0], self._target_dir))
            self._old_files.append(self._to_copy.popleft())
##            self.__leds.busy_led = False
        self.exit()
        
        
    def poll_once(self, timeout=1):
        self.poll_events(timeout)
        self.poll_files()
##        if timeout is None:
##            timeout = self._timeout
##        timeout = timeout * 1000
##        try:
##            event, data = self._camera.wait_for_event(1000)
##        except gp.GPhoto2Error as e:
##            event = None
##            data = None
##            logging.exception('Problem communicating with camera. Attempting to reconnect')
##            self.__connect(self._wait_for_camera)
##            return
##        # handles events
##        logging.debug('gphoto2 event %s' % _EVENT_NAMES[event])
##        if event == gp.GP_EVENT_FILE_ADDED:
##            # assumes an ything with DCIM in the folder is on
##            # the storage card.
##            # no DCIM = internal memory so can't queue for download
##            logging.debug('New file added event: %s' % os.path.join(data.folder, data.name))
####            if 'dcim' in data.folder.lower():
##            logging.debug('\t added to "to_copy" list')
##            self._to_copy.append(os.path.join(data.folder, data.name))
####            else:
####                logging.debug('\tScanning for new files')
####                self._to_copy.extend(self.list_new_files())
##        elif event == gp.GP_EVENT_TIMEOUT:
##            pass
####        else:
####            logging.debug('Unhandled gphoto2 event: %s %s' % (_EVENT_NAMES[event], data))
##        # update to_copy list
##        if self._poll_count % _UPDATE_NEW_EVERY == 0:
##            logging.debug('Scanning for new files')
##            l = len(self._to_copy)
##            self._to_copy.extend(self.list_new_files())
##            logging.debug('\tFound %s' % (len(self._to_copy) - l))
##            self._poll_count = 0
##        else:
##            self._poll_count += 1
##        # do file copy stuff here
##        if len(self._to_copy) > 0:
####            self.__leds.busy_led = True
##            if self.get_file(self._to_copy[0], self._target_dir):
##                logging.info('Copied %s to %s' %
##                             (self._to_copy[0], self._target_dir))
##            self._old_files.append(self._to_copy.popleft())
####            self.__leds.busy_led = False
##        self.exit()
    
    
    def poll_every(self, interval, timeout=1):
        # poll camera for events and new files every interval seconds
        # this function will never return
        while True:
            self.poll_once(timeout=timeout)
            time.sleep(interval)


# functions
    

# main
if __name__ == '__main__':
    print('Nothing to see here, move along.')