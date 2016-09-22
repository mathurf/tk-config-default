# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Before App Launch Hook

This hook is executed prior to application launch and is useful if you need
to set environment variables or run scripts as part of the app initialization.
"""

import os
import sys
import tank

class BeforeAppLaunch(tank.Hook):
    """
    Hook to set up the system prior to app launch.
    """
    
    def execute(self, app_path, app_args, version, **kwargs):
        """
        The execute functon of the hook will be called prior to starting the required application        
        
        :param app_path: (str) The path of the application executable
        :param app_args: (str) Any arguments the application may require
        :param version: (str) version of the application being run if set in the "versions" settings
                              of the Launcher instance, otherwise None

        """

        # accessing the current context (current shot, etc)
        # can be done via the parent object
        #
        # > multi_launchapp = self.parent
        # > current_entity = multi_launchapp.context.entity
        
        # you can set environment variables like this:
        # os.environ["MY_SETTING"] = "foo bar"
        
        # if you are using a shared hook to cover multiple applications,
        # you can use the engine setting to figure out which application 
        # is currently being launched:
        #
        # > multi_launchapp = self.parent
        # > if multi_launchapp.get_setting("engine") == "tk-nuke":
        #       do_something()

        multi_launchapp = self.parent
        current_project = multi_launchapp.context.project['name']
        current_project = current_project.lower()
        print '<DEBUG>', multi_launchapp
        print '<DEBUG>', current_project


        if os.name == 'nt':
            os.environ["MAYA_SCRIPT_PATH"] = "N:\\application_support\\maya\\2016\\scripts"
            python_path = os.environ["PYTHONPATH"]
            os.environ["PYTHONPATH"] = ';'.join([python_path, "N:\\application_support\\maya\\2016\\scripts",
                                                 "N:/application_support/maya/2016/scripts/zync-maya"])
            os.environ["XBMLANGPATH"] = "N:/application_support/maya/2016/scripts/zync-maya"
            os.environ["MAYA_RENDER_SETUP_GLOBAL_PRESETS_PATH"] = "P:/projects/{0}/global/render_presets".format(current_project)
            # sys.path.append('N:\\application_support\\maya\\2016\\scripts\\rebus')
        else:
            os.environ["MAYA_SCRIPT_PATH"] = "/studio/application_support/maya/2016/scripts"
            python_path = os.environ["PYTHONPATH"]
            os.environ["PYTHONPATH"] = ':'.join([python_path, "/studio/application_support/maya/2016/scripts",
                                                 "/studio/application_support/maya/2016/scripts/zync-maya"])
            os.environ["XBMLANGPATH"] = "/studio/application_support/maya/2016/scripts/zync-maya/%B"
            os.environ["MAYA_RENDER_SETUP_GLOBAL_PRESETS_PATH"] = "/productions/projects/{0}/global/render_presets".format(current_project)
            # os.environ["PYTHONPATH"] = "/studio/application_support/maya/2016/scripts"
            # sys.path.append('/studio/application_support/maya/2016/scripts/rebus')

        print '<DEBUG>', os.environ["MAYA_RENDER_SETUP_GLOBAL_PRESETS_PATH"]
