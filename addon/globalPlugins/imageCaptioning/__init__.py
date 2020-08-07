# Image Captioning global plugin main module
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import globalPluginHandler
from scriptHandler import script
from globalCommands import SCRCAT_VISION
import vision
import ui
from collections import deque, namedtuple
from contentRecog import SimpleTextResult
from visionEnhancementProviders.screenCurtain import ScreenCurtainSettings
from visionEnhancementProviders.imageCaptioning import ImageCaptioning

from ._doImageCaptioning import DoImageCaptioning
from ._resultUI import recognizeNavigatorObject, VirtualResultWindow


def isScreenCurtainEnabled():
	isEnabled = any([x.providerId == ScreenCurtainSettings.getId()
					 for x in vision.handler.getActiveProviderInfos()])
	if isEnabled:
		ui.message("Screen curtain is enabled. Disable screen curtain to use the object detection add-on.")
	return isEnabled


_cachedResults = deque(maxlen=10)


class SpeakResult():
	def __init__(self, result: namedtuple):
		self.result = result
		self.cacheResult()

		ui.message(result.caption)

	def cacheResult(self):
		global _cachedResults
		alreadyCached = False
		for cachedResult in _cachedResults:
			if self.result.imageHash == cachedResult.imageHash:
				alreadyCached = True
				break
		if not alreadyCached:
			_cachedResults.appendleft(self.result)


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		# Translators: Input trigger to perform object detection on focused image
		description=_("Perform image captioning on focused image"),
		category=SCRCAT_VISION,
	)
	def script_imageCaptioning(self, gesture):
		global _cachedResults
		if not isScreenCurtainEnabled():
			x = DoImageCaptioning(SpeakResult)
			filterNonGraphic = ImageCaptioning.getSettings().filterNonGraphicElements
			recognizeNavigatorObject(x, filterNonGraphic=filterNonGraphic, cachedResults=_cachedResults)

	@script(
		description=_("Present image captioning result in a virtual, browseable window"),
		category=SCRCAT_VISION,
	)
	def script_browsePreviousResult(self, gesture):
		global _cachedResults
		lastResult = _cachedResults[0]
		sentenceResult = SimpleTextResult(lastResult.caption)
		resObj = VirtualResultWindow(result=sentenceResult)
		# This method queues an event to the main thread.
		resObj.setFocus()
