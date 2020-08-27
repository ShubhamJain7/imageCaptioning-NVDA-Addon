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
	"""ResultHandlerClass that speaks the obtained image captioning result."""
	def __init__(self, result: namedtuple):
		"""Calls methods that cache the result and speak it.
		@param result: image captioning result
		"""
		self.result = result
		self.cacheResult()
		self.presentResult()

	def presentResult(self):
		"""Speaks the caption"""
		ui.message(self.result.caption)

	def cacheResult(self):
		"""Caches the result in _cachedResults unless it is already cached. The result may already be
		cached since the same ResultHandlerClass is used to present result in case of cache hits.
		"""
		global _cachedResults
		alreadyCached = False
		for cachedResult in _cachedResults:
			if self.result.imageHash == cachedResult.imageHash:
				alreadyCached = True
				break
		if not alreadyCached:
			_cachedResults.appendleft(self.result)


class BrowseableResult():
	"""ResultHandlerClass that presents the obtained image captioning result in a virtual window."""
	def __init__(self, result: namedtuple):
		"""Calls methods that cache the result and present it in a virtual window.
		@param result: image captioning result
		"""
		self.result = result
		self.cacheResult()
		self.presentResults()

	def presentResults(self):
		"""converts the caption from string to L{SimpleTextResult}, create a virtual result window
		using it and set focus onto the window."""
		sentenceResult = SimpleTextResult(self.result.caption)
		resObj = RecogResultNVDAObject(result=sentenceResult)
		resObj.setFocus()

	def cacheResult(self):
		"""Caches the result in _cachedResults unless it is already cached. The result may already be
		cached since the same ResultHandlerClass is used to present result in case of cache hits.
		"""
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
	if isinstance(api.getFocusObject(), RecogResultNVDAObject):
		# Translators: Reported when content recognition is attempted, but the user is already reading a
		# content recognition result.
		ui.message(_("Already in a content recognition result"))
		return

	# Get the object that currently has system focus
	obj = api.getFocusObject()
	# treeInterceptor may be None is some cases. If so, use the navigator object instead.
	if obj.treeInterceptor:
		isFocusModeEnabled = obj.treeInterceptor.passThrough
		# if Focus mode is enabled we must check if any child of the focus object is graphic because it
		# itself cannot be graphic
		if isFocusModeEnabled:
			recognizer.checkChildren = True
		# if focus mode is disabled, use the navigator object
		else:
			obj = api.getNavigatorObject()
	else:
		obj = api.getNavigatorObject()

	# if filterNonGraphic True, validate the object. If invalid end the recognition process
	if filterNonGraphic and not recognizer.validateObject(obj):
		return
	# Translators: Reported when content recognition is attempted, but the content is not visible.
	notVisibleMsg = _("Content is not visible")
	try:
		left, top, width, height = obj.location
	except TypeError:
		log.debugWarning("Object returned location %r" % obj.location)
		ui.message(notVisibleMsg)
		return
	# If the object bounds are not valid, end the recognition process.
	if not recognizer.validateBounds(obj.location):
		return
	try:
		imgInfo = RecogImageInfo.createFromRecognizer(left, top, width, height, recognizer)
	except ValueError:
		ui.message(notVisibleMsg)
		return

	global _activeRecog
	if _activeRecog:
		# If a recognition process is already occurring and a new one is started after more than 3 seconds,
		# warn the user and block the new recognition process. If the delay is less than 3 seconds, the
		# user probably pressed the gesture multiple times so cancel the old process and let the new one
		# continue. Cancelling the old process results in errors that cause both recognition processes to
		# fail so we just update the resultHandlerClass of the previous recognition process instead of
		# cancelling it and end the new recognition process here.
		if ((time.time() - _activeRecog.timeCreated) <= 3) and (
				_activeRecog.resultHandlerClass != BrowseableResult):
			_activeRecog.resultHandlerClass = BrowseableResult
			# Translators: Reporting when content recognition begins.
			ui.message(_("Recognizing"))
		else:
			ui.message("Already running an image captioning process. Please try again later.")
		return

	# capture object pixels
	sb = screenBitmap.ScreenBitmap(imgInfo.recogWidth, imgInfo.recogHeight)
	pixels = sb.captureImage(left, top, width, height)

	# calculate L{imageHash} using the inbuilt hash function. Only one channel is used to calculate the
	# hash to save time but all pixels in that channel must be used since using only part of the image may
	# cause false cache hits for images with padding.
	rowHashes = []
	for i in range(imgInfo.recogWidth):
		row = []
		for j in range(imgInfo.recogHeight):
			row.append(pixels[j][i].rgbRed)  # column major order
		rowHashes.append(hash(str(row)))
	imageHash = hash(str(rowHashes))

	global _cachedResults
	# check if the hash of the current object matches that of any previous result
	for result in _cachedResults:
		# if a match is found, call the recognizer's I{getResultHandler} method with the cached result and
		# end the current recognition process here.
		if result[0] == imageHash:
			handler = recognizer.getResultHandler(result)
			return

	# Translators: Reporting when content recognition begins.
	ui.message(_("Recognizing"))
	# Store a copy of the recognizer before image captioning really starts. This can also be used to check
	# recognition process is active
	_activeRecog = recognizer

	recognizer.recognize(imageHash, pixels, imgInfo, _recogOnResult)


def _recogOnResult(result):
	"""Presents the image captioning result whether successful or not.
	@param result: image captioning result
	"""
	global _activeRecog
	# Create a local copy of the active recognizer for later use and set original to L{None} so new
	# recognition processes may be started.
	recognizer: ContentRecognizer = _activeRecog
	_activeRecog = None
	# This might get called from a background thread, so any UI calls must be queued to the main thread.
	if isinstance(result, Exception):
		# Translators: Reported when recognition fails.
		log.error("Recognition failed: %s" % result)
		queueHandler.queueFunction(queueHandler.eventQueue, ui.message, _("Recognition failed"))
		return
	# Call the recognizer's L{getResultHandler} method. The __init__ method of the L{ResultHandlerClass}
	# usually contains code that presents the result to the user and so the result is presented when this
	# method is called.
	if recognizer:
		handler = recognizer.getResultHandler(result)
