from django.utils.functional import cached_property


class CachedPropertyHandlerMixin:
    """
    This Class purge or resetting all property attribute those are wrapped
    with `@cached_property`.
    """

    def refresh_from_db(self, *args, **kwargs):
        self.purge_cached_properties()
        return super().refresh_from_db(*args, **kwargs)

    def purge_cached_properties(self):
        for key, value in self.__class__.__dict__.items():
            if isinstance(value, cached_property):
                self.__dict__.pop(key, None)
