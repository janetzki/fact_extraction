from pattern_extraction.direction import Direction


class DependencyKey(object):
    def __init__(self, meaning, from_node, to_node, node_addr):
        self.meaning = meaning
        self.direction = DependencyKey.direction(from_node, to_node, node_addr)

    def __repr__(self):
        return 'DependencyKey()'

    def __str__(self):
        return '(' + self.meaning + ', ' + str(self.direction) + ')'

    @staticmethod
    def direction(from_node, to_node, node_addr):
        if from_node == node_addr and to_node == node_addr:
            assert False
            return Direction.loop
        if from_node == node_addr:
            return Direction.outgoing
        elif to_node == node_addr:
            return Direction.incoming
        else:
            assert False

    @staticmethod
    def partner_node(from_node, to_node, node_addr):
        direction = DependencyKey.direction(from_node, to_node, node_addr)
        if direction == Direction.outgoing or direction == Direction.loop:
            return to_node
        elif direction == Direction.incoming:
            return from_node
        else:
            assert False

    def __hash__(self):
        return hash((self.meaning, self.direction))

    def __eq__(self, other):
        return (self.meaning, self.direction) == (other.meaning, other.direction)

    def __ne__(self, other):
        return not (self == other)
