from datetime import timedelta, datetime

from django.utils.timezone import make_aware
from django_filters import rest_framework as filters


class TimeStampFilter(filters.Filter):
    """
    Custom filter for DateTime model fields.

    Allows for filtering on datetime fields using a date formatted as an
    integer. The default integer date expected is a millisecond timestamp.
    """

    # Default to a millisecond multiplier.
    multiplier = 1000

    def filter(self, qs, value):
        if not value:
            return qs

        # Convert the value to a datetime and ensure invalid dates return an
        # empty list.
        try:
            dt = int(value) / int(self.multiplier)
            dt = make_aware(datetime.fromtimestamp(dt))
        except ValueError:
            return qs.none()

        # Build lookups for the filter.
        lookups = {}

        # If a range-based lookup is used then we should perform the query
        # as per normal as milliseconds will be handled via the range.
        if self.lookup_expr in ("lt", "lte", "gt", "gte",):
            lookup_key = "{}__{}".format(self.field_name, self.lookup_expr)
            lookups[lookup_key] = dt

        # For exact lookups we should do some internal padding and force a range
        # lookup in order to get millisecond precision.
        elif self.lookup_expr in ("exact",):
            gte_key = "{}__{}".format(self.field_name, "gte")
            lt_key = "{}__{}".format(self.field_name, "lt")
            lookups.update({
                gte_key: dt,
                lt_key: dt + timedelta(milliseconds=1),
            })

        qs = self.get_method(qs)(**lookups)
        return qs
