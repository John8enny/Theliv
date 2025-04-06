from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


class Evidence(models.Model):
    id = models.CharField(max_length=100, unique=True, primary_key=True)
    cid = models.CharField(max_length=256)  # CID from IPFS
    file_hash = models.CharField(max_length=256)
    evd_name = models.CharField(max_length=255)  # Evidence Name
    case_num = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    file_type = models.CharField(max_length=50)
    metadata = models.JSONField(blank=True, null=True)
    custom_data = models.JSONField(blank=True, null=True)  # Optional field
    added_by_django = models.CharField(max_length=100, null=False)
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.evd_name} - {self.case_num}"

    def __str__(self):
        return f"{self.evd_title} - {self.case_num}"