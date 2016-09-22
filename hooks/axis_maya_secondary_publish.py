# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
# import shutil
import re
from shutil import copy
import maya.cmds as cmds
import maya.mel as mel

import tank
from tank import Hook
from tank import TankError

class PublishHook(Hook):
    """
    Single hook that implements publish functionality for secondary tasks
    """    
    def execute(self, tasks, work_template, comment, thumbnail_path, sg_task, primary_task, primary_publish_path, progress_cb, **kwargs):
        """
        Main hook entry point
        :param tasks:                   List of secondary tasks to be published.  Each task is a 
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
                        
        :param work_template:           template
                                        This is the template defined in the config that
                                        represents the current work file
               
        :param comment:                 String
                                        The comment provided for the publish
                        
        :param thumbnail:               Path string
                                        The default thumbnail provided for the publish
                        
        :param sg_task:                 Dictionary (shotgun entity description)
                                        The shotgun task to use for the publish    
                        
        :param primary_publish_path:    Path string
                                        This is the path of the primary published file as returned
                                        by the primary publish hook
                        
        :param progress_cb:             Function
                                        A progress callback to log progress during pre-publish.  Call:
                                        
                                            progress_cb(percentage, msg)
                                             
                                        to report progress to the UI
                        
        :param primary_task:            The primary task that was published by the primary publish hook.  Passed
                                        in here for reference.  This is a dictionary in the same format as the
                                        secondary tasks above.
        
        :returns:                       A list of any tasks that had problems that need to be reported 
                                        in the UI.  Each item in the list should be a dictionary containing 
                                        the following keys:
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
        results = []

        # print "<tasks> ", tasks
        
        # publish all tasks:
        for task in tasks:
            item = task["item"]
            output = task["output"]
            errors = []

            # print "<publish> ", item
            # print "<publish> ", output
            # print output["name"]
        
            # report progress:
            progress_cb(0, "Publishing", task)

            # calculate publish path for this task
            working_path = cmds.file(query=True, sceneName=True)

            fields = work_template.get_fields(working_path)
            publish_template = output["publish_template"]
            # secondary_publish_path = publish_template.apply_fields(fields)

            # print "<fields> ", fields
        
            # publish alembic_cache output
            if output["name"] == "camera_export":
                try:
                    task_errors = self._publish_camera(item, publish_template, fields, comment, sg_task,
                                                      primary_publish_path, progress_cb, thumbnail_path)
                except Exception, e:
                    errors.append("Publish failed - %s" % e)
            elif output["name"] == "geo_export":
                try:
                    task_errors = self._publish_geo(item, publish_template, fields, comment, sg_task,
                                                   primary_publish_path, progress_cb, thumbnail_path)
                except Exception, e:
                    errors.append("Publish failed - %s" % e)
            elif output["name"] == "render_publish":
                fields['width'] = cmds.getAttr('defaultResolution.width')
                fields['height'] = cmds.getAttr('defaultResolution.height')
                # print "<fields> ", fields

                try:
                    task_errors = self._publish_renders(item, publish_template, fields, comment, sg_task,
                                                       primary_publish_path, progress_cb, thumbnail_path)
                except Exception, e:
                    errors.append("Publish failed - %s" % e)
            else:
                # don't know how to publish this output types!
                errors.append("Don't know how to publish this item!")

            if len(task_errors) > 0:
                errors.extend(task_errors)

            # if there is anything to report then add to result
            if len(errors) > 0:
                # add result:
                results.append({"task":task, "errors":errors})
             
            progress_cb(100)

        return results

    def _publish_camera(self, item, publish_template, fields, comment, sg_task, primary_publish_path, progress_cb,
                        thumbnail_path):
        """
        Publishes the selected camera
        """
        errors = []

        print "<publish> publish camera called"

        # set publish path and publish name based on publish template and item name respectively.
        fields['name'] = item['name'].replace(":","_")
        secondary_publish_path = publish_template.apply_fields(fields)
        secondary_publish_name = fields.get("name").upper()  # we want an uppercase name
        if not secondary_publish_name:
            secondary_publish_name = os.path.basename(secondary_publish_path)

        print "<publish> using name for publish: %s" % secondary_publish_name

        # check if camera has already been published.
        if os.path.exists(secondary_publish_path):
            print "<publish> The published camera named '%s' already exists!" % secondary_publish_path
            errors.append("The published camera named '%s' already exists!" % secondary_publish_path)
            return errors

        # select the camera
        try:
            cmds.select(item['name'], visible=True, hierarchy=True, replace=True)
            print "<publish> selected %s" % item['name']
        except ValueError as e:
            errors.append('Unable to select camera [%s]' % item['name'])
            return errors

        # find the animated frame range to use:
        start_frame, end_frame = self._find_scene_animation_range()

        # bake out camera if grouped
        if not cmds.listRelatives( item['name'], allParents=True ) is None:
            dup_name = self._bake_camera(item, start_frame, end_frame)
        else:
            dup_name = item['name']
            self._unlock_camera(dup_name)
            if not cmds.getAttr(''.join([dup_name, '.sx'])) == 1:
                cmds.setAttr(''.join([dup_name, '.sx']), 1)
                cmds.setAttr(''.join([dup_name, '.sy']), 1)
                cmds.setAttr(''.join([dup_name, '.sz']), 1)

        alembic_args_string = ''.join(["-root |", dup_name])
        alembic_args = [alembic_args_string] 

        if start_frame and end_frame:
            alembic_args.append("-fr %d %d" % (start_frame, end_frame))

        # Set the output path: 
        # Note: The AbcExport command expects forward slashes!
        alembic_args.append("-file %s" % secondary_publish_path.replace("\\", "/"))

        # build the export command.  Note, use AbcExport -help in Maya for
        # more detailed Alembic export help
        abc_export_cmd = ("AbcExport -j \"%s\"" % " ".join(alembic_args))

        # ...and execute it:
        progress_cb(30, "Exporting Alembic cache")
        try:
            self.parent.log_debug("Executing command: %s" % abc_export_cmd)
            mel.eval(abc_export_cmd)
        except Exception, e:
            raise TankError("Failed to export Alembic Cache: %s" % e)

        # register the publish:
        progress_cb(75, "Registering the publish")        
        args = {
            "tk": self.parent.tank,
            "context": self.parent.context,
            "comment": comment,
            "path": secondary_publish_path,
            "name": secondary_publish_name,
            "version_number": fields["version"],
            "thumbnail_path": thumbnail_path,
            "task": sg_task,
            "dependency_paths": [primary_publish_path],
            "published_file_type":'Camera'
        }
        tank.util.register_publish(**args)

        return errors

    def _publish_geo(self, item, publish_template, fields, comment, sg_task, primary_publish_path, progress_cb,
                     thumbnail_path):
        """
        Publishes the mesh group as an alembic.
        """
        errors = []
        print "<publish> publish model called"

        # print item['name']

        # fields['name'] = item['name'].split('|')[-1]
        fields['name'] = item['name'].split(':')[-1]
        # print fields['name']
        secondary_publish_path = publish_template.apply_fields(fields)

        secondary_publish_name = fields.get("name")
        if not secondary_publish_name:
            secondary_publish_name = os.path.basename(secondary_publish_path)

        if os.path.exists(secondary_publish_path):
            print "<publish> The geoPublish named '%s' already exists!" % secondary_publish_path
            errors.append("The geoPublish named '%s' already exists!" % secondary_publish_path)
            return errors

        progress_cb(10, "Analysing scene")

        alembic_args = ["-renderableOnly",   # only renderable objects (visible and not templated)
                        "-worldSpace",       # root nodes will be stored in world space
                        "-uvWrite",           # write uv's (only the current uv set gets written)
                        "-wholeFrameGeo",
                        "-selection"
                        ]

        # find the animated frame range to use:
        start_frame, end_frame = self._find_scene_animation_range()
        if start_frame and end_frame:
            alembic_args.append("-fr %d %d" % (start_frame, end_frame))

        # Set the output path:
        # Note: The AbcExport command expects forward slashes!
        alembic_args.append("-file %s" % secondary_publish_path.replace("\\", "/"))

        # build the export command.  Note, use AbcExport -help in Maya for
        # more detailed Alembic export help
        abc_export_cmd = ("AbcExport -j \"%s\"" % " ".join(alembic_args))

        # select geo
        try:
            cmds.select(item['name'], hierarchy=True)
        except Exception as e:
            print e
            errors.append('Unable to select transform [%s]' % item['name'])
            return errors

        # export selection
        progress_cb(30, "Exporting Alembic cache")
        try:
            self.parent.log_debug("Executing command: %s" % abc_export_cmd)
            mel.eval(abc_export_cmd)
        except Exception, e:
            raise TankError("Failed to export Alembic Cache: %s" % e)

        # register the publish:
        progress_cb(75, "Registering the publish")        
        args = {
            "tk": self.parent.tank,
            "context": self.parent.context,
            "comment": comment,
            "path": secondary_publish_path,
            "name": secondary_publish_name,
            "version_number": fields["version"],
            "thumbnail_path": thumbnail_path,
            "task": sg_task,
            "dependency_paths": [primary_publish_path],
            "published_file_type":'Geometry'
        }
        tank.util.register_publish(**args)

        return errors

    def _publish_renders(self, item, publish_template, fields, comment, sg_task, primary_publish_path, progress_cb,
                        thumbnail_path):
        """
        Publish rendered images and register with Shotgun.
        """
        errors = []

        # determine the publish info to use
        progress_cb(10, "Determining publish details")
        secondary_publish_path = publish_template.apply_fields(fields)

        secondary_publish_name = fields.get("name")
        if not secondary_publish_name:
            secondary_publish_name = os.path.basename(secondary_publish_path)

        if os.path.exists(secondary_publish_path):
            print "<publish> The render named '%s' already exists!" % secondary_publish_path
            errors.append("The geoPublish named '%s' already exists!" % secondary_publish_path)
            return errors

        # print "<debug>", secondary_publish_path

        spp_split = secondary_publish_path.split(os.sep)
        output_path = os.sep.join(spp_split[0:-1])

        # print "<debug>", spp_split
        # print "<debug>", output_path

        # copy files
        progress_cb(30, "Copying files...")
        if not self._copy_sequence(item['other_params']['path'], output_path):
            errors.append("Problem copying files. Check permissions of output path.")
            return errors

        # register the publish:
        progress_cb(75, "Registering the publish")

        args = {
            "tk": self.parent.tank,
            "context": self.parent.context,
            "comment": comment,
            "path": secondary_publish_path,
            "name": secondary_publish_name,
            "version_number": fields["version"],
            "thumbnail_path": thumbnail_path,
            "task": sg_task,
            "dependency_paths": [primary_publish_path],
            "published_file_type": 'Rendered Image'
        }
        # print "<debug>", args
        tank.util.register_publish(**args)

        return errors

    def _bake_camera(self, item, start_frame, end_frame):

        cmds.currentTime(start_frame)
        dup_name = ''.join([item['name'], '_exp'])
        cmds.duplicate(item['name'], rr=True, name=dup_name)
        self._unlock_camera(dup_name)
        cmds.parent(dup_name, world=True)
        cmds.parentConstraint(item['name'], dup_name, name='_tempPC')
        cmds.select(dup_name, visible=True, hierarchy=True, replace=True)
        if start_frame == end_frame:
            cmds.bakeResults(dup_name, t=(start_frame, start_frame+1), simulation=True)
        else:
            cmds.bakeResults(dup_name, t=(start_frame, end_frame), simulation=True)

        cmds.delete('_tempPC')
        cmds.cutKey(dup_name, attribute = 'scaleX', clear=True)
        cmds.cutKey(dup_name, attribute = 'scaleY', clear=True)
        cmds.cutKey(dup_name, attribute = 'scaleZ', clear=True)
        if not cmds.getAttr(''.join([dup_name, '.sx'])) == 1:
            cmds.setAttr(''.join([dup_name, '.sx']), 1)
            cmds.setAttr(''.join([dup_name, '.sy']), 1)
            cmds.setAttr(''.join([dup_name, '.sz']), 1)

        return dup_name

    def _unlock_camera(self, camera_name):

        cmds.setAttr(''.join([camera_name, '.tx']), lock=False)
        cmds.setAttr(''.join([camera_name, '.ty']), lock=False)
        cmds.setAttr(''.join([camera_name, '.tz']), lock=False)
        cmds.setAttr(''.join([camera_name, '.rx']), lock=False)
        cmds.setAttr(''.join([camera_name, '.ry']), lock=False)
        cmds.setAttr(''.join([camera_name, '.rz']), lock=False)
        cmds.setAttr(''.join([camera_name, '.sx']), lock=False)
        cmds.setAttr(''.join([camera_name, '.sy']), lock=False)
        cmds.setAttr(''.join([camera_name, '.sz']), lock=False)

    def _find_scene_animation_range(self):
        """
        Find the animation range from the current scene.
        """
        # look for any animation in the scene:
        animation_curves = cmds.ls(typ="animCurve")
        
        # if there aren't any animation curves then just return
        # a single frame:
        if not animation_curves:
            return (1, 1)
        
        # something in the scene is animated so return the
        # current timeline.  This could be extended if needed
        # to calculate the frame range of the animated curves.
        start = int(cmds.playbackOptions(q=True, min=True))
        end = int(cmds.playbackOptions(q=True, max=True))        
        
        return (start, end)

    def _copy_sequence(self, input_path, output_path):

        fl = cmds.renderSettings(firstImageName=True, lastImageName=True)

        try:
            fl0_split = fl[0].split('.')
            start_frame = int(fl0_split[len(fl0_split) - 2])
            fr_padding = len(fl0_split[len(fl0_split) - 2])
        except:
            print "<debug>", fl
            raise TankError("Problem with naming convention of render. Render naming convention {name}.{version}.{SEQ}.exr")

        if fl[1] == '':
            end_frame = int(fl0_split[len(fl0_split) - 2])
        else:
            fl1_split = fl[1].split('.')
            end_frame = int(fl1_split[len(fl1_split) - 2])

        # print "<debug>", output_path

        # Make directories based on output path.
        try:
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            # Copy image sequence
            for num in range(start_frame, end_frame+1):
                input_path_new = re.sub(r'%[0-9]+d', str(num).zfill(fr_padding), input_path)
                # print "<debug>", input_path_new
                copy(input_path_new, output_path)
        except:
            print "Problem copying files. Check permissions of output path."
            return False

        return True
