# Copyright (c) 2013 Shotgun Software Inc.
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


class HieroGetShot(Hook):
    """
    Return a Shotgun Shot dictionary for the given Hiero items
    """
    def execute(self, task, item, data, **kwargs):
        """
        Takes a hiero.core.TrackItem as input and returns a data dictionary for
        the shot to update the cut info for.
        """

        # get the parent sequence for the Shot
        sequence = self._get_sequence(item, data)

        # grab shot from Shotgun
        sg = self.parent.shotgun
        filt = [
            ["project", "is", self.parent.context.project],
            ["sg_sequence", "is", sequence],
            ["code", "is", item.name()],
        ]
        fields = kwargs.get("fields", [])
        shots = sg.find("Shot", filt, fields=fields)
        if len(shots) > 1:
            # can not handle multiple shots with the same name
            raise StandardError("Multiple shots named '%s' found", item.name())
        if len(shots) == 0:
            # create shot in shotgun
            shot_data = {
                "code": item.name(),
                "sg_sequence": sequence,
                "project": self.parent.context.project,
            }
            shot = sg.create("Shot", shot_data)
            self.parent.log_info("Created Shot in Shotgun: %s" % shot_data)
        else:
            shot = shots[0]

        # update the thumbnail for the shot
        upload_thumbnail = kwargs.get("upload_thumbnail", True)
        if upload_thumbnail:
            self.parent.execute_hook(
                "hook_upload_thumbnail",
                entity=shot,
                source=item.source(),
                item=item,
                task=kwargs.get("task")
            )

        shot['sg_tc_in'] = self._get_dst_in(item)
        shot['sg_tc_out'] = self._get_dst_out(item)
        # print '<shot>', shot

        return shot

    def _get_sequence(self, item, data):
        """Return the shotgun sequence for the given Hiero items"""
        # stick a lookup cache on the data object.
        if "seq_cache" not in data:
            data["seq_cache"] = {}

        hiero_sequence = item.parentSequence()
        if hiero_sequence.guid() in data["seq_cache"]:
            return data["seq_cache"][hiero_sequence.guid()]

        # sequence not found in cache, grab it from Shotgun
        sg = self.parent.shotgun
        filt = [
            ["project", "is", self.parent.context.project],
            ["code", "is", hiero_sequence.name()],
        ]
        sequences = sg.find("Sequence", filt)
        if len(sequences) > 1:
            # can not handle multiple sequences with the same name
            raise StandardError("Multiple sequences named '%s' found" % hiero_sequence.name())

        if len(sequences) == 0:
            # create the sequence in shotgun
            seq_data = {
                "code": hiero_sequence.name(),
                "project": self.parent.context.project,
            }
            sequence = sg.create("Sequence", seq_data)
            self.parent.log_info("Created Sequence in Shotgun: %s" % seq_data)
        else:
            sequence = sequences[0]

        # update the thumbnail for the sequence
        self.parent.execute_hook("hook_upload_thumbnail", entity=sequence, source=hiero_sequence, item=None)

        # cache the results
        data["seq_cache"][hiero_sequence.guid()] = sequence

        return sequence

    def _timecode_pref_check(self):
        # We need to check the user Preference for 'Timecode > EDL-Style Spreadsheet Timecodes'
        return int(hiero.core.ApplicationSettings().boolValue('useVideoEDLTimecodes'))

    def _get_dst_in(self, trackitem):

        seq = trackitem.parent().parent()
        t_start = seq.timecodeStart()
        fps = seq.framerate()
        dst_in_str = Timecode.timeToString(t_start+trackitem.timelineIn(), fps, Timecode.kDisplayTimecode)
        dst_in_ms = self._timecode_to_ms(dst_in_str, fps.toFloat())

        return dst_in_ms

    def _get_dst_out(self, trackitem):

        seq = trackitem.parent().parent()
        t_start = seq.timecodeStart()
        fps = seq.framerate()
        dst_out_str = Timecode.timeToString(t_start+trackitem.timelineOut() + self._timecode_pref_check(), fps,
                                        Timecode.kDisplayTimecode)
        dst_out_ms = self._timecode_to_ms(dst_out_str, fps.toFloat())

        return dst_out_ms

    def _timecode_to_ms(self, _timecode, fps):

        _timecode_split = _timecode.split(':')
        _timecode_ms = long((int(_timecode_split[0]) * 60 * 60 + int(_timecode_split[1]) * 60 + int(_timecode_split[2])
                        + float(_timecode_split[3]) / fps) * 1000)

        return _timecode_ms

