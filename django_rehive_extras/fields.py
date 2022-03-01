from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models.fields import files
from django.core import checks

from pyexiv2 import ImageData


class MoneyField(models.DecimalField):
    """
    Decimal Field for money values.
    """

    def __init__(self, verbose_name=None, name=None, max_digits=30,
            decimal_places=18, **kwargs):
        super().__init__(
            verbose_name,
            name,
            max_digits,
            decimal_places,
            **kwargs
        )


class FieldFile(files.FieldFile):
    def save(self, name, content, save=True):
        content = self.field.generate_content(self.instance, content)
        content.seek(0)
        content.size = len(content.read())
        super().save(name, content, save)


class ImageFieldFile(FieldFile, files.ImageFieldFile):
    pass


class FileField(files.FileField):
    attr_class = FieldFile

    def __init__(self, verbose_name=None, name=None, upload_to='', storage=None, clear_metadata=True, **kwargs):
        self.clear_metadata = self._clear_metadata if clear_metadata is True else clear_metadata
        # To maintain the MRO sequence
        kwargs.update({
            "upload_to": upload_to,
            "storage": storage
        })
        super().__init__(verbose_name, name, **kwargs)

    def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_clear_metadata()
        ]

    def _check_clear_metadata(self):
        if self.clear_metadata and not callable(self.clear_metadata):
            return [
                checks.Error(
                    "%s's 'clear_metadata' argument must be a callable method." % self.__class__.__name__,
                    obj=self,
                    id='fields.E202',
                    hint='Make sure method name is correct.',
                )
            ]
        else:
            return []

    def generate_content(self, instance, content):
        if callable(self.clear_metadata):
            return self.clear_metadata(instance, content)
        return content

    @classmethod
    def _clear_metadata(cls, instance, file):
        try:
            pyexiv_image = ImageData(file.read())
            pyexiv_image.clear_exif()
            file.seek(0)
            file.truncate()
            file.write(pyexiv_image.get_bytes())
            return file
        except RuntimeError:
            return file


class ImageField(FileField, models.ImageField):
    attr_class = ImageFieldFile

    def __init__(
            self,
            verbose_name=None,
            name=None,
            width_field=None,
            height_field=None,
            clear_metadata=True,
            **kwargs):
        # To maintain the MRO sequence
        kwargs.update({
            "width_field": width_field,
            "height_field": height_field
        })
        super().__init__(verbose_name, name, clear_metadata=clear_metadata, **kwargs)
