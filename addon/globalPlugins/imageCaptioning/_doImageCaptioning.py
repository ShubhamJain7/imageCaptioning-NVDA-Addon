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
	def __init__(self, resultHandlerClass, timeCreated):
		self.resultHandlerClass = resultHandlerClass
		self.timeCreated = timeCreated
		self.checkChildren = False

	def recognize(self, imageHash, pixels, imgInfo, onResult):
		self.imageHash = imageHash
		self.imgInfo = imgInfo
		bmp = wx.EmptyBitmap(imgInfo.recogWidth, imgInfo.recogHeight, 32)
		bmp.CopyFromBuffer(pixels, wx.BitmapBufferFormat_RGB32)
		self._imagePath = tempfile.mktemp(prefix="nvda_ImageCaption_", suffix=".jpg")
		bmp.SaveFile(self._imagePath, wx.BITMAP_TYPE_JPEG)
		self._onResult = onResult
		t = threading.Thread(target=self._bgRecog)
		t.daemon = True
		t.start()

	def _bgRecog(self):
		try:
			result = self.detect(self._imagePath)
		except Exception as e:
			result = e
		finally:
			os.remove(self._imagePath)
		if self._onResult:
			self._onResult(result)

	def cancel(self):
		self._onResult = None

	def detect(self, imagePath):
		caption = SayLookTellCaptioning(imagePath).getCaption()
		detectionResult = namedtuple('Detection', ['imageHash', 'caption'])
		result = detectionResult(self.imageHash, caption)
		return result

	def validateObject(self, obj):
		if obj.role != ROLE_GRAPHIC:
			# If in focus mode, check if at least one child of the object is graphic because the focus
			# object itself will not be graphic.
			if self.checkChildren:
				for child in obj.children:
					if child.role == ROLE_GRAPHIC:
						return True
			ui.message("Currently focused element is not an image. Please try again with an image element "
					"or change your add-on settings.")
			log.debug(f"(imageCaptioning) Focused object role:{obj.role}")
			return False
		return True

	def validateBounds(self, location: RectLTWH):
		if location.width < _sizeThreshold or location.height < _sizeThreshold:
			ui.message("Image too small to produce good results. Please try again with a larger image.")
			log.debug(f"(imageCaptioning) Capture bounds: width={location.width}, height={location.height}.")
			return False
		return True

	def getResultHandler(self, result: Any):
		return self.resultHandlerClass(result)
