class KeyWord:
    command = None

    @property
    def inverse(self):
        if self.command.startswith('$n'):
            return '$' + self.command[2:]
        return '$n' + self.command[1:]


class TopLevelKeyWord(KeyWord):
    def __init__(self, *args):
        self.expressions = args


class Eq(KeyWord):
    command = '$eq'


class Neq(KeyWord):
    command = '$neq'


class Or(TopLevelKeyWord):
    command = '$or'


class Nor(TopLevelKeyWord):
    command = '$nor'


class In(KeyWord):
    command = '$in'


class Nin(KeyWord):
    command = '$nin'


class And(TopLevelKeyWord):
    command = '$and'


class Nand(TopLevelKeyWord):
    command = '$nand'


class Gte(KeyWord):
    command = '$gte'

    @property
    def inverse(self):
        return '$lt'


class Lte(KeyWord):
    command = '$lte'

    @property
    def inverse(self):
        return '$gt'


class Lt(KeyWord):
    command = '$lt'

    @property
    def inverse(self):
        return '$gte'


class Gt(KeyWord):
    command = '$gt'

    @property
    def inverse(self):
        return '$lte'
