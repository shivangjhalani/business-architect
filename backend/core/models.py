import uuid
from django.db import models
from django.core.validators import MinLengthValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from .constants import ContentTypes

class Capability(models.Model):
    STRATEGIC_IMPORTANCE_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('CURRENT', 'Current'),
        ('PROPOSED', 'Proposed'),
        ('DEPRECATED', 'Deprecated'),
        ('ARCHIVED', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CURRENT')
    strategic_importance = models.CharField(max_length=20, choices=STRATEGIC_IMPORTANCE_CHOICES, default='MEDIUM')
    owner = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'name']
        verbose_name_plural = 'Capabilities'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0
        super().save(*args, **kwargs)


class BusinessGoal(models.Model):
    """Business goal model."""
    
    STATUS_CHOICES = [
        ('PENDING_ANALYSIS', 'Pending Analysis'),
        ('ANALYZED', 'Analyzed'),
        ('RECOMMENDATIONS_APPLIED', 'Recommendations Applied'),
        ('CLOSED', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    pdf_file = models.FileField(upload_to='business_goals/', null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_ANALYSIS')
    submitted_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return self.title


class CapabilityRecommendation(models.Model):
    RECOMMENDATION_TYPE_CHOICES = [
        ('ADD_CAPABILITY', 'Add New Capability'),
        ('MODIFY_CAPABILITY', 'Modify Existing Capability'),
        ('STRENGTHEN_CAPABILITY', 'Strengthen Existing Capability'),
        ('REMOVE_CAPABILITY', 'Remove Capability'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPLIED', 'Applied'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business_goal = models.ForeignKey(BusinessGoal, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=30, choices=RECOMMENDATION_TYPE_CHOICES)
    target_capability = models.ForeignKey(Capability, on_delete=models.CASCADE, null=True, blank=True, related_name='recommendations')
    proposed_name = models.CharField(max_length=200, null=True, blank=True)
    proposed_description = models.TextField(null=True, blank=True)
    proposed_parent = models.ForeignKey(Capability, on_delete=models.CASCADE, null=True, blank=True, related_name='proposed_children')
    additional_details = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    recommended_by_ai_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-recommended_by_ai_at']

    def __str__(self):
        return f"{self.get_recommendation_type_display()} - {self.business_goal.title}"


class VectorEmbedding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField(max_length=50, choices=[(ct, ct) for ct in [ContentTypes.CAPABILITY, ContentTypes.BUSINESS_GOAL, ContentTypes.RECOMMENDATION]])
    object_id = models.CharField(max_length=100)
    vector_index = models.IntegerField()
    text_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.content_type} - {self.object_id}"
