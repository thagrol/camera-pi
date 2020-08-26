#!/usr/bin/env python3

# imports
import gphoto2 as gp
import gpio
import logging
import os
import shutil
import threading
import time

from collections import deque
from datetime import datetime, date

# globals
_CAMERA_TIMEOUT = 1.0
_UPDATE_NEW_EVERY = 3
_EVENT_NAMES = {}
for name in ('GP_EVENT_UNKNOWN', 'GP_EVENT_TIMEOUT',
             'GP_EVENT_FILE_ADDED', 'GP_EVENT_FOLDER_ADDED',
             'GP_EVENT_CAPTURE_COMPLETE'):
    _EVENT_NAMES[getattr(gp, name)] = name
##_CAMERA_LOCK = threading.Lock()


# classes
class camera(object):
    def __init__(self, target_dir, leds,
                 copy_all=False,
                 overwrite=False,
                 wait_for_camera=True,
                 timeout=_CAMERA_TIMEOUT,
                 update_new_every=_UPDATE_NEW_EVERY,
                 sync=False):
        self._target_dir = os.path.normpath(os.path.abspath(os.path.expanduser(os.path.expandvars(self._validate_dest(target_dir)))))
        self.__leds = leds
        self._copy_all = copy_all
        self._overwrite = overwrite
        self._wait_for_camera = wait_for_camera
        self._timeout = timeout
        self._update_new_every = update_new_every
        self._to_copy = deque()
        self._ignore_list = []
        self._poll_new = True
        self._poll_count = 0
        self._lock = threading.Lock()
        self._sync = sync
##        gp.use_python_logging()
        
        self._camera=gp.Camera()
    
    
    def __find_DCIM(self):
        # find base DCIM folder. assumes camera follows DCF rules
        # returns the first DCIM folder found
        # or '/' if none
        storage = self._camera.get_storageinfo()
        paths =[]
        for s in storage:
            paths.append(s.basedir)
        for p in paths:
            for name, value in self._camera.folder_list_folders(p):
                if name.lower() == 'dcim':
                    return os.path.join(p, name)
                paths.append(os.path.join(p, name))
        # not found so
        return '/'
        
        
##    def __connect(self, wait):
##        # (re)connect to camera
##        logging.info('Connecting to camera')
##        self.exit()
##        self._camera=gp.Camera()
##        while True:
##            try:
##                self._camera.init()
##            except gp.GPhoto2Error as e:
##                if e.code == gp.GP_ERROR_MODEL_NOT_FOUND and wait:
##                    logging.debug('\tnot found. Sleeping')
##                    time.sleep(2)
##                    continue
##                raise
##            logging.info('\tsuccessful')
##            break
        
    def exit(self):
        try:
            logging.debug('Closing camera')
            self._camera.exit()
            logging.debug('Closed')
        except Exception:
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
        logging.debug('Fetching %s' % source)
        if dest is None:
            dest = self._target_dir
        else:
            dest = self._validate_dest(dest)
        dest = os.path.join(dest, source_file)
        if os.path.exists(dest) and self._overwrite != True:
            logging.error('File not copied as destination file %s exists and overwrite not specified' %
                          dest)
            return False
        try:
            file = self._camera.file_get(source_folder, source_file,
                                         gp.GP_FILE_TYPE_NORMAL)
            logging.debug('Saving to %s' % dest)
            gp.check_result(gp.gp_file_save(file, dest))
            if self._sync:
                logging.debug('syncing filesystem')
                os.sync()
        except Exception:
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
    
    
##    def poll_events(self, timeout=1):
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
##        self.exit()
    
    
    def poll_files(self):# update to_copy list
        if self._poll_count % _UPDATE_NEW_EVERY == 0:
            logging.debug('Scanning for new files')
            l = len(self._to_copy)
            self._to_copy.extend(self.list_new_files(self.__base_path))
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
        logging.debug('Aquiring lock.')
##        _CAMERA_LOCK.aquire()
        with self._lock:
            logging.debug('Aquiried.')
            self.__leds[gpio.LED_BUSY].blink()
##            return
            try:
                # get date from camera
                try:
                    config = self._camera.get_config()
                except gp.GPhoto2Error:
                    # try with a fresh camera object
                    self._camera=gp.Camera()
                    config = self._camera.get_config()
                for name, fmt in (('datetime', '%Y-%m-%d %H:%M:%S'),
                                  ('d034', None)):
                    OK, datetime_config = gp.gp_widget_get_child_by_name(config, name)
                    if OK >= gp.GP_OK:
                        widget_type = gp.check_result(gp.gp_widget_get_type(datetime_config))
                        if widget_type == gp.GP_WIDGET_DATE:
                            raw_value = gp.check_result(gp.gp_widget_get_value(datetime_config))
                            camera_time = datetime.fromtimestamp(raw_value)
                        else:
                            raw_value = (gp.gp_widget_get_value(datetime_config))
                            if fmt:
                                camera_time = datetime.strptime(raw_value, fmt)
                            else:
                                camera_time = datetime.utcfromtimestamp(float(raw_value))
                        camera_date = camera_time.date().isoformat()
                    else:
                        camera_date = date.today().isoformat()
                logging.debug('Camera date: %s ' % camera_date)
                # find new files
                search_top = self.__find_DCIM()
                logging.debug('searching for files in %s' % search_top)
                for f in self.list_files(search_top):
                    if f in self._ignore_list:
                        continue
                    p, n = os.path.split(f)
                    info = self._camera.file_get_info(p, n)
                    mdate = date.fromtimestamp(info.file.mtime).isoformat()
                    downloaded = info.file.status & gp.GP_FILE_STATUS_DOWNLOADED
                    if mdate != camera_date or downloaded:
                        logging.debug('Skipping %s' % f)
                        continue
                    freespace = shutil.disk_usage(self._target_dir).free
                    if freespace <= info.file.size:
                        logging.error('Not enough space on target device.')
                        logging.error('\tHave %s Need %s' % (freespace, info.file.size))
                        break
                    # download file
                    self.get_file(f)
                        
            except gp.GPhoto2Error:
                logging.exception('Problem communicationg with camera')
            finally:
                self.__leds[gpio.LED_BUSY].off()
                try:
##                    self._camera.exit()
                    self.exit()
                except Exception:
                    pass
        return
##        self.poll_events(timeout)
##        self.poll_files()
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