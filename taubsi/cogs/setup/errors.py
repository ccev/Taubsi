from taubsi.utils.errors import TaubsiError

class LevelTooHigh(TaubsiError):
    "level_too_high"
    pass

class LevelTooSmall(TaubsiError):
    "level_too_small"
    pass

class NoTeam(TaubsiError):
    "no_team"
    pass

class NoCodeSet(TaubsiError):
    "no_code_set"
    pass

class WrongCodeFormat(TaubsiError):
    "wrong_code_format"
    pass