from taubsi.utils.errors import TaubsiError


class UserNotLinked(TaubsiError):
    "user_not_linked"
    pass


class PlayerNotLinked(TaubsiError):
    "player_not_inked"
    pass


class SelfNotLinked(TaubsiError):
    "self_not_linked"
    pass
