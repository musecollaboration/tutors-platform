class DomenError(Exception):
    pass


class InvalidFullNameError(DomenError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidEmailError(DomenError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
