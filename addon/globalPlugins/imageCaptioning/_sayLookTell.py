# Image Captioning model DLL interface
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import os
from ctypes import *


class SayLookTellCaptioning():
	"""Class that interfaces with the ImageCaptioning DLL that performs image captioning. Responsible for
	converting results to appropriate formats and ensuring DLL dependencies are satisfied."""
	def __init__(self, imagePath):
		""" Defines paths to all the required files (image, DLLs and model files)
		@param imagePath: path to image to be recognized
		"""
		self.imagePath = imagePath
		self.baseDir = os.path.abspath(os.path.dirname(__file__))
		self.encoderPath = self.baseDir + "\\data\\encoder.onnx"
		self.decoderPath = self.baseDir + "\\data\\decoder.onnx"
		self.vocabPath = self.baseDir + "\\data\\vocab.txt"
		# Must be in dependency order (ie. A<-B<-C where C depends on B and B depends on A).
		self.dllPaths = ["\\dlls\\opencv_core430.dll", "\\dlls\\opencv_imgproc430.dll",
						"\\dlls\\opencv_imgcodecs430.dll", "\\dlls\\onnxruntime.dll",
						"\\dlls\\ImageCaptioning-DLL.dll"]
		self.dllPaths = [self.baseDir + dllPath for dllPath in self.dllPaths]
		self._checkFiles()

	def _checkFiles(self):
		"""Checks if all the required files are present. Raises a L{FileNotFoundError} if any file is
		missing"""
		notFound = ""
		if not os.path.exists(self.imagePath):
			notFound = notFound + f'imageCaptioning: Image file not found at {self.imagePath}'

		if not os.path.exists(self.encoderPath):
			notFound = notFound + f'\nimageCaptioning: Encoder model file not found at {self.encoderPath}'

		if not os.path.exists(self.decoderPath):
			notFound = notFound + f'\nimageCaptioning: Decoder model file not found at {self.decoderPath}'

		for dllPath in self.dllPaths:
			if not os.path.exists(dllPath):
				notFound = notFound + f'\nimageCaptioning: DLL file not found at {dllPath}'

		if notFound != "":
			raise FileNotFoundError(notFound)

	def _loadDLLs(self):
		"""Loads all the DLL files."""
		# loads all the DLLs required by the ImageCaptioning DLL
		for dllPath in self.dllPaths[:-1]:
			_ = CDLL(dllPath)

		# load the ImageCaptioning DLL
		lib = CDLL(self.dllPaths[-1])
		return lib

	def _getResult(self, lib) -> str:
		"""Calls the DLL public methods and gets the image captioning results.
		@return: generated caption
		"""
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

	def getCaption(self) -> str:
		"""Performs image captioning on input image and returns the resulting caption
		@return: caption
		"""
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
