from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=40, blank=True)
    city = models.CharField(max_length=80, blank=True)
    address = models.CharField(max_length=300, blank=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.email or self.username


class Address(models.Model):
    user = models.ForeignKey(User, related_name="addresses", on_delete=models.CASCADE)
    label = models.CharField(max_length=60, default="المنزل")
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40)
    country_code = models.CharField(max_length=2, default="SA")
    city = models.CharField(max_length=80)
    region = models.CharField(max_length=80, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    line1 = models.CharField(max_length=220)
    line2 = models.CharField(max_length=220, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-updated_at"]
        indexes = [models.Index(fields=["user", "-is_default"])]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )

    def __str__(self):
        return f"{self.label} - {self.full_name}"
