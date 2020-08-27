# Image Captioning global plugin main module
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import globalPluginHandler
from scriptHandler import script
from globalCommands import SCRCAT_VISION
import vision
import ui
import time
from visionEnhancementProviders.screenCurtain import ScreenCurtainSettings
from visionEnhancementProviders.imageCaptioning import ImageCaptioning

from ._doImageCaptioning import DoImageCaptioning
from ._resultUI import recognizeNavigatorObject, SpeakResult, BrowseableResult


def isScreenCurtainEnabled() -> bool:
	"""Checks if screen curtain is currently enabled or not. Speaks message if it is enabled.
	@return: True if screen curtain is enabled else False
	"""
	isEnabled = any([x.providerId == ScreenCurtainSettings.getId() for x in vision.handler.getActiveProviderInfos()])
	if isEnabled:
		#Translators: reported when the user tries to start a recognition process while the screen curtain
		# is enabled
		ui.message(
			_("Screen curtain is enabled. Disable screen curtain to use the object detection add-on.")
		)
	return isEnabled


# Stores timestamp of when the script was last called. Initially set to zero.
_lastCalled = 0

def recentlyCalled() -> bool:
	"""Checks if the global plugin script was called in the last three seconds or not.
	@return: True if script was called in the last three seconds, else False
	"""
	global _lastCalled
	if (time.time() - _lastCalled) <= 3:
		_lastCalled = time.time()
		return True
	else:
		_lastCalled = time.time()
		return False


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		# Translators: Input trigger to perform object detection on focused image
		description=_("Perform image captioning on focused image. Press once to speak result, more than "
					"once to present result in a virtual window."),
		category=SCRCAT_VISION,
	)
	def script_imageCaptioning(self, gesture):
		wasRecentlyCalled = recentlyCalled()
		# get filterNonGraphic preference
		filterNonGraphic = ImageCaptioning.getSettings().filterNonGraphicElements

		# If the screen curtain is enabled, a screenshot of the element will only contain black pixels.
		# Such an image won't produce good results so inform the user and quit.
		if not isScreenCurtainEnabled():
			# Script not called in the last 3 seconds so use SpeakResult as resultHandlerClass
			if not wasRecentlyCalled:
				recognizer = DoImageCaptioning(SpeakResult, time.time())
				recognizeNavigatorObject(recognizer, filterNonGraphic=filterNonGraphic)
			# Script was called in the last 3 seconds so the user probably pressed the gesture multiple
			# times and wants the result to be presented in a virtual result window.
			else:
				recognizer = DoImageCaptioning(BrowseableResult, time.time())
				recognizeNavigatorObject(recognizer, filterNonGraphic=filterNonGraphic)
