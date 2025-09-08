from django.db import models
from django.db.models.base import ModelState


def copy_model_instance(instance, memo=None):
    """
    Copy a Django model instance preserving lazy loading capability.

    This function creates a shallow copy of a Django model instance that:
    1. Copies all concrete (non-relational) model fields
    2. Preserves foreign key IDs to maintain lazy loading capability
    3. Avoids deep recursion and performance issues from related objects

    Args:
        instance: Django model instance to copy
        memo: Optional memo dict for recursion tracking (unused but kept for
              compatibility)

    Returns:
        A new instance of the same model class with copied field values
    """

    if not isinstance(instance, models.Model):
        raise TypeError(
            f"Expected Django model instance, got {type(instance).__name__}"
        )

    # Get the model class and metadata once.
    model_class = instance.__class__
    opts = instance._meta

    # Create a new instance without calling __init__ to avoid triggering
    # any initialization logic that might cause side effects.
    new_instance = model_class.__new__(model_class)

    # Initialize the model state to avoid AttributeError.
    new_instance._state = ModelState()
    new_instance._state.db = instance._state.db
    new_instance._state.adding = False

    # Use direct __dict__ access for better performance when possible.
    # This avoids descriptor overhead for most fields.
    instance_dict = instance.__dict__
    new_instance_dict = new_instance.__dict__

    # Copy concrete fields in a single pass.
    for field in opts.concrete_fields:
        if isinstance(field, (models.ForeignKey, models.OneToOneField)):
            # For foreign keys, copy the ID value to preserve lazy loading.
            id_field_name = field.attname
            if id_field_name in instance_dict:
                new_instance_dict[id_field_name] = instance_dict[id_field_name]
        else:
            # For regular fields, copy the value directly.
            field_name = field.name
            if field_name in instance_dict:
                new_instance_dict[field_name] = instance_dict[field_name]

    return new_instance
