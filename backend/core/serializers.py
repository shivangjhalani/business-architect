from rest_framework import serializers
from .models import Capability, BusinessGoal, CapabilityRecommendation

class CapabilityListSerializer(serializers.ModelSerializer):
    full_path = serializers.SerializerMethodField()
    
    class Meta:
        model = Capability
        fields = [
            'id', 'name', 'description', 'level', 'status', 
            'strategic_importance', 'parent', 'full_path',
            'created_at', 'updated_at'
        ]
    
    def get_full_path(self, obj):
        path = []
        current = obj
        while current:
            path.append(current.name)
            current = current.parent
        return ' > '.join(reversed(path))

class CapabilitySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    
    class Meta:
        model = Capability
        fields = [
            'id', 'name', 'description', 'level', 'status',
            'strategic_importance', 'parent', 'children', 'full_path',
            'owner', 'notes', 'created_at', 'updated_at'
        ]
    
    def get_children(self, obj):
        children = obj.children.all()
        return CapabilityListSerializer(children, many=True).data
    
    def get_full_path(self, obj):
        path = []
        current = obj
        while current:
            path.append(current.name)
            current = current.parent
        return ' > '.join(reversed(path))

    def validate(self, data):
        if self.instance and 'parent' in data:
            new_parent = data['parent']
            if new_parent:
                current = new_parent
                while current:
                    if current == self.instance:
                        raise serializers.ValidationError("Cannot set parent to create circular reference")
                    current = current.parent
        return data

class BusinessGoalSerializer(serializers.ModelSerializer):
    pdf_filename = serializers.SerializerMethodField()
    is_analyzed = serializers.SerializerMethodField()
    recommendations_count = serializers.SerializerMethodField()
    pending_recommendations_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BusinessGoal
        fields = [
            'id', 'title', 'description', 'status', 'pdf_file', 'pdf_filename',
            'is_analyzed', 'recommendations_count', 'pending_recommendations_count',
            'submitted_at', 'updated_at'
        ]
    
    def get_pdf_filename(self, obj):
        if obj.pdf_file:
            return obj.pdf_file.name.split('/')[-1]
        return None
    
    def get_is_analyzed(self, obj):
        return obj.status == 'ANALYZED'
    
    def get_recommendations_count(self, obj):
        return obj.recommendations.count()
    
    def get_pending_recommendations_count(self, obj):
        return obj.recommendations.filter(status='PENDING').count()

class BusinessGoalDetailSerializer(BusinessGoalSerializer):
    recommendations = serializers.SerializerMethodField()
    
    class Meta(BusinessGoalSerializer.Meta):
        fields = BusinessGoalSerializer.Meta.fields + ['recommendations']
    
    def get_recommendations(self, obj):
        recommendations = obj.recommendations.all()
        return CapabilityRecommendationSerializer(recommendations, many=True).data

class CapabilityRecommendationSerializer(serializers.ModelSerializer):
    proposed_parent_details = serializers.SerializerMethodField()
    target_capability_details = serializers.SerializerMethodField()
    is_actionable = serializers.SerializerMethodField()
    confidence_score = serializers.SerializerMethodField()
    
    class Meta:
        model = CapabilityRecommendation
        fields = [
            'id', 'business_goal', 'recommendation_type', 'status',
            'target_capability', 'target_capability_details',
            'proposed_name', 'proposed_description', 'proposed_parent',
            'proposed_parent_details', 'additional_details',
            'is_actionable', 'confidence_score',
            'recommended_by_ai_at', 'applied_at'
        ]
    
    def get_proposed_parent_details(self, obj):
        if obj.proposed_parent:
            return CapabilityListSerializer(obj.proposed_parent).data
        return None
    
    def get_target_capability_details(self, obj):
        if obj.target_capability:
            return CapabilityListSerializer(obj.target_capability).data
        return None
    
    def get_is_actionable(self, obj):
        return obj.status == 'PENDING'
    
    def get_confidence_score(self, obj):
        return 0.8

class LLMQuerySerializer(serializers.Serializer):
    query = serializers.CharField(max_length=1000)
    context = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    
    def validate_query(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Query must be at least 3 characters long")
        return value.strip()

class LLMResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()
    query = serializers.CharField()
    context_used = serializers.CharField()
    vector_context = serializers.DictField() 