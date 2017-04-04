from enum import Enum


class Direction(Enum):
    outgoing = 1
    incoming = 2
    loop = 3

    def __repr__(self):
        return 'Direction()'

    def __str__(self):
        if self.value == 1:
            return 'outgoing'
        elif self.value == 2:
            return 'incoming'
        elif self.value == 3:
            return 'loop'
        return '<invalid>'
