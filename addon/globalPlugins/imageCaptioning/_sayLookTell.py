# Image Captioning model DLL interface
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import os
from ctypes import *


class SayLookTellCaptioning():

	def __init__(self, imagePath):
		self.baseDir = os.path.abspath(os.path.dirname(__file__))

		if not os.path.exists(imagePath):
			return None
		else:
			self.imagePath = imagePath

		self.encoderPath = self.baseDir + "\\data\\encoder.onnx"
		self.decoderPath = self.baseDir + "\\data\\decoder.onnx"
		self.vocabPath = self.baseDir + "\\data\\vocab.txt"
		self.dllPaths = ["\\dlls\\opencv_core430.dll", "\\dlls\\opencv_imgproc430.dll",
						"\\dlls\\opencv_imgcodecs430.dll", "\\dlls\\onnxruntime.dll",
						"\\dlls\\ImageCaptioning-DLL.dll"]
		self.dllPaths = [self.baseDir + dllPath for dllPath in self.dllPaths]

	def _checkFiles(self):
		notFound = ""
		if not os.path.exists(self.encoderPath):
			notFound = notFound + f'imageCaptioning: Encoder model file not found at {self.encoderPath}'

		if not os.path.exists(self.decoderPath):
			notFound = notFound + f'\nimageCaptioning: Decoder model file not found at {self.decoderPath}'

		for dllPath in self.dllPaths:
			if not os.path.exists(dllPath):
				notFound = notFound + f'\nimageCaptioning: DLL file not found at {dllPath}'

		if notFound != "":
			raise FileNotFoundError(notFound)

	def _loadDLLs(self):
		# load dependant DLLs
		for dllPath in self.dllPaths[:-1]:
			_ = CDLL(dllPath)

		# load required DLL
		lib = CDLL(self.dllPaths[-1])
		return lib

	def _getResult(self, lib):
		# define return type and arguments of 'doDetection' function
		lib.doDetection.restype = c_int
		lib.doDetection.argtypes = [c_wchar_p, c_wchar_p, c_char_p, c_char_p]

		# call 'doDetection' function and get length of result
		res = lib.doDetection(c_wchar_p(self.encoderPath), c_wchar_p(self.decoderPath),
							c_char_p(self.vocabPath.encode('utf-8')), c_char_p(self.imagePath.encode('utf-8')))

		# continue if there is a result
		if res != 0:
			# define return type and arguments of 'getCaption' function
			lib.getCaption.restype = c_int
			lib.getCaption.argtypes = [c_char_p, c_size_t]

			# define string buffer to store caption and call 'getCaption' function
			caption = create_string_buffer(res)
			size = lib.getCaption(caption, res)

			# get only relevant portion of byte string and decode it
			stringCaption = (caption.raw[:size - 1]).decode('utf-8')
			return stringCaption
		else:
			return None

	def getCaption(self):
		lib = self._loadDLLs()
		result = self._getResult(lib)
		if not result:
			return "Could not generate a caption for the image."
		caption = ""
		for word in result.split():
			if "<" not in word and word != ".":
				caption = caption + f'{word} '
		caption = caption.strip() + "."
		return caption
