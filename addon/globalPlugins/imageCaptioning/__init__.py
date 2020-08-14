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


def isScreenCurtainEnabled():
	isEnabled = any([x.providerId == ScreenCurtainSettings.getId()
					for x in vision.handler.getActiveProviderInfos()])
	if isEnabled:
		ui.message("Screen curtain is enabled. Disable screen curtain to use the object detection add-on.")
	return isEnabled

_lastCalled = 0
def getScriptCount():
	global _lastCalled
	if 0<(time.time() - _lastCalled)<=3:
		_lastCalled = time.time()
		return 1
	else:
		_lastCalled = time.time()
		return 0


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		# Translators: Input trigger to perform object detection on focused image
		description=_("Perform image captioning on focused image"),
		category=SCRCAT_VISION,
	)
	def script_imageCaptioning(self, gesture):
		scriptCount = getScriptCount()
		filterNonGraphic = ImageCaptioning.getSettings().filterNonGraphicElements
		if not isScreenCurtainEnabled():
			if scriptCount==0:
				recognizer = DoImageCaptioning(SpeakResult, time.time())
				recognizeNavigatorObject(recognizer, filterNonGraphic=filterNonGraphic)
			else:
				recognizer = DoImageCaptioning(BrowseableResult, time.time())
				recognizeNavigatorObject(recognizer, filterNonGraphic=filterNonGraphic)
