from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
import google.generativeai as genai
import os
import json
import PyPDF2
import io

from .models import Capability, BusinessGoal, CapabilityRecommendation
from .serializers import (
    CapabilitySerializer, CapabilityListSerializer,
    BusinessGoalSerializer, BusinessGoalDetailSerializer,
    CapabilityRecommendationSerializer,
    LLMQuerySerializer, LLMResponseSerializer
)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

class CapabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing business capabilities with hierarchical support.
    
    Provides CRUD operations and filtering capabilities.
    """
    queryset = Capability.objects.all()
    serializer_class = CapabilitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'status', 'parent', 'strategic_importance']
    search_fields = ['name', 'description', 'owner']
    ordering_fields = ['name', 'level', 'created_at', 'strategic_importance']
    ordering = ['level', 'name']

    def get_serializer_class(self):
        """Use different serializers for list vs detail views."""
        if self.action == 'list':
            return CapabilityListSerializer
        return CapabilitySerializer

    def get_queryset(self):
        """Apply custom filtering based on query parameters."""
        queryset = Capability.objects.all()
        
        # Filter by root capabilities only
        if self.request.query_params.get('root_only', '').lower() == 'true':
            queryset = queryset.filter(parent__isnull=True)
        
        # Filter by parent capability
        parent_id = self.request.query_params.get('parent_id')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        
        # Filter by maximum level
        max_level = self.request.query_params.get('max_level')
        if max_level:
            try:
                queryset = queryset.filter(level__lte=int(max_level))
            except ValueError:
                pass
        
        return queryset

    def destroy(self, request, *args, **kwargs):
        """Override delete to handle capability hierarchy properly."""
        capability = self.get_object()
        
        # Check if capability has children
        if capability.children.exists():
            return Response(
                {'error': 'Cannot delete capability with children. Please reassign or delete children first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Soft delete by changing status to ARCHIVED
        capability.status = 'ARCHIVED'
        capability.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get all direct children of a capability."""
        capability = self.get_object()
        children = capability.children.all()
        serializer = CapabilityListSerializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        """Get all ancestor capabilities."""
        capability = self.get_object()
        ancestors = capability.get_ancestors()
        serializer = CapabilityListSerializer(ancestors, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        """Get all descendant capabilities."""
        capability = self.get_object()
        descendants = capability.get_descendants()
        serializer = CapabilityListSerializer(descendants, many=True)
        return Response(serializer.data)


class BusinessGoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing business goals and triggering AI analysis.
    """
    queryset = BusinessGoal.objects.all()
    serializer_class = BusinessGoalSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'description']
    ordering_fields = ['submitted_at', 'title']
    ordering = ['-submitted_at']

    def get_serializer_class(self):
        """Use detailed serializer for retrieve action."""
        if self.action == 'retrieve':
            return BusinessGoalDetailSerializer
        return BusinessGoalSerializer

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """
        Trigger AI analysis for a business goal.
        
        This endpoint processes the goal description and optional PDF,
        generates capability recommendations using Gemini AI.
        """
        business_goal = self.get_object()
        
        if business_goal.status != 'PENDING_ANALYSIS':
            return Response(
                {'error': f'Goal is already {business_goal.status.lower()}. Only pending goals can be analyzed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Extract text from PDF if present
            goal_text = business_goal.description
            if business_goal.pdf_file:
                try:
                    pdf_text = self._extract_pdf_text(business_goal.pdf_file)
                    goal_text = f"{goal_text}\n\nAdditional details from PDF:\n{pdf_text}"
                except Exception as e:
                    # Continue without PDF if extraction fails
                    print(f"PDF extraction failed: {e}")

            # Get current capability map for context
            capabilities = Capability.objects.filter(status__in=['CURRENT', 'PROPOSED'])
            capability_context = self._build_capability_context(capabilities)

            # Generate AI recommendations
            recommendations_data = self._generate_recommendations(goal_text, capability_context)
            
            # Create recommendations in database
            created_count = self._create_recommendations(business_goal, recommendations_data)
            
            # Update goal status
            business_goal.status = 'ANALYZED'
            business_goal.save()
            
            return Response({
                'status': 'analysis complete',
                'recommendations_created': created_count,
                'summary': recommendations_data.get('summary_of_impact', 'Analysis completed successfully.')
            })
            
        except Exception as e:
            return Response(
                {'error': f'Analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _extract_pdf_text(self, pdf_file):
        """Extract text content from uploaded PDF file."""
        pdf_file.seek(0)  # Reset file pointer
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        
        return text.strip()

    def _build_capability_context(self, capabilities):
        """Build a structured context of the current capability map."""
        context = {
            "capability_map": [],
            "summary": {
                "total_capabilities": capabilities.count(),
                "root_capabilities": capabilities.filter(parent__isnull=True).count(),
                "status_distribution": {}
            }
        }
        
        # Add capability details
        for cap in capabilities.select_related('parent'):
            context["capability_map"].append({
                "name": cap.name,
                "description": cap.description,
                "level": cap.level,
                "parent": cap.parent.name if cap.parent else None,
                "status": cap.status,
                "importance": cap.strategic_importance
            })
        
        # Add status distribution
        for status_choice in ['CURRENT', 'PROPOSED', 'DEPRECATED', 'ARCHIVED']:
            count = capabilities.filter(status=status_choice).count()
            if count > 0:
                context["summary"]["status_distribution"][status_choice] = count
        
        return context

    def _generate_recommendations(self, goal_text, capability_context):
        """Generate recommendations using Gemini AI."""
        prompt = f"""You are a highly skilled business architect AI. Analyze the provided business goal in the context of the current business capabilities. Recommend changes to the capability map to achieve this goal.

Business Goal:
{goal_text}

Current Capability Map Context:
{json.dumps(capability_context, indent=2)}

Please provide recommendations in the following JSON format:
{{
  "summary_of_impact": "Overall summary of how this goal impacts the capability map.",
  "recommendations": [
    {{
      "type": "ADD_CAPABILITY",
      "rationale": "Explanation for this recommendation.",
      "details": {{
        "proposed_name": "New Capability Name",
        "proposed_description": "Description of the new capability",
        "proposed_parent_name": "Existing Parent Capability Name or null for top-level"
      }}
    }},
    {{
      "type": "MODIFY_CAPABILITY",
      "rationale": "Explanation for this recommendation.",
      "details": {{
        "target_capability_name": "Existing Capability Name",
        "proposed_name": "New Name (optional)",
        "proposed_description": "New Description (optional)",
        "proposed_parent_name": "New Parent Name (optional)"
      }}
    }},
    {{
      "type": "STRENGTHEN_CAPABILITY",
      "rationale": "Explanation for this recommendation.",
      "details": {{
        "target_capability_name": "Existing Capability Name"
      }}
    }},
    {{
      "type": "DELETE_CAPABILITY",
      "rationale": "Explanation for this recommendation.",
      "details": {{
        "target_capability_name": "Existing Capability Name"
      }}
    }}
  ]
}}

Focus on practical, actionable recommendations. Ensure capability names match exactly with existing ones when referencing them."""

        response = model.generate_content(prompt)
        
        try:
            # Parse JSON response
            recommendations_data = json.loads(response.text)
            return recommendations_data
        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic structure
            return {
                "summary_of_impact": "Analysis completed but response format was unexpected.",
                "recommendations": []
            }

    def _create_recommendations(self, business_goal, recommendations_data):
        """Create CapabilityRecommendation objects from AI response."""
        created_count = 0
        
        for rec in recommendations_data.get('recommendations', []):
            try:
                target_capability = None
                proposed_parent = None
                
                # Find target capability if specified
                details = rec.get('details', {})
                if 'target_capability_name' in details:
                    target_capability = Capability.objects.filter(
                        name=details['target_capability_name']
                    ).first()
                
                # Find proposed parent if specified
                if details.get('proposed_parent_name'):
                    proposed_parent = Capability.objects.filter(
                        name=details['proposed_parent_name']
                    ).first()
                
                # Create recommendation
                CapabilityRecommendation.objects.create(
                    business_goal=business_goal,
                    recommendation_type=rec['type'],
                    target_capability=target_capability,
                    proposed_name=details.get('proposed_name'),
                    proposed_description=details.get('proposed_description'),
                    proposed_parent=proposed_parent,
                    additional_details=rec.get('rationale', ''),
                    status='PENDING'
                )
                created_count += 1
                
            except Exception as e:
                print(f"Failed to create recommendation: {e}")
                continue
        
        return created_count

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        """Get all recommendations for a business goal."""
        business_goal = self.get_object()
        recommendations = business_goal.recommendations.all().order_by('-recommended_by_ai_at')
        serializer = CapabilityRecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)


class CapabilityRecommendationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing capability recommendations.
    """
    queryset = CapabilityRecommendation.objects.all()
    serializer_class = CapabilityRecommendationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['recommendation_type', 'status', 'business_goal']
    ordering_fields = ['recommended_by_ai_at', 'status']
    ordering = ['-recommended_by_ai_at']

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """
        Apply a capability recommendation to update the capability map.
        
        This handles creating, modifying, or deleting capabilities based on the recommendation.
        """
        recommendation = self.get_object()
        
        if recommendation.status != 'PENDING':
            return Response(
                {'error': 'Recommendation has already been processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                result = self._apply_recommendation(recommendation)
                
                # Update recommendation status
                recommendation.status = 'APPLIED'
                recommendation.applied_at = timezone.now()
                recommendation.save()
                
                return Response({
                    'status': 'recommendation applied',
                    'action_taken': result['action'],
                    'capability_id': result.get('capability_id'),
                    'message': result.get('message', 'Recommendation applied successfully.')
                })
                
        except Exception as e:
            return Response(
                {'error': f'Failed to apply recommendation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Mark a recommendation as rejected."""
        recommendation = self.get_object()
        
        if recommendation.status != 'PENDING':
            return Response(
                {'error': 'Only pending recommendations can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        recommendation.status = 'REJECTED'
        recommendation.save()
        
        return Response({'status': 'recommendation rejected'})

    def _apply_recommendation(self, recommendation):
        """Apply the specific recommendation based on its type."""
        rec_type = recommendation.recommendation_type
        
        if rec_type == 'ADD_CAPABILITY':
            return self._apply_add_capability(recommendation)
        elif rec_type == 'MODIFY_CAPABILITY':
            return self._apply_modify_capability(recommendation)
        elif rec_type == 'DELETE_CAPABILITY':
            return self._apply_delete_capability(recommendation)
        elif rec_type == 'STRENGTHEN_CAPABILITY':
            return self._apply_strengthen_capability(recommendation)
        else:
            raise ValueError(f"Unsupported recommendation type: {rec_type}")

    def _apply_add_capability(self, recommendation):
        """Create a new capability."""
        capability = Capability.objects.create(
            name=recommendation.proposed_name,
            description=recommendation.proposed_description or "New capability added via AI recommendation",
            parent=recommendation.proposed_parent,
            status='CURRENT',
            strategic_importance='MEDIUM'
        )
        
        return {
            'action': 'created_capability',
            'capability_id': str(capability.id),
            'message': f"Created new capability: {capability.name}"
        }

    def _apply_modify_capability(self, recommendation):
        """Modify an existing capability."""
        if not recommendation.target_capability:
            raise ValueError('Target capability not found for modification')
        
        capability = recommendation.target_capability
        changes = []
        
        if recommendation.proposed_name:
            capability.name = recommendation.proposed_name
            changes.append(f"name to '{recommendation.proposed_name}'")
        
        if recommendation.proposed_description:
            capability.description = recommendation.proposed_description
            changes.append("description")
        
        if recommendation.proposed_parent:
            capability.parent = recommendation.proposed_parent
            changes.append(f"parent to '{recommendation.proposed_parent.name}'")
        
        capability.save()
        
        return {
            'action': 'modified_capability',
            'capability_id': str(capability.id),
            'message': f"Modified {capability.name}: {', '.join(changes)}"
        }

    def _apply_delete_capability(self, recommendation):
        """Soft delete a capability by changing its status."""
        if not recommendation.target_capability:
            raise ValueError('Target capability not found for deletion')
        
        capability = recommendation.target_capability
        capability.status = 'DEPRECATED'
        capability.save()
        
        return {
            'action': 'deprecated_capability',
            'capability_id': str(capability.id),
            'message': f"Deprecated capability: {capability.name}"
        }

    def _apply_strengthen_capability(self, recommendation):
        """Strengthen a capability by increasing its strategic importance."""
        if not recommendation.target_capability:
            raise ValueError('Target capability not found for strengthening')
        
        capability = recommendation.target_capability
        
        # Upgrade strategic importance
        importance_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        current_index = importance_levels.index(capability.strategic_importance)
        if current_index < len(importance_levels) - 1:
            capability.strategic_importance = importance_levels[current_index + 1]
            capability.save()
        
        return {
            'action': 'strengthened_capability',
            'capability_id': str(capability.id),
            'message': f"Strengthened capability: {capability.name} (importance: {capability.strategic_importance})"
        }


class LLMQueryView(APIView):
    """
    General purpose endpoint for user-initiated LLM questions.
    """
    
    def post(self, request):
        """Handle LLM query requests."""
        serializer = LLMQuerySerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['query']
        context = serializer.validated_data.get('context', '')
        
        try:
            # Build context with current capability map if not provided
            if not context:
                capabilities = Capability.objects.filter(status__in=['CURRENT', 'PROPOSED'])
                capability_summary = self._build_capability_summary(capabilities)
                context = f"Current Business Capability Map Summary:\n{capability_summary}"
            
            # Construct prompt
            prompt = f"""You are a business architect AI assistant. Answer questions about business capabilities and strategy concisely and helpfully.

Context:
{context}

User Question:
{query}

Please provide a clear, actionable response that helps the user understand business capabilities and their strategic implications."""

            # Get response from Gemini
            response = model.generate_content(prompt)
            
            response_serializer = LLMResponseSerializer(data={
                'answer': response.text,
                'query': query,
                'context_used': context[:500] + "..." if len(context) > 500 else context
            })
            
            if response_serializer.is_valid():
                return Response(response_serializer.data)
            else:
                return Response(
                    {'error': 'Failed to format response'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': f'LLM query failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _build_capability_summary(self, capabilities):
        """Build a concise summary of the capability map for context."""
        summary = []
        root_capabilities = capabilities.filter(parent__isnull=True)
        
        for root_cap in root_capabilities:
            summary.append(f"• {root_cap.name}: {root_cap.description[:100]}...")
            
            # Add key sub-capabilities
            children = capabilities.filter(parent=root_cap, strategic_importance__in=['HIGH', 'CRITICAL'])
            for child in children[:3]:  # Limit to top 3 important children
                summary.append(f"  - {child.name}")
        
        return "\n".join(summary)


# Import timezone for applied_at timestamp
from django.utils import timezone
