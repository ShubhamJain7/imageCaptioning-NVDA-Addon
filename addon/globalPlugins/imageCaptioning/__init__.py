# Image Captioning global plugin main module
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import globalPluginHandler
from scriptHandler import script
from globalCommands import SCRCAT_VISION
import scriptHandler
import vision
import ui
from typing import Optional
from visionEnhancementProviders.screenCurtain import ScreenCurtainSettings
from contentRecog.recogUi import RecogResultNVDAObject
from contentRecog import SimpleTextResult

from visionEnhancementProviders.imageCaptioning import ImageCaptioning

from ._doImageCaptioning import DoImageCaptioning
from ._resultUI import recognizeNavigatorObject


def isScreenCurtainEnabled():
	isEnabled = any([x.providerId == ScreenCurtainSettings.getId() for x in vision.handler.getActiveProviderInfos()])
	if isEnabled:
		ui.message("Screen curtain is enabled. Disable screen curtain to use the object detection add-on.")
	return isEnabled

_previousResult:Optional[str] = None


class SpeakResultAndCreateVirtualResultWindow():
	def __init__(self, result:str):
		global _previousResult
		_previousResult = result
		ui.message(result)
		sentenceResult = SimpleTextResult(result)
		resObj = RecogResultNVDAObject(result=sentenceResult)
		# This method queues an event to the main thread.
		resObj.setFocus()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		# Translators: Input trigger to perform object detection on focused image
		description=_("Perform image captioning on focused image"),
		category=SCRCAT_VISION,
		gesture="kb:Alt+NVDA+C",
	)
	def script_imageCaptioning(self, gesture):
		scriptCount = scriptHandler.getLastScriptRepeatCount()
		if not isScreenCurtainEnabled():
			x = DoImageCaptioning(SpeakResultAndCreateVirtualResultWindow)
			filterNonGraphic = ImageCaptioning.getSettings().filterNonGraphicElements
			recognizeNavigatorObject(x, filterNonGraphic)

	@script(
		description=_("Present image captioning result again"),
		category=SCRCAT_VISION,
		gesture="kb:Alt+NVDA+R",
	)
	def script_speakPreviousResult(self, gesture):
		global _previousResult
		SpeakResultAndCreateVirtualResultWindow(_previousResult)