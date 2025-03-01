import platform
from enum import Enum


class Platform(Enum):
    WINDOWS = "Windows"
    LINUX = "Linux"
    MACOS = "Darwin"


_platform = platform.system()

if _platform not in [platform.value for platform in Platform]:
    raise ValueError(
        f"Unsupported platform: {_platform}. Supported platforms are: {', '.join([platform.name for platform in Platform])}"
    )

CURRENT_PLATFORM = Platform(_platform)
