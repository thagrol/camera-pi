#!/usr/bin/env python3

# imports
import gphoto2 as gp
import logging
import os
import sys
import time

# globals
EVENT_TIMEOUT = 1000

# functions
def list_files(camera, path='/'):
    result = []
    # get files
    for name, value in camera.folder_list_files(path):
        result.append(os.path.join(path, name))
    # read folders
    folders = []
    for name, value in camera.folder_list_folders(path):
        folders.append(name)
    # recurse over subfolders
    for name in folders:
        result.extend(list_files(camera, os.path.join(path, name)))
    return result


def main():
    camera = gp.Camera()
    camera.init()
    
    old_files = list_files
##    print(old_files)
    
    while True:
        try:
            ev_type, ev_data = camera.wait_for_event(EVENT_TIMEOUT)
            if ev_type == gp.GP_EVENT_FILE_ADDED:
                print('file added event: ',
                      os.path.join(ev_data.folder, ev_data.name))
                print(camera.file_get_info(ev_data.folder, ev_data.name).file.fields)
##                new_files = []
##                for f in list_files(camera):
##                    if f not in old_files and f not in new_files:
##                        new_files.append(f)
##                print(f)
##                camera.exit()
##                os.system('/usr/bin/gphoto2 -R -L --new')
##                camera = gp.Camera()
##                camera.init()
        except KeyboardInterrupt:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())