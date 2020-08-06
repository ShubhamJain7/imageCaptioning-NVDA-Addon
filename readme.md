# Image Captioning Add-on

* Author: Shubham Dilip Jain
* Download: https://github.com/ShubhamJain7/imageCaptioning-NVDA-Addon

This add-on allows users to perform image captioning on image elements present on their screen and get a caption that describes the image in English. The result is announced to the user and also presented in a virtual window that allows users to access the result character-by-character, word-by-word, as a whole and even copy the result.

### Usage
----
Detection can triggered by pressing `Alt+NVDA+C` or `Alt+NVDA+C+C+...`
The former only performs detection if the navigator object currently in focus has the role `ROLE_GRAPHIC`. This prevents non-visual users from waiting for bad results after mistakenly starting a captioning process on non-image elements. Low-vision users or otherwise can press `Alt+NVDA+C+C+..` to perform captioning on any element without filtering out non `ROLE_GRAPHIC` roles.
The result is announced as soon as it is available. This announcement is then followed by `RESULT_DOCUMENT` which indicates that focus has been shifted to a "virtual result window". Users can then use arrow-key navigation to access the result character-by-character, word-by-word or as a whole. Pressing `ESC` or changing focus to another element on the screen escapes the "virtual result window".
The result can be re-accessed by pressing `Alt+NVDA+R`.

### Building it yourself
----
Requirements:
* a Python distribution (2.7 or greater is recommended). Check the [Python Website](http://www.python.org) for Windows Installers.
* Scons - [Website](http://www.scons.org/) - version 2.1.0 or greater. Install it using **easy_install** or grab a windows installer from the website.
* GNU Gettext tools, if you want to have localization support for your add-on - Recommended. Any Linux distro or Cygwin have those installed. You can find windows builds [here](http://gnuwin32.sourceforge.net/downlinks/gettext.php).
* Markdown-2.0.1 or greater, if you want to convert documentation files to HTML documents. You can [Download Markdown](https://pypi.org/project/Markdown/) or get it using `easy_install markdown`.

Once the requirements are satisfied:
1. Clone this repo
2. Open a command line and navigate to the cloned repo
3. Run the command `scons` in the directory containing the **sconstruct** file

You can then install the add-on in NVDA by double-clicking on the **.nvda-addon** file while NVDA is running or goto NVDA->tools->manage add-ons->Install and the selecting the **.nvda-addon** file.


### Developer notes
----
The model used for image captioning in this add-on was converted from a PyTorch model found [here](https://github.com/yunjey/pytorch-tutorial/tree/master/tutorials/03-advanced/image_captioning). The model was converted to the ONNX format and thus relies on [ONNX Runtime 1.3.0](https://github.com/microsoft/onnxruntime) to run. This add-on also relies on [OpenCV 4.3.0](https://opencv.org/) for processing the image for captioning. At its core, the model is in the form of a DLL called `ImageCaptioning-DLL.dll` that can be found at `addon\globalPlugins\imageCaptioning\dlls` along with the ONNX Runtime and OpenCV DLLs. The model itself and the vocabulary file can be found at `addon\globalPlugins\imageCaptioning\data`. 
As is the case with most open-source image captioning models available, the results produced can be wrong at times. The model can also produce different results for the same image at different sizes. For images in which objects could not be easily identified, the model takes quite some time to produce any results. In some cases, it may be slow the first time it is triggered.