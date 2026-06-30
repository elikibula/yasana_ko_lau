from django.conf import settings
from django.db import models


class YavusaReport(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    yavusa_name = models.CharField(max_length=100)
    member_count = models.PositiveIntegerField(default=0)
    content = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.yavusa_name} Yavusa Report"
