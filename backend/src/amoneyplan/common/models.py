from cuid2 import Cuid
from django.db import models
from profanity_check import predict

"""
1.84BN ids till 50% chance of collision
https://www.wolframalpha.com/input?i=sqrt(36%5E(12-1)+*+26)
"""
CUID_12_GENERATOR: Cuid = Cuid(length=12)

# New 16-character generator
"""2.3 trillion ids till 50% chance of collision
https://www.wolframalpha.com/input?i=sqrt(36%5E(16-1)+*+26)
"""
CUID_16_GENERATOR: Cuid = Cuid(length=16)

"""
4 quintillion 26 quadrillion 800 trillion ids till 50% chance of collision
https://www.wolframalpha.com/input?i=sqrt(36%5E(24-1)+*+26)
"""
CUID_24_GENERATOR: Cuid = Cuid(length=24)


def generate_safe_cuid(generator: Cuid) -> str:
    """
    Generates a CUID and ensures it doesn't contain offensive content.
    Retries until a safe CUID is produced.
    """
    while True:
        cuid = generator.generate()
        # predict returns [0] for non-offensive text
        if predict([cuid])[0] == 0:
            return cuid


def generate_safe_cuid12():
    """Generate a safe 12-character CUID."""
    return generate_safe_cuid(CUID_12_GENERATOR)


def generate_safe_cuid16():
    """Generate a safe 16-character CUID."""
    return generate_safe_cuid(CUID_16_GENERATOR)


def generate_safe_cuid24():
    """Generate a safe 24-character CUID."""
    return generate_safe_cuid(CUID_24_GENERATOR)


class SafeCuid16Field(models.CharField):
    """
    CharField implementation of SafeCuid16Field for use with explicit model fields.
    """

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 16
        kwargs["default"] = generate_safe_cuid16
        super().__init__(*args, **kwargs)


class SafeCuidField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 12
        kwargs["default"] = generate_safe_cuid12
        super().__init__(*args, **kwargs)


class SafeBigCuidField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 24
        kwargs["default"] = generate_safe_cuid24
        super().__init__(*args, **kwargs)


class ActiveManager(models.Manager):
    """
    Manager that returns only active (not deleted) records.
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class BaseModel(models.Model):
    id = SafeCuid16Field(editable=False, primary_key=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Add default manager
    objects = models.Manager()
    # Add active manager (filters out deleted records)
    active = ActiveManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]
