from copy import deepcopy

from django.db import models, transaction
from django.db.models import Case, When, Value, ProtectedError
from django.db.models.expressions import Func, Expression, F
from django.contrib.postgres.fields import ArrayField

from .exceptions import (
    CannotModifyObjectWithArchivedParentError,
    CannotModifyArchivedObjectError,
    CannotDeleteUnarchivedObjectError,
    CannotDeleteObjectError
)


class BaseFunc(Func):
    """
    Base function class for basic database func() expressions.
    """

    def __init__(self, field, *values, **extra):
        if not isinstance(field, Expression):
            field = F(field)
            if values and not isinstance(values[0], Expression):
                values = [Value(v) for v in values]
        super().__init__(field, *values, **extra)


class ArrayAppend(BaseFunc):
    """
    Expression for the postgres array append function.
    """

    function = 'array_append'


class ArrayRemove(BaseFunc):
    """
    Expressionf for the postgres array remove function.
    """

    function = 'array_remove'


class ArchiveNode():
    """
    A single direction cascade node for django models. Expanding this
    node will create a tree that can be used to cascade changes through
    all related tables in one direction.
    """

    def __init__(self, model, parent=None, relation_field=None):
        """
        Initiate the node. Only a model is required. a parent and relation will
        be added when expand is invoked.
        """

        self.model = model
        self.parent = parent
        self.relation_field = relation_field
        self.children = []

    def __str__(self):
        """
        String value for a node instance.
        """

        return str(self.model)

    @staticmethod
    def _get_relation_fields(node, fields=None):
        """
        Build a list relationship fields by ascending up the node tree.

        The resulting list can then be used to construct a Django
        "query param" filter field.
        """

        if not fields:
            fields = []

        if node.parent:
            fields.append(node.relation_field)
            return ArchiveNode._get_relation_fields(node.parent, fields)

        return fields

    def expand(self, models=None):
        """
        Expand relationships from the node.

        Uses introspection to build a single-direction tree of related models.
        """

        # Instantiate a model list. Prevents circular dependences in the tree.
        if models is None:
            models = [self.model]

        # Get the current node's (model's) dependent relationship fields.
        # 1. The field must be a relationship field.
        # 2. The related field's model must be a BaseModel type.
        fields = [f for f in self.model._meta.get_fields()
                 if (f.related_model not in models
                 and (f.one_to_many or f.one_to_one)
                 and (issubclass(f.related_model, ArchiveModel)))]

        for f in fields:
            if hasattr(f, 'field'):
                name = f.field.name
            else:
                name = f.remote_field.name

            # Create a new node with the correct parent and relationship field.
            node = ArchiveNode(
                f.related_model,
                parent=self,
                relation_field=name
            )

            # Add model to models list so circular dependencies don't occur.
            models.append(f.related_model)
            node.expand(models=models)

            # Append the completed child node (and tree) to the parent node.
            self.children.append(node)

    def update(self, instance, archived=None):
        """
        Update the node by cascading down the tree. Requires an instance id.
        """

        if archived is None:
            raise Exception("The archived kwarg should be a boolean.")

        # Get the model name of the instance that triggered the update action.
        # This is used to track what object caused another object to be updated.
        point = instance.__class__.__name__.lower()

        for node in self.children:
            # Build filters for specific model and run an update.
            filters = {}
            fields = self._get_relation_fields(node)
            filters["".join(("__".join(fields), '__id'))] = instance.id

            # If archiving the related objects. Then ensure the new `point`
            # is added to the related objects.
            if archived is True:
                node.model.objects.filter(**filters).update(
                    archived=archived,
                    archive_points=ArrayAppend('archive_points', point)
                )

            # If unarchiving the related objects. Then ensure the current
            # `point` is removed from the related objects. Only set the
            # archived field to false if there are no points.
            if archived is False:
                node.model.objects.filter(**filters).update(
                    archived=Case(
                        When(
                            archive_points__contains=[point],
                            archive_points__len=1,
                            then=archived
                        ),
                        default=F('archived')
                    ),
                    archive_points=ArrayRemove('archive_points', point)
                )

            # Cascade down to next node.
            node.update(instance, archived)


class DateModel(models.Model):
    """
    Abstract model that stores a created and updated date for each object.
    """

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.created)


class StateModel(models.Model):
    """
    Abstract model that stores a temporary model state on instantiation.
    """

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        """
        Set the original state of the model on instantiation.
        """

        super().__init__(*args, **kwargs)
        self.original = deepcopy(self)


class ArchiveModel(StateModel):
    """
    Abstract model that handles archiving of related data.
    """

    archived = models.BooleanField(default=False)
    archive_points = ArrayField(
        models.CharField(max_length=50),
        size=10,
        null=True,
        blank=True
    )

    _must_be_archived_to_delete = True
    _must_be_unarchived_to_modify = True

    class Meta:
        abstract = True

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Save the instance and handle archiving if necessary. Run save in a
        transaction so that failed inserts are rolled back.
        """

        # If the archived status has changed ensure all related objects are
        # also altered accordingly.
        if self.original and self.archived != self.original.archived:
            node = ArchiveNode(self.__class__)

            # Archive the object and all related/dependent objects.
            if self.archived and not self.original.archived:
                node.expand()
                node.update(self, archived=True)

            # Unarchive the object and all related/dependent objects.
            elif not self.archived and self.original.archived:
                # Ensure that a parent is not already archived.
                if self.archive_points:
                    raise CannotModifyObjectWithArchivedParentError()

                node.expand()
                node.update(self, archived=False)

        # If already archived then ensure modifications cannot be performed
        # on the model instance (except for archive changes as above).
        elif self._must_be_unarchived_to_modify and self.archived:
            raise CannotModifyArchivedObjectError()

        return super().save(*args, **kwargs)

    def delete(self):
        """
        Delete the instance and handle model specific delete preferences.
        """

        # Ensure the object is already archived before deleting.
        if self._must_be_archived_to_delete and not self.archived:
            raise CannotDeleteUnarchivedObjectError()

        try:
            super().delete()
        except ProtectedError:
            raise CannotDeleteObjectError()


class IntegratedModel(DateModel, ArchiveModel):
    """
    Generic abstract model that includes date, original state, and
    archive related functionality.
    """

    class Meta:
        abstract = True
