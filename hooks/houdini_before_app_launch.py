"""
[Rob]
This script runs before houdini launches, and serializes the current SG context within various env VARs
These can then be read by the axis launcher script. 
"""

import os
import sys
import tank
#import pickle
import logging
import time

class BeforeAppLaunch(tank.Hook):
	if os.name == 'nt':
		LOG_PATH = 'C:/logs/'
		if not os.path.isdir(LOG_PATH):
			os.makedirs(LOG_PATH)
		LOG_FILENAME = '%shoudini_launch.log' %LOG_PATH
	else:
		LOG_FILENAME = '/tmp/houdini_launch.log'
	logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
	currenttime = time.asctime(time.localtime(time.time()))
	logging.debug('\n')
	logging.debug('==============================================')
	logging.debug('Running before_app_launch at: %s', currenttime)

	def execute(self, **kwargs):
		os.environ["TANK_CONTEXT"] = tank.context.serialize(self.parent.context)		
		connection = self.parent.shotgun
		logging.debug('connection: %s' % connection)
		
		project = self.parent.context.project
		logging.debug('project: %s' % project)

		version = connection.find_one("Project", [["id", "is", project['id']]], fields=["sg_houdiniversion"]).get("sg_houdiniversion")
		os.environ["HOUDINI_VERSION"] = version
		logging.debug('Houdini Version : %s' % os.getenv('HOUDINI_VERSION'))
		
		sg_fps = connection.find_one("Project", [["id", "is", project['id']]], fields=["sg_projectfps"]).get("sg_projectfps")
		os.environ["SG_FPS"] = str(sg_fps)
		logging.debug('Project FPS : %s' % os.getenv('SG_FPS'))

		sg_resx = connection.find_one("Project", [["id", "is", project['id']]], fields=["sg_resx"]).get("sg_resx")
		os.environ["SG_RESX"] = str(sg_resx)
		logging.debug('project Res X : %s' % os.getenv('SG_RESX'))

		sg_resy = connection.find_one("Project", [["id", "is", project['id']]], fields=["sg_resy"]).get("sg_resy")
		os.environ["SG_RESY"] = str(sg_resy)
		logging.debug('Project Res Y: %s' % os.getenv('SG_RESY'))

		sg_tankName = connection.find_one("Project", [["id", "is", project['id']]], fields=["tank_name"]).get("tank_name")
		os.environ["TANKNAME"] = str(sg_tankName)
		logging.debug('Tank Name : %s' % os.getenv('TANKNAME'))
		
		sg_code = connection.find_one("Project", [["id", "is", project['id']]], fields=["sg_code"]).get("sg_code")
		os.environ["SG_CODE"] = str(sg_code)
		logging.debug('Project Code : %s' % os.getenv('SG_CODE'))

        # following section taken from hmaster_launch.py in ../houdiniSettings/axis_tools
		osenv = sys.platform

		if ('linux' in osenv) or ('darwin' in osenv):
			os.environ['h_path'] = '/opt/hfs15.0.416'
			os.environ[
				'otl_base'] = '/studio/application_support/glasgow_PipelineTools/plugins/axis/houdiniTools/houdiniTools_v15.7'
			os.environ['HOUDINI_OTLSCAN_PATH'] = os.path.expandvars(
				'$otl_base/otls/3rdParty:$otl_base/otls/animTransfer:'
				'$otl_base/otls/furtools:$otl_base/otls/fx:'
				'$otl_base/otls/lightingTools:$otl_base/otls/objTools:'
				'$otl_base/otls/renderingTools:$otl_base/otls/Shaders:'
				'$otl_base/otls/sops:$h_path/houdini/otls:@')
			os.environ['HOUDINI_VOP_DEFINITIONS_PATH'] = os.path.expandvars('$otl_base/vop:$h_path/houdini/vop')
			os.environ['HOUDINI_GALLERY_PATH'] = os.path.expandvars('$otl_base/gallery:$h_path/houdini/gallery')
			os.environ['HOUDINI_PATH'] = ':'.join([os.environ['HOUDINI_PATH'], os.path.expandvars(
				'$HOME/houdini15.0;$otl_base;$otl_base/config;$h_path/houdini;$h_path/bin;@')])
			os.environ['HOUDINI_UI_ICON_PATH'] = os.path.expandvars('$h_path/houdini/config/Icons')
			os.environ['HOUDINI_DESKTOP_DIR'] = os.path.expandvars('$h_path/houdini/desktop')
			#filepath = os.path.expandvars('$h_path/bin/hescape')
			#subprocess.call(filepath, shell=True, universal_newlines=True)
		else:
			os.environ['h_path'] = 'C:/appnet/applications/houdini/15.0.416'
			os.environ[
				'otl_base'] = 'N:/application_support/glasgow_PipelineTools/plugins/axis/houdiniTools/houdiniTools_v15.7'
			os.environ['HOUDINI_OTLSCAN_PATH'] = os.path.expandvars(
				'$otl_base/otls/3rdParty;$otl_base/otls/animTransfer;'
				'$otl_base/otls/furtools;$otl_base/otls/fx;'
				'$otl_base/otls/lightingTools;$otl_base/otls/objTools;'
				'$otl_base/otls/renderingTools;$otl_base/otls/Shaders;'
				'$otl_base/otls/sops;$h_path/houdini/otls;@')
			os.environ['HOUDINI_VOP_DEFINITIONS_PATH'] = os.path.expandvars('$otl_base/vop;$h_path/houdini/vop')
			os.environ['HOUDINI_GALLERY_PATH'] = os.path.expandvars('$otl_base/gallery;$h_path/houdini/gallery')
			os.environ['HOUDINI_PATH'] = ';'.join([os.environ['HOUDINI_PATH'], os.path.expandvars(
				'$HOME/houdini15.0;$otl_base;$otl_base/config;$h_path/houdini;$h_path/bin;@')])
			os.environ['HOUDINI_UI_ICON_PATH'] = os.path.expandvars('$h_path/houdini/config/Icons')
			os.environ['HOUDINI_DESKTOP_DIR'] = os.path.expandvars('$h_path/houdini/desktop')
			#filepath = os.path.expandvars('$h_path/bin/hescape.exe')
			#subprocess.Popen(filepath)

		# print filepath
		# for key in os.environ.keys():
		#    print "%30s %s \n" % (key,os.environ[key])
		
		logging.debug('\n')
		logging.debug('==============================================')
		logging.debug('\n')