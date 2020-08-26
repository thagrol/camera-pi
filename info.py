#!/usr/bin/env python3

import gphoto2 as gp2
import os
import sys

camera = gp2.Camera()


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

for f in list_files(camera):
    folder, name = os.path.split(f)
    info = camera.file_get_info(folder, name).file
    print(f,
          info.fields,
##          info.height,
          info.permissions,
##          info.size,
          info.status,
##          info.type,
##          info.width
          )
camera.Exit()