from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('CLINICIAN', 'Clinician'),
        ('ANALYST', 'Data Analyst'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CLINICIAN')
    supabase_uid = models.UUIDField(unique=True, null=True, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class AuditLog(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=255)
    affected_table = models.CharField(max_length=255)
    affected_record_id = models.UUIDField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.action_type} on {self.affected_table} by {self.user_id}"
