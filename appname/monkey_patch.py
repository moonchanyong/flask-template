def patch_all():
    from flask_restful import reqparse
    from werkzeug import MultiDict
    import six

    def source(self, request):
        if isinstance(self.location, six.string_types):
            value = getattr(request, self.location, MultiDict())
            if callable(value):
                value = value()
            if value is not None:
                return value
        else:
            values = MultiDict()
            for l in self.location:
                value = getattr(request, l, None)
                if callable(value):
                    value = value()
                # replace existing key lists
                if isinstance(value, dict):
                    for k, v in value.items():
                        values[k] = v

                elif value is not None:
                    values.update(value)
            return values
        return MultiDict()
    reqparse.Argument.source = source

