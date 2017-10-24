from django.db.models import Q


class CustomFieldsQ(Q):

    def __init__(self, *args, **kwargs):
        connector = kwargs.pop('_connector', None)
        negated = kwargs.pop('_negated', False)
        self._fields = kwargs.keys()
        for arg in list(args):
            if isinstance(arg, CustomFieldsQ):
                self._fields += arg.get_fields()
        self._fields = list(set(self._fields))
        super().__init__(children=list(args) + list(kwargs.items()), connector=connector, negated=negated)

    def get_fields(self):
        return self._fields

    def _combine(self, other, conn):
        import copy
        if not isinstance(other, CustomFieldsQ) and not isinstance(other, Q):
            raise TypeError(other)

        # If the other Q() is empty, ignore it and just use `self`.
        if not other:
            return copy.deepcopy(self)
        # Or if this Q is empty, ignore it and just use `other`.
        elif not self:
            return copy.deepcopy(other)

        obj = type(self)()
        obj.connector = conn
        obj.add(self, conn)
        obj.add(other, conn)

        other_fields = other.get_fields() if isinstance(other, CustomFieldsQ) else []
        obj._fields = list(set(self.get_fields() + other_fields))

        return obj
