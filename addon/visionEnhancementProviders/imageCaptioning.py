from autoSettingsUtils.autoSettings import SupportedSettingType
from vision import providerBase
import driverHandler


class ImageCaptioningSettings(providerBase.VisionEnhancementProviderSettings):
	filterNonGraphicElements = True

	@classmethod
	def getId(cls) -> str:
		return "ImageCaptioning"

	@classmethod
	def getDisplayName(cls) -> str:
		return _("Image captioning add-on")

	def _get_supportedSettings(self) -> SupportedSettingType:
		settings = [
			driverHandler.BooleanDriverSetting(
				"filterNonGraphicElements",
				"filter non-graphic elements",
				defaultVal=True
			)
		]
		return settings


class ImageCaptioning(providerBase.VisionEnhancementProvider):
	_settings = ImageCaptioningSettings()

	@classmethod  # override
	def getSettings(cls) -> ImageCaptioningSettings:
		return cls._settings

	@classmethod  # override
	def getSettingsPanelClass(cls):
		return None

	@classmethod  # override
	def canStart(cls) -> bool:
		return True

	def registerEventExtensionPoints(self, extensionPoints):
		pass

	def terminate(self):
		super().terminate()


VisionEnhancementProvider = ImageCaptioning
