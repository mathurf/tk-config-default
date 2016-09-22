import sgtk
import os

# toolkit will automatically resolve the base class for you
# this means that you will derive from the default hook that comes with the app
HookBaseClass = sgtk.get_hook_baseclass()
print HookBaseClass

class MyActions(HookBaseClass):

    def generate_actions(self, sg_data, actions, ui_area):
        """
        Returns a list of action instances for a particular object.
        The data returned from this hook will be used to populate the
        actions menu.

        The mapping between Shotgun objects and actions are kept in a different place
        (in the configuration) so at the point when this hook is called, the app
        has already established *which* actions are appropriate for this object.

        This method needs to return detailed data for those actions, in the form of a list
        of dictionaries, each with name, params, caption and description keys.

        Because you are operating on a particular object, you may tailor the output
        (caption, tooltip etc) to contain custom information suitable for this publish.

        The ui_area parameter is a string and indicates where the publish is to be shown.

        - If it will be shown in the main browsing area, "main" is passed.
        - If it will be shown in the details area, "details" is passed.

        :param sg_data: Shotgun data dictionary with all the standard publish fields.
        :param actions: List of action strings which have been defined in the app configuration.
        :param ui_area: String denoting the UI Area (see above).
        :returns List of dictionaries, each with keys name, params, caption and description
        """

        # get the actions from the base class first
        action_instances = super(MyActions, self).generate_actions(sg_data, actions, ui_area)
        # print '<DEBUG> ', actions

        if "play_in_rv" in actions:
            action_instances.append({"name": "play_in_rv",
                                     "params": None,
                                     "caption": "Play in RV",
                                     "description": "Play version in RV."})

        # print '<DEBUG> ', action_instances

        return action_instances

    def execute_action(self, name, params, sg_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.

        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_data: Shotgun data dictionary with all the standard publish fields.
        :returns: No return value expected.
        """

        if name == "play_in_rv":
            # Set temp path for movie
            connection = self.parent.shotgun
            if os.name == 'nt':
                path = ''.join([os.environ["TMP"],'\\',sg_data['sg_uploaded_movie']['name']])
            else:
                path = ''.join([os.environ["TMPDIR"],'/',sg_data['sg_uploaded_movie']['name']])

            # Find version
            version = connection.find_one('Version', [['id', 'is', sg_data['id']]], ['sg_uploaded_movie'])
            try:
                # Download version
                attachment = connection.download_attachment(attachment=version['sg_uploaded_movie'], file_path=path)
                # Load version into RV
                commandline = ''.join(['rv.exe ','\"',attachment,'\"'])
                # Run commandline
                print commandline
                os.system(commandline)
            except:
                print "Failed to play version in RV. Check env variable PATH contains RV path."
                return

            # Remove attachment
            os.remove(attachment)
        else:
            # call base class implementation
            super(MyActions, self).execute_action(name, params, sg_data)