# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os, re
import maya.cmds as cmds

import tank
from tank import Hook
from tank import TankError

# need the engine to access templates for publishing
from tank.platform.engine import current_engine

class ScanSceneHook(Hook):
    """
    Hook to scan scene for items to publish
    """
    
    def execute(self, **kwargs):
        """
        Main hook entry point
        :returns:       A list of any items that were found to be published.  
                        Each item in the list should be a dictionary containing 
                        the following keys:
                        {
                            type:   String
                                    This should match a scene_item_type defined in
                                    one of the outputs in the configuration and is 
                                    used to determine the outputs that should be 
                                    published for the item
                                    
                            name:   String
                                    Name to use for the item in the UI
                            
                            description:    String
                                            Description of the item to use in the UI
                                            
                            selected:       Bool
                                            Initial selected state of item in the UI.  
                                            Items are selected by default.
                                            
                            required:       Bool
                                            Required state of item in the UI.  If True then
                                            item will not be deselectable.  Items are not
                                            required by default.
                                            
                            other_params:   Dictionary
                                            Optional dictionary that will be passed to the
                                            pre-publish and publish hooks
                        }
        """   
                
        items = []
        
        # get the main scene:
        scene_name = cmds.file(query=True, sn=True)
        if not scene_name:
            raise TankError("Please Save your file before Publishing")
        
        scene_path = os.path.abspath(scene_name)
        name = os.path.basename(scene_path)

        # create the primary item - this will match the primary output 'scene_item_type':            
        items.append({"type": "work_file", "name": name})

        # get a list of any cameras in the scene
        all_persp_cameras = cmds.listCameras(perspective=True)
        for camera in all_persp_cameras:
            if not camera == 'persp':
                print '<scan-scene> found camera %s' % camera
                items.append({
                    "type": "camera",
                    "name": camera,
                    "description": "scene renderable camera",
                    "selected": True,
                })

        # look for root level groups that have meshes as children:
        for grp in cmds.ls(assemblies=True):
            if cmds.ls(grp, dag=True, type="mesh"):
                # Include this group as a 'mesh_group' type. Once we find one
                # we will return, as we're taking the simple approach and exporting
                # a single abc for all meshes in the scene.
                items.append(
                    dict(
                        type="mesh_group",
                        name=grp,
                    )
                )

        fl = cmds.renderSettings(firstImageName=True, lastImageName=True)

        # if in shot context check for renders to publish
        if 'assets' not in scene_path.lower() and not fl[1] == '':
            # we'll use the engine to get the templates
            engine = current_engine()

            # get the "maya_shot_work" template to grab some info from the current
            # work file. get_fields will pull out the version number for us.
            work_template = engine.tank.templates.get("maya_shot_work")
            work_template_fields = work_template.get_fields(scene_name)
            version = work_template_fields["version"]

            # now grab the render template to match against.
            render_template = engine.tank.templates.get("maya_shot_render")

            fields = {
                'Sequence': work_template_fields['Sequence'],
                'Shot': work_template_fields['Shot'],
                'Step': work_template_fields['Step'],
                'name': work_template_fields['name'],
                'version': work_template_fields['version']
            }

            # match existing paths against the render template
            paths = engine.tank.abstract_paths_from_template(render_template, fields)

            # no render sequence found
            if paths == []:
                return items

            try:
                fl0_split = fl[0].split('.')
                ren_start = int(fl0_split[len(fl0_split) - 2])
                frame_padding = len(fl0_split[len(fl0_split) - 2])
                frame_path = re.sub(r'%[0-9]+d', str(ren_start).zfill(frame_padding), paths[0])
                # print "<debug>", frame_path
            except:
                # print "<debug>", paths
                # print "<debug>", fl
                raise TankError("Problem with naming convention of render. Render naming convention {name}.{version}.{SEQ}.exr")

            # if there's a match, add an item to the render
            if os.path.exists(frame_path):
                render_name = os.path.basename(paths[0])
                fl1_split = fl[1].split('.')
                ren_end = int(fl1_split[len(fl1_split) - 2])

                items.append({
                    "type": "rendered_image",
                    "name": render_name,

                    # since we already know the path, pass it along for
                    # publish hook to use
                    "other_params": {
                        'path': paths[0],
                        'start': ren_start,
                        'end':ren_end,
                        'fr_padding': frame_padding
                    }
                })

        return items
