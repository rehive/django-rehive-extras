from django.db.models import Func


class AtTimeZone(Func):
    """
    This database function class convert the ISO datetime to any specific
    timezone. Basically this class use the PostgreSql `TIMESTMPTZ (<timestamp>)
    AT TIME ZONE <tz_info>`. This can take `tz_info` and `date_time` as a
    arguments. These arguments value can be static value or model field. The
    default value is respectively `UTC` and `NOW()`. Another argument is
    `output_field` this argument value should be `models.DatetimeField()` or
    `models.DateField()`.
    """

    def __init__(self, tz_info=None, date_time=None, output_field=None):
        self.datetime = self._parse_expressions(date_time)[0] \
            if date_time else None
        self.tz_info = self._parse_expressions(tz_info)[0] if tz_info else None

        super().__init__(self.tz_info, output_field=output_field)

    def as_postgresql(self, compiler, connection, **extra_context):
        datetime_template = "TIMESTAMPTZ %(datetime)s" if self.datetime \
            else "TIMESTAMPTZ (NOW())"
        timezone_template = "AT TIME ZONE %(tz_info)s" if self.tz_info \
            else "AT TIME ZONE 'UTC'"
        template = "%s %s" % (datetime_template, timezone_template)
        extra = {}
        if self.datetime:
            datetime_sql, datetime_params = compiler.compile(
                self.datetime.resolve_expression(compiler.query)
            )
            extra['datetime'] = datetime_sql or datetime_sql[0]
        if self.tz_info:
            tz_info_sql, tz_info_params = compiler.compile(
                self.tz_info.resolve_expression(compiler.query)
            )
            extra['tz_info'] = tz_info_sql or tz_info_params[0]

        extra.update(**extra_context)
        return self.as_sql(
            compiler, connection, template=template,
            **extra
        )
