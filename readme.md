# Image Captioning Add-on

* Author: Shubham Dilip Jain
* Download: https://github.com/ShubhamJain7/imageCaptioning-NVDA-Addon/releases

This add-on allows users to perform image captioning on image elements present on their screen and get a caption that describes the image in English. The result is announced to the user and if the user wishes, can be presented in a virtual, browseable window that allows users to access the result character-by-character, word-by-word, as a whole and even copy the result. This add-on works well only with "natural images" of people, animals and common-objects.

### Usage
----
After installing, the user must first set their preferred gestures at __Preferences->Input gestures->Vision__. There are only two gestures, one for performing detection on a currently focused image and another for accessing the result in a virtual, browseable window. 
Keying the first gesture triggers the image-captioning process. The user first hears "Recognizing" and then the generated caption is announced whenever it is available (this may take a few seconds). Captions are more accurate when the image is larger and has no padding. Keying the second gesture opens up a virtual browseable window containing the same caption. Users can use navigations keys in this window to browse the caption letter-by-letter, word-by-word, as a whole or even copy the caption. Users must escape this window before starting another image-captioning process. This can be done by pressing the `ESC` key or shifting focus to another element.
Users can also prevent the image-captioning process to be started on non-graphic elements by checking the `filter non-graphic elements` option under __Preferences->Settings->Vision->Image captioning add-on__. This prevents users from accidentally starting the image-captioning process on elements that do not contain images and will produce bad results. Unchecking it allows users to perform detections on elements that may be containing images but fail to report the same.


### Building it yourself
----
Requirements:
* [Python 3](http://www.python.org) for Windows. See website for installers.
* [Scons](http://www.scons.org/) - Can be installed by running `pip install Scons` or using a windows installer from the website.
* [Markdown](https://pypi.org/project/Markdown/) - Can be installed by running `pip install Markdown`.

Once the requirements are satisfied:
1. Clone this repo
2. Open a command line and navigate to the cloned repo
3. Run the command `scons` in the directory containing the **sconstruct** file

You can then install the add-on in NVDA by double-clicking on the **.nvda-addon** file while NVDA is running or goto NVDA->tools->manage add-ons->Install and the selecting the **.nvda-addon** file.


### Developer notes
----
The model used for image captioning in this add-on was converted from a PyTorch model found [here](https://github.com/yunjey/pytorch-tutorial/tree/master/tutorials/03-advanced/image_captioning). The model was converted to the ONNX format and thus relies on [ONNX Runtime 1.3.0](https://github.com/microsoft/onnxruntime) to run. This add-on also relies on [OpenCV 4.3.0](https://opencv.org/) for processing the image for captioning. At its core, the model is in the form of a DLL called `ImageCaptioning-DLL.dll` that can be found at `addon\globalPlugins\imageCaptioning\dlls` along with the ONNX Runtime and OpenCV DLLs. The model itself and the vocabulary file can be found at `addon\globalPlugins\imageCaptioning\data`. 
As is the case with most open-source image captioning models available, the results produced can be wrong at times. The model can also produce different results for the same image at different sizes or with padding. For images in which objects could not be easily identified, the model takes quite some time to produce any results. In some cases, it may be slow the first time it is triggered.
