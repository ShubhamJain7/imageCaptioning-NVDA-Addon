# Image Captioning navigator object recognition, recognition tracking, result presentation and result caching
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import api
import ui
import screenBitmap
from logHandler import log
from typing import Optional
import queueHandler
from contentRecog import ContentRecognizer, RecogImageInfo, SimpleTextResult
from contentRecog.recogUi import RecogResultNVDAObject
from collections import deque, namedtuple
import time

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


class BrowseableResult():
	def __init__(self, result: namedtuple):
		self.result = result
		self.cacheResult()

		sentenceResult = SimpleTextResult(result.caption)
		resObj = RecogResultNVDAObject(result=sentenceResult)
		resObj.setFocus()

	def cacheResult(self):
		global _cachedResults
		alreadyCached = False
		for cachedResult in _cachedResults:
			if self.result.imageHash == cachedResult.imageHash:
				alreadyCached = True
				break
		if not alreadyCached:
			_cachedResults.appendleft(self.result)


#: Keeps track of the recognition in progress, if any.
_activeRecog: Optional[ContentRecognizer] = None


def recognizeNavigatorObject(recognizer, filterNonGraphic=True):
	"""User interface function to recognize content in the navigator object.
	This should be called from a script or in response to a GUI action.
	@param recognizer: The content recognizer to use.
	@type recognizer: L{contentRecog.ContentRecognizer}
	"""
	global _activeRecog
	if isinstance(api.getFocusObject(), RecogResultNVDAObject):
		# Translators: Reported when content recognition (e.g. OCR) is attempted,
		# but the user is already reading a content recognition result.
		ui.message(_("Already in a content recognition result"))
		return
	nav = api.getNavigatorObject()
	if filterNonGraphic and not recognizer.validateObject(nav):
		return
	# Translators: Reported when content recognition (e.g. OCR) is attempted,
	# but the content is not visible.
	notVisibleMsg = _("Content is not visible")
	try:
		left, top, width, height = nav.location
	except TypeError:
		log.debugWarning("Object returned location %r" % nav.location)
		ui.message(notVisibleMsg)
		return
	if not recognizer.validateBounds(nav.location):
		return
	try:
		imgInfo = RecogImageInfo.createFromRecognizer(left, top, width, height, recognizer)
	except ValueError:
		ui.message(notVisibleMsg)
		return

	if _activeRecog:
		if (0 < (time.time() - _activeRecog.timeCreated) <= 3) and (
				_activeRecog.resultHandlerClass != BrowseableResult):
			_activeRecog.resultHandlerClass = BrowseableResult
			ui.message(_("Recognizing"))
		else:
			ui.message("Already running an image captioning process. Please try again later.")
		return

	sb = screenBitmap.ScreenBitmap(imgInfo.recogWidth, imgInfo.recogHeight)
	pixels = sb.captureImage(left, top, width, height)

	rowHashes = []
	for i in range(imgInfo.recogWidth):
		row = []
		for j in range(imgInfo.recogHeight):
			row.append(pixels[j][i].rgbRed)  # column major order
		rowHashes.append(hash(str(row)))

	global _cachedResults
	imageHash = hash(str(rowHashes))
	for result in _cachedResults:
		if result[0] == imageHash:
			handler = recognizer.getResultHandler(result)
			return

	ui.message(_("Recognizing"))
	_activeRecog = recognizer

	recognizer.recognize(imageHash, pixels, imgInfo, _recogOnResult)


def _recogOnResult(result):
	global _activeRecog
	recognizer: ContentRecognizer = _activeRecog
	_activeRecog = None
	# This might get called from a background thread, so any UI calls must be queued to the main thread.
	if isinstance(result, Exception):
		# Translators: Reported when recognition (e.g. OCR) fails.
		log.error("Recognition failed: %s" % result)
		queueHandler.queueFunction(queueHandler.eventQueue, ui.message, _("Recognition failed"))
		return
	if recognizer:
		handler = recognizer.getResultHandler(result)
