# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys, os
import maya.cmds as cmds
# import maya.mel as mel

# import tank
from tank import Hook
# from tank import TankError

class PrePublishHook(Hook):
    """
    Single hook that implements pre-publish functionality
    """
    def execute(self, tasks, work_template, progress_cb, **kwargs):
        """
        Main hook entry point
        :param tasks:           List of tasks to be pre-published.  Each task is be a 
                                dictionary containing the following keys:
                                {   
                                    item:   Dictionary
                                            This is the item returned by the scan hook 
                                            {   
                                                name:           String
                                                description:    String
                                                type:           String
                                                other_params:   Dictionary
                                            }
                                           
                                    output: Dictionary
                                            This is the output as defined in the configuration - the 
                                            primary output will always be named 'primary' 
                                            {
                                                name:             String
                                                publish_template: template
                                                tank_type:        String
                                            }
                                }
                        
        :param work_template:   template
                                This is the template defined in the config that
                                represents the current work file
               
        :param progress_cb:     Function
                                A progress callback to log progress during pre-publish.  Call:
                                
                                    progress_cb(percentage, msg)
                                     
                                to report progress to the UI
                        
        :returns:               A list of any tasks that were found which have problems that
                                need to be reported in the UI.  Each item in the list should
                                be a dictionary containing the following keys:
                                {
                                    task:   Dictionary
                                            This is the task that was passed into the hook and
                                            should not be modified
                                            {
                                                item:...
                                                output:...
                                            }
                                            
                                    errors: List
                                            A list of error messages (strings) to report    
                                }
        """

        print "<pre-publish> tasks =>", tasks
        print "<pre-publish> work_template =>", work_template
              
        results = []
        
        # validate tasks:
        for task in tasks:
            item = task["item"]
            output = task["output"]
            errors = []
        
            # report progress:
            progress_cb(0, "Validating", task)

            print output["name"]
        
            # pre-publish alembic_cache output
            if output["name"] == "camera_export":
                errors.extend(self._validate_camera())
            elif output["name"] == "geo_export":
                errors.extend(self._validate_geometry(item))
            elif output["name"] == "render_publish":
                errors.extend(self._validate_renders(item))
            else:
                # don't know how to publish this output types!
                errors.append("Don't know how to publish this item!")            

            # if there is anything to report then add to result
            if len(errors) > 0:
                # add result:
                results.append({"task":task, "errors":errors})
                
            progress_cb(100)

        print "<pre-publish> complete"
            
        return results

    def _validate_camera(self):
        """
        Validate that the appropriate plugins are available and loaded to enable export of camera.
        """
        errors = []

        try:
            cmds.loadPlugin('AbcExport')
        except RuntimeError:
            print '<pre-publish> Unable to load AbcExport plugin. We will be unable to export abc camera for publish!'
            errors.append('Unable to load AbcExport plugin. We will be unable to export abc camera for publish!')

        return errors

    def _validate_geometry(self, item):
        """
        Validate that the appropriate plugins are available and loaded to enable export of geometry. Check geo is not
        hidden.
        """
        errors = []

        try:
            cmds.loadPlugin('AbcExport')
        except RuntimeError:
            print '<pre-publish> Unable to load AbcExport plugin. We will be unable to export alembic for publish!'
            errors.append('Unable to load AbcExport plugin. We will be unable to export alembic for publish!')

        # check that the group still exists:
        if not cmds.objExists(item["name"]):
            errors.append("This group couldn't be found in the scene!")
        # and that it still contains meshes:
        elif not cmds.ls(item["name"], dag=True, type="mesh"):
            errors.append("This group doesn't appear to contain any meshes!")

        return errors

    def _validate_renders(self, item):

        errors = []
        # print item

        """
        fl = cmds.renderSettings(firstImageName=True, lastImageName=True)
        fl0_split = fl[0].split('.')
        item['other_params']['start'] = int(fl0_split[1])
        item['other_params']['fr_padding'] = len(fl0_split[1])

        if fl[1] == '':
            item['other_params']['end'] = int(fl0_split[1])
        else:
            fl1_split = fl[1].split('.')
            item['other_params']['end'] = int(fl1_split[1])
        """

        seq_valid, frame_path, next_frame = self.check_frames(item)

        if not seq_valid:
            errors.append("Invalid sequence. Problem between %s and %s." %(frame_path, next_frame))

        # print errors
        # errors.append("Invalid Sequence")

        return errors

    def check_frames(self, item):
        """
        Checks an image sequence to see if there are any file size discrepancies
        between adjacent frames. Inputs are

        framepath 	(str): normalized path to first frame in image sequence
        first_frame (int): first frame in sequence (not plate)
        last_frame 	(int): last frame in sequence

        Filename format is name.num.ext.

        size_threshold is used to set allowable percentage difference in size
        between each frame.

        Returns a flag indicating if frame sequence is valid.
        """

        frame_path = ''
        next_frame = ''
        first_frame = item['other_params']['start']
        last_frame = item['other_params']['end']

        # Size threshold, allowable percentage difference in size between each frame
        size_threshold = 0.2

        # Extract file extension and filename from framepath.
        framepath_split = item['other_params']['path'].split(os.sep)
        filename_split = framepath_split[-1].split('.')
        seq_filename = filename_split[0]
        seq_ext = filename_split[-1]
        num_pad = len(filename_split[len(filename_split) - 2])
        version = filename_split[len(filename_split) - 3]

        # Loop through frame sequence and check size difference between frames
        for i in range(first_frame, last_frame):
            seq_number = str(i).zfill(num_pad)
            next_seq_number = str(i+1).zfill(num_pad)
            frame_path = os.sep.join([os.sep.join(framepath_split[0:-1]), '.'.join([seq_filename, version, seq_number, seq_ext])])
            next_frame = os.sep.join([os.sep.join(framepath_split[0:-1]), '.'.join([seq_filename, version, next_seq_number, seq_ext])])

            # Check if path exists
            if not (os.path.exists(frame_path) and os.path.exists(next_frame)):
                print "Invalid path."
                return False, os.path.basename(frame_path), os.path.basename(next_frame)

            curr_frame_size = float(os.path.getsize(frame_path))
            next_frame_size = float(os.path.getsize(next_frame))

            if next_frame_size > curr_frame_size:
                size_diff = curr_frame_size/next_frame_size
            else:
                size_diff = next_frame_size/curr_frame_size

            if size_diff < size_threshold:
                print("Invalid sequence. Problem between frames %s and %s." %(frame_path, next_frame))
                return False, os.path.basename(frame_path), os.path.basename(next_frame)

        return True, os.path.basename(frame_path), os.path.basename(next_frame)
