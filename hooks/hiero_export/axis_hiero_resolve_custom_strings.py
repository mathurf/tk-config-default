# Copyright (c) 2014 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from hiero.core import *
from hiero.ui import *
from tank import Hook


class HieroResolveCustomStrings(Hook):
    """Translates a keyword string into its resolved value for a given task."""
    # cache of shots that have already been pulled from shotgun
    # _sg_lookup_cache = {}

    GBL_TIMECODE_TOKEN_NAME = "{gbl_timecode}"

    def execute(self, task, keyword, **kwargs):
        """
        The default implementation of the custom resolver simply looks up
        the keyword from the shotgun shot dictionary.

        For example, to pull the shot code, you would simply specify 'code'.
        To pull the sequence code you would use 'sg_sequence.Sequence.code'.
        """
        """
        shot_code = task._item.name()

        # grab the shot from the cache, or the get_shot hook if not cached
        sg_shot = self._sg_lookup_cache.get(shot_code)
        if sg_shot is None:
            fields = [ctf['keyword'] for ctf in self.parent.get_setting('custom_template_fields')]
            sg_shot = self.parent.execute_hook(
                "hook_get_shot",
                task=task,
                item=task._item,
                data=self.parent.preprocess_data,
                fields=fields,
                upload_thumbnail=False,
            )

            self._sg_lookup_cache[shot_code] = sg_shot

        if sg_shot is None:
            raise RuntimeError("Could not find shot for custom resolver: %s" % keyword)

        # strip off the leading and trailing curly brackets
        keyword = keyword[1:-1]
        result = sg_shot.get(keyword, "")

        self.parent.log_debug("Custom resolver: %s[%s] -> %s" % (shot_code, keyword, result))

        return result
        """

        self.parent.log_debug("attempting to resolve custom keyword: %s" % keyword)
        if keyword == self.GBL_TIMECODE_TOKEN_NAME:
            translated_value = self._get_dst_in(task._item)
        else:
            raise RuntimeError("No translation handler found for custom_template_field: %s" % keyword)

        self.parent.log_debug("Custom resolver: %s -> %s" % (keyword, translated_value))

        # translated_value = 'timecode_test'

        return translated_value

    def _timecode_pref_check(self):
        # We need to check the user Preference for 'Timecode > EDL-Style Spreadsheet Timecodes'
        return int(hiero.core.ApplicationSettings().boolValue('useVideoEDLTimecodes'))

    def _get_dst_in(self, trackitem):

        seq = trackitem.parent().parent()
        t_start = seq.timecodeStart()
        fps = seq.framerate()
        dst_in_str = Timecode.timeToString(t_start+trackitem.timelineIn(), fps, Timecode.kDisplayTimecode)

        return dst_in_str

