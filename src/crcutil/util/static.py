from typing import Self


class Static:
    def __new__(cls) -> Self:
        description = "Static classes cannot be instantiated"
        raise TypeError(description)
