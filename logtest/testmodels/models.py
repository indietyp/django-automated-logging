import uuid
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Base(BaseModel):
    pass


class M2MTest(BaseModel):
    test = models.ManyToManyField(Base, null=True)


class ForeignTest(BaseModel):
    test = models.ForeignKey(Base, on_delete=models.CASCADE, null=True)


class OneToOneTest(BaseModel):
    test = models.OneToOneField(Base, null=True, on_delete=models.CASCADE)


class OrdinaryTest(BaseModel):
    test = models.CharField(max_length=255, null=True)
