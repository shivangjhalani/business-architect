from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Capability, BusinessGoal, CapabilityRecommendation

class CapabilityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing capabilities without nested children."""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children_count = serializers.SerializerMethodField()
    full_path = serializers.ReadOnlyField()
    
    class Meta:
        model = Capability
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name', 
            'level', 'status', 'strategic_importance', 'owner', 
            'notes', 'created_at', 'updated_at', 'children_count', 'full_path'
        ]
    
    def get_children_count(self, obj):
        return obj.children.count()

class CapabilitySerializer(serializers.ModelSerializer):
    """Full serializer with nested children for hierarchical display."""
    children = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    full_path = serializers.ReadOnlyField()
    ancestor_count = serializers.SerializerMethodField()
    descendant_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Capability
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name', 
            'level', 'status', 'strategic_importance', 'owner', 
            'notes', 'created_at', 'updated_at', 'children', 
            'full_path', 'ancestor_count', 'descendant_count'
        ]
    
    def get_children(self, obj):
        children = obj.children.filter(status__in=['CURRENT', 'PROPOSED'])
        return CapabilityListSerializer(children, many=True).data
    
    def get_ancestor_count(self, obj):
        return len(obj.get_ancestors())
    
    def validate(self, data):
        """Custom validation for capability creation/update."""
        if self.instance:
            # For updates, check if parent change would create circular reference
            parent = data.get('parent', self.instance.parent)
            if parent and parent.id == self.instance.id:
                raise ValidationError("A capability cannot be its own parent.")
        
        return data

class BusinessGoalSerializer(serializers.ModelSerializer):
    recommendations_count = serializers.ReadOnlyField()
    pending_recommendations_count = serializers.ReadOnlyField()
    is_analyzed = serializers.ReadOnlyField()
    pdf_filename = serializers.SerializerMethodField()
    
    class Meta:
        model = BusinessGoal
        fields = [
            'id', 'title', 'description', 'pdf_file', 'status', 
            'submitted_at', 'recommendations_count', 
            'pending_recommendations_count', 'is_analyzed', 'pdf_filename'
        ]
    
    def get_pdf_filename(self, obj):
        return obj.get_pdf_filename()

class BusinessGoalDetailSerializer(BusinessGoalSerializer):
    """Extended serializer with recommendations for detail view."""
    recommendations = serializers.SerializerMethodField()
    
    class Meta(BusinessGoalSerializer.Meta):
        fields = BusinessGoalSerializer.Meta.fields + ['recommendations']
    
    def get_recommendations(self, obj):
        recommendations = obj.recommendations.all().order_by('-recommended_by_ai_at')
        return CapabilityRecommendationSerializer(recommendations, many=True).data

class CapabilityRecommendationSerializer(serializers.ModelSerializer):
    target_capability_details = CapabilityListSerializer(source='target_capability', read_only=True)
    proposed_parent_details = CapabilityListSerializer(source='proposed_parent', read_only=True)
    business_goal_title = serializers.CharField(source='business_goal.title', read_only=True)
    is_actionable = serializers.ReadOnlyField()
    processing_duration = serializers.ReadOnlyField()
    
    class Meta:
        model = CapabilityRecommendation
        fields = [
            'id', 'business_goal', 'business_goal_title', 'recommendation_type',
            'target_capability', 'target_capability_details', 
            'proposed_name', 'proposed_description', 'proposed_parent',
            'proposed_parent_details', 'additional_details', 'status',
            'recommended_by_ai_at', 'applied_at', 'is_actionable', 'processing_duration'
        ]
        read_only_fields = ['business_goal', 'recommended_by_ai_at', 'applied_at']

class LLMQuerySerializer(serializers.Serializer):
    """Serializer for LLM query requests."""
    query = serializers.CharField(
        max_length=2000,
        help_text="Question or query for the AI assistant"
    )
    context = serializers.CharField(
        max_length=10000,
        required=False,
        allow_blank=True,
        help_text="Optional context to help the AI understand the query better"
    )
    
    def validate_query(self, value):
        if len(value.strip()) < 3:
            raise ValidationError("Query must be at least 3 characters long.")
        return value.strip()

class LLMResponseSerializer(serializers.Serializer):
    """Serializer for LLM response."""
    answer = serializers.CharField()
    query = serializers.CharField()
    context_used = serializers.CharField(required=False) 