# Image Captioning model runner
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import os
import threading
import tempfile
from typing import Any
from collections import namedtuple

import wx
import ui
import contentRecog
from logHandler import log
from controlTypes import ROLE_GRAPHIC
from locationHelper import RectLTWH

from ._sayLookTell import SayLookTellCaptioning

#: Elements with width or height small than this value will not be processed
_sizeThreshold = 128


class DoImageCaptioning(contentRecog.ContentRecognizer):
	"""Recognizer class that is responsible for calling the ImageCaptioning DLL that performs
	image captioning."""
	def __init__(self, resultHandlerClass, timeCreated):
		"""
		@param resultHandlerClass: class that contains code for handling image captioning result
		@param timeCreated: stores timestamp of when an instance of this class was created
		"""
		self.resultHandlerClass = resultHandlerClass
		self.timeCreated = timeCreated
		# Set to True only if Focus mode is enabled
		self.checkChildren = False

	def recognize(self, imageHash, pixels, imgInfo, onResult):
		""" Starts the image detection process on a new thread and sets the I{onResult} method
		@param imageHash: hash used to uniquely identify the recognized image
		@param pixels: 2D array of RGBAQUAD values that store image pixels
		@param imgInfo: stores details of the image to be recognized
		@param onResult: Function that defines logic for what to do when result is obtained
		"""
		self.imageHash = imageHash
		self.imgInfo = imgInfo
		# Copy pixels to empty bitmap and save it as a temporary jpeg image
		bmp = wx.EmptyBitmap(imgInfo.recogWidth, imgInfo.recogHeight, 32)
		bmp.CopyFromBuffer(pixels, wx.BitmapBufferFormat_RGB32)
		self._imagePath = tempfile.mktemp(prefix="nvda_ImageCaption_", suffix=".jpg")
		bmp.SaveFile(self._imagePath, wx.BITMAP_TYPE_JPEG)
		# Set L{onResult} method
		self._onResult = onResult
		# Start image captioning on separate thread
		t = threading.Thread(target=self._bgRecog)
		t.daemon = True
		t.start()

	def _bgRecog(self):
		"""Handles the image captioning process thread and calls L{onResult} when the result is ready."""
		try:
			result = self.detect(self._imagePath)
		except Exception as e:
			result = e
		finally:
			# Delete temporary image file since we don't need it anymore
			os.remove(self._imagePath)
		if self._onResult:
			self._onResult(result)

	def cancel(self):
		"""Cancels image captioning process
		@note: process runs but nothing is done on completion."""
		self._onResult = None

	def detect(self, imagePath):
		""" Gets the object detection results and returns it
		@param imagePath: file system path to input image
		@return: named tuple with attributes: imageHash and caption
		"""
		caption = SayLookTellCaptioning(imagePath).getCaption()
		detectionResult = namedtuple('Detection', ['imageHash', 'caption'])
		result = detectionResult(self.imageHash, caption)
		return result

	def validateObject(self, obj) -> bool:
		"""Checks if the focus or navigator object or any of its children (only in case of focus objects)
		are graphic. If invalid, a message is presented to the user.
		@param obj: focus/navigator object to be validated
		@return: True is object is valid else False
		"""
		if obj.role != ROLE_GRAPHIC:
			# If in focus mode, check if at least one child of the object is graphic because the focus
			# object itself will not be graphic.
			if self.checkChildren:
				for child in obj.children:
					if child.role == ROLE_GRAPHIC:
						return True
			# Translators: Reported when the focused element is not an image and the filterNonGraphic
			# option in the Setting is enabled.
			ui.message(
				_("Currently focused element is not an image. Please try again with an image element or "
				"change your add-on settings.")
			)
			log.debug(f"(imageCaptioning) Focused object role:{obj.role}")
			return False
		return True

	def validateBounds(self, location: RectLTWH) -> bool:
		"""Checks the bounds of the object to be recognized are greater than the minimum value. If not, a
		message is presented to the user.
		@param location: stores the screen co-ordinates and dimensions of the image object to be recognized
		@return: True is object size is greater than the minimum value, false otherwise
		"""
		# object must be greater than the size threshold in at least one dimension
		if location.width < _sizeThreshold or location.height < _sizeThreshold:
			# Translators: Reported when the size focused element is too small to produce good results.
			ui.message(_("Image too small to produce good results. Please try again with a larger image."))
			log.debug(f"(imageCaptioning) Capture bounds: width={location.width}, height={location.height}.")
			return False
		return True

	def getResultHandler(self, result: Any):
		"""Returns an instance of the L{resultHandlerClass} instantiated with the image captioning result.
		@param result: The image captioning result
		@return: instance of I{self.resultHandlerClass}
		"""
		return self.resultHandlerClass(result)
