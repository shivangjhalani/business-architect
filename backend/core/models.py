from django.db import models
from django.core.validators import MinLengthValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import os

class Capability(models.Model):
    """
    Represents a business capability with hierarchical structure and lifecycle management.
    """
    
    # Status choices
    STATUS_CHOICES = [
        ('CURRENT', 'Current'),
        ('PROPOSED', 'Proposed'),
        ('DEPRECATED', 'Deprecated'),
        ('ARCHIVED', 'Archived'),
    ]
    
    # Strategic importance choices
    IMPORTANCE_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(2, "Capability name must be at least 2 characters long.")],
        help_text="Unique name for the business capability"
    )
    description = models.TextField(
        validators=[MinLengthValidator(10, "Description must be at least 10 characters long.")],
        help_text="Detailed explanation of what this capability encompasses"
    )
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='children',
        help_text="Parent capability in the hierarchy"
    )
    level = models.PositiveIntegerField(
        default=1,
        help_text="Hierarchy level (1 = top level, 2 = sub-capability, etc.)"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='CURRENT',
        help_text="Current status of the capability"
    )
    strategic_importance = models.CharField(
        max_length=20, 
        choices=IMPORTANCE_CHOICES, 
        default='MEDIUM',
        help_text="Strategic importance to the organization"
    )
    owner = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="Business unit or individual responsible for this capability"
    )
    notes = models.TextField(
        null=True, 
        blank=True,
        help_text="Additional internal notes and comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Business Capability"
        verbose_name_plural = "Business Capabilities"
        ordering = ['level', 'name']
        constraints = [
            models.CheckConstraint(
                check=models.Q(level__gte=1) & models.Q(level__lte=10),
                name='valid_capability_level'
            ),
            models.UniqueConstraint(
                fields=['name', 'parent'],
                name='unique_capability_name_per_parent'
            ),
        ]
        indexes = [
            models.Index(fields=['status', 'strategic_importance']),
            models.Index(fields=['parent', 'level']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Custom validation for the model."""
        super().clean()
        
        # Validate hierarchy constraints
        if self.parent:
            # Check for circular references
            if self._check_circular_reference():
                raise ValidationError("Circular reference detected in capability hierarchy.")
            
            # Validate level consistency
            if self.level <= self.parent.level:
                raise ValidationError("Child capability level must be greater than parent level.")
        else:
            # Root capabilities should be level 1
            if self.level != 1:
                self.level = 1

    def save(self, *args, **kwargs):
        """Override save to auto-calculate level and validate."""
        # Auto-calculate level based on parent
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        
        # Run full validation
        self.full_clean()
        super().save(*args, **kwargs)

    def _check_circular_reference(self):
        """Check for circular references in the hierarchy."""
        visited = set()
        current = self.parent
        
        while current:
            if current.id in visited or current.id == self.id:
                return True
            visited.add(current.id)
            current = current.parent
        
        return False

    @property
    def full_path(self):
        """Return the full hierarchical path of the capability."""
        path = [self.name]
        current = self.parent
        
        while current:
            path.insert(0, current.name)
            current = current.parent
        
        return " > ".join(path)

    @property
    def is_root(self):
        """Check if this is a root-level capability."""
        return self.parent is None

    @property
    def descendant_count(self):
        """Count all descendants (children, grandchildren, etc.)."""
        count = 0
        for child in self.children.all():
            count += 1 + child.descendant_count
        return count

    def get_ancestors(self):
        """Get all ancestor capabilities."""
        ancestors = []
        current = self.parent
        
        while current:
            ancestors.append(current)
            current = current.parent
        
        return ancestors

    def get_descendants(self):
        """Get all descendant capabilities."""
        descendants = []
        
        def collect_descendants(capability):
            for child in capability.children.all():
                descendants.append(child)
                collect_descendants(child)
        
        collect_descendants(self)
        return descendants


class BusinessGoal(models.Model):
    """
    Represents a strategic business objective that may impact capability architecture.
    """
    
    # Status choices
    STATUS_CHOICES = [
        ('PENDING_ANALYSIS', 'Pending Analysis'),
        ('ANALYZED', 'Analyzed'),
        ('RECOMMENDATIONS_APPLIED', 'Recommendations Applied'),
        ('CLOSED', 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(5, "Goal title must be at least 5 characters long.")],
        help_text="Brief, descriptive title for the business goal"
    )
    description = models.TextField(
        validators=[MinLengthValidator(20, "Description must be at least 20 characters long.")],
        help_text="Detailed explanation of the business goal and its objectives"
    )
    pdf_file = models.FileField(
        upload_to='business_goals/pdfs/', 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Optional PDF document with additional goal details"
    )
    status = models.CharField(
        max_length=30, 
        choices=STATUS_CHOICES, 
        default='PENDING_ANALYSIS',
        help_text="Current status of the goal analysis process"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Business Goal"
        verbose_name_plural = "Business Goals"
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status', 'submitted_at']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        """Custom validation for the model."""
        super().clean()
        
        # Validate PDF file size (max 10MB)
        if self.pdf_file:
            if self.pdf_file.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError("PDF file size cannot exceed 10MB.")

    @property
    def analysis_duration(self):
        """Calculate how long ago the goal was submitted."""
        return timezone.now() - self.submitted_at

    @property
    def is_analyzed(self):
        """Check if the goal has been analyzed."""
        return self.status in ['ANALYZED', 'RECOMMENDATIONS_APPLIED', 'CLOSED']

    @property
    def recommendations_count(self):
        """Count of associated recommendations."""
        return self.recommendations.count()

    @property
    def pending_recommendations_count(self):
        """Count of pending recommendations."""
        return self.recommendations.filter(status='PENDING').count()

    def get_pdf_filename(self):
        """Get the original filename of the uploaded PDF."""
        if self.pdf_file:
            return os.path.basename(self.pdf_file.name)
        return None


class CapabilityRecommendation(models.Model):
    """
    Represents an AI-generated recommendation for capability map changes.
    """
    
    # Recommendation type choices
    TYPE_CHOICES = [
        ('ADD_CAPABILITY', 'Add Capability'),
        ('MODIFY_CAPABILITY', 'Modify Capability'),
        ('DELETE_CAPABILITY', 'Delete Capability'),
        ('STRENGTHEN_CAPABILITY', 'Strengthen Capability'),
        ('MERGE_CAPABILITIES', 'Merge Capabilities'),
        ('SPLIT_CAPABILITY', 'Split Capability'),
    ]
    
    # Status choices
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPLIED', 'Applied'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business_goal = models.ForeignKey(
        BusinessGoal, 
        on_delete=models.CASCADE, 
        related_name='recommendations',
        help_text="The business goal that triggered this recommendation"
    )
    recommendation_type = models.CharField(
        max_length=30, 
        choices=TYPE_CHOICES,
        help_text="Type of recommended action"
    )
    target_capability = models.ForeignKey(
        Capability, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='recommendations',
        help_text="Existing capability being targeted (for modify/delete/strengthen)"
    )
    proposed_name = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="Proposed name for new or modified capability"
    )
    proposed_description = models.TextField(
        null=True, 
        blank=True,
        help_text="Proposed description for new or modified capability"
    )
    proposed_parent = models.ForeignKey(
        Capability, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='proposed_parent_recommendations',
        help_text="Proposed parent capability for hierarchy changes"
    )
    additional_details = models.TextField(
        null=True, 
        blank=True,
        help_text="AI's detailed explanation and rationale for the recommendation"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        help_text="Current status of the recommendation"
    )
    recommended_by_ai_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when the recommendation was applied"
    )

    class Meta:
        verbose_name = "Capability Recommendation"
        verbose_name_plural = "Capability Recommendations"
        ordering = ['-recommended_by_ai_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(status='PENDING') | models.Q(applied_at__isnull=False),
                name='applied_recommendations_have_timestamp'
            ),
        ]
        indexes = [
            models.Index(fields=['business_goal', 'status']),
            models.Index(fields=['recommendation_type', 'status']),
            models.Index(fields=['target_capability']),
        ]

    def __str__(self):
        return f"{self.get_recommendation_type_display()} for {self.business_goal.title}"

    def clean(self):
        """Custom validation for the model."""
        super().clean()
        
        # Validate that target_capability is provided for relevant types
        target_required_types = ['MODIFY_CAPABILITY', 'DELETE_CAPABILITY', 'STRENGTHEN_CAPABILITY']
        if self.recommendation_type in target_required_types and not self.target_capability:
            raise ValidationError(
                f"Target capability is required for {self.get_recommendation_type_display()} recommendations."
            )
        
        # Validate that proposed fields are provided for ADD_CAPABILITY
        if self.recommendation_type == 'ADD_CAPABILITY':
            if not self.proposed_name:
                raise ValidationError("Proposed name is required for Add Capability recommendations.")
            if not self.proposed_description:
                raise ValidationError("Proposed description is required for Add Capability recommendations.")
        
        # Validate applied_at timestamp consistency
        if self.status == 'APPLIED' and not self.applied_at:
            self.applied_at = timezone.now()
        elif self.status != 'APPLIED' and self.applied_at:
            raise ValidationError("Applied timestamp should only be set for applied recommendations.")

    def save(self, *args, **kwargs):
        """Override save to set applied_at timestamp."""
        # Set applied_at timestamp when status changes to APPLIED
        if self.status == 'APPLIED' and not self.applied_at:
            self.applied_at = timezone.now()
        
        # Run full validation
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_actionable(self):
        """Check if the recommendation can be acted upon."""
        return self.status == 'PENDING'

    @property
    def processing_duration(self):
        """Calculate how long the recommendation has been pending."""
        if self.status == 'PENDING':
            return timezone.now() - self.recommended_by_ai_at
        elif self.applied_at:
            return self.applied_at - self.recommended_by_ai_at
        return None

    def get_impact_summary(self):
        """Generate a human-readable impact summary."""
        if self.recommendation_type == 'ADD_CAPABILITY':
            return f"Add new capability: {self.proposed_name}"
        elif self.recommendation_type == 'MODIFY_CAPABILITY' and self.target_capability:
            return f"Modify capability: {self.target_capability.name}"
        elif self.recommendation_type == 'DELETE_CAPABILITY' and self.target_capability:
            return f"Delete capability: {self.target_capability.name}"
        elif self.recommendation_type == 'STRENGTHEN_CAPABILITY' and self.target_capability:
            return f"Strengthen capability: {self.target_capability.name}"
        else:
            return f"{self.get_recommendation_type_display()}"
