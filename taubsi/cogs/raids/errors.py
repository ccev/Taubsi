from taubsi.utils.errors import TaubsiError


class InvalidTime(TaubsiError):
    """invalid_time"""


class WrongChannel(TaubsiError):
    """wrong_channel"""


class WrongGymName(TaubsiError):
    """wrong_gym_name"""
