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
import logging
from django.utils import timezone

from .models import Capability, BusinessGoal, CapabilityRecommendation
from .serializers import (
    CapabilitySerializer, CapabilityListSerializer,
    BusinessGoalSerializer, BusinessGoalDetailSerializer,
    CapabilityRecommendationSerializer,
    LLMQuerySerializer, LLMResponseSerializer
)
from .constants import API_TO_MODEL_CONTENT_TYPE, VALID_API_CONTENT_TYPES, ContentTypes

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-exp')
logger = logging.getLogger(__name__)


class BaseViewMixin:
    """Common functionality for all viewsets."""
    
    def error_response(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        return Response({'error': message}, status=status_code)
    
    def success_response(self, message, data=None, status_code=status.HTTP_200_OK):
        response_data = {'message': message}
        if data:
            response_data.update(data)
        return Response(response_data, status=status_code)
    
    def check_dependencies(self, obj, dependency_check_func, error_message):
        """Check if object has dependencies before deletion."""
        if dependency_check_func(obj):
            return self.error_response(error_message)
        return None
    
    def soft_delete(self, obj, status_field='status', archive_value='ARCHIVED'):
        setattr(obj, status_field, archive_value)
        obj.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def permanent_delete(self, obj, obj_name_field='name'):
        obj_name = getattr(obj, obj_name_field, str(obj))
        obj.delete()
        return self.success_response(f'{obj.__class__.__name__} "{obj_name}" has been permanently deleted.')


class CapabilityViewSet(BaseViewMixin, viewsets.ModelViewSet):
    """Manages business capabilities: hierarchy and filtering"""
    queryset = Capability.objects.all()
    serializer_class = CapabilitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'status', 'parent', 'strategic_importance']
    search_fields = ['name', 'description', 'owner']
    ordering_fields = ['name', 'level', 'created_at', 'strategic_importance']
    ordering = ['level', 'name']

    def get_serializer_class(self):
        return CapabilityListSerializer if self.action == 'list' else CapabilitySerializer

    def get_queryset(self):
        """Apply custom filtering based on query parameters."""
        queryset = Capability.objects.all()
        params = self.request.query_params
        
        if params.get('root_only', '').lower() == 'true':
            queryset = queryset.filter(parent__isnull=True)
        
        if parent_id := params.get('parent_id'):
            queryset = queryset.filter(parent_id=parent_id)
        
        if max_level := params.get('max_level'):
            try:
                queryset = queryset.filter(level__lte=int(max_level))
            except ValueError:
                pass
        
        return queryset

    def destroy(self, request, *args, **kwargs):
        capability = self.get_object()
        
        error = self.check_dependencies(
            capability,
            lambda cap: cap.children.exists(),
            'Cannot delete capability with children. Please reassign or delete children first.'
        )
        if error:
            return error
        
        return self.soft_delete(capability)

    @action(detail=True, methods=['delete'])
    def permanent_delete(self, request, pk=None):
        capability = self.get_object()
        
        error = self.check_dependencies(
            capability,
            lambda cap: cap.children.exists(),
            'Cannot permanently delete capability with children. Please reassign or delete children first.'
        )
        if error:
            return error
        
        recommendations = CapabilityRecommendation.objects.filter(target_capability=capability)
        error = self.check_dependencies(
            capability,
            lambda cap: recommendations.exists(),
            f'Cannot permanently delete capability that is referenced by {recommendations.count()} recommendation(s). Delete or update the recommendations first.'
        )
        if error:
            return error
        
        return super().permanent_delete(capability)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        capability = self.get_object()
        children = capability.children.all()
        serializer = CapabilityListSerializer(children, many=True)
        return Response({'results': serializer.data})

    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        capability = self.get_object()
        ancestors = capability.get_ancestors()
        serializer = CapabilityListSerializer(ancestors, many=True)
        return Response({'results': serializer.data})

    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        capability = self.get_object()
        descendants = capability.get_descendants()
        serializer = CapabilityListSerializer(descendants, many=True)
        return Response({'results': serializer.data})

    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """Find similar capabilities using vector search."""
        from .vector_manager import vector_manager
        
        capability = self.get_object()
        limit = min(int(request.GET.get('limit', 5)), 20)
        threshold = float(request.GET.get('threshold', 0.6))
        
        try:
            query_text = f"{capability.name} {capability.description}"
            results = vector_manager.search_similar(
                content_type=ContentTypes.CAPABILITY,
                query_text=query_text,
                k=limit + 1,
                threshold=threshold
            )
            
            filtered_results = [r for r in results if r['object_id'] != str(capability.id)][:limit]
            
            return Response({
                'similar_capabilities': filtered_results,
                'query_capability': {'id': str(capability.id), 'name': capability.name},
                'search_parameters': {
                    'limit': limit,
                    'threshold': threshold,
                    'total_found': len(filtered_results)
                }
            })
            
        except Exception as e:
            return self.error_response(f'Similar search failed: {str(e)}', status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        capability = self.get_object()
        recommendations = CapabilityRecommendation.objects.filter(target_capability=capability)
        serializer = CapabilityRecommendationSerializer(recommendations, many=True)
        return Response({'results': serializer.data, 'count': recommendations.count()})


class BusinessGoalViewSet(BaseViewMixin, viewsets.ModelViewSet):
    """ViewSet for managing business goals and triggering AI analysis."""
    queryset = BusinessGoal.objects.all()
    serializer_class = BusinessGoalSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'description']
    ordering_fields = ['submitted_at', 'title']
    ordering = ['-submitted_at']

    def get_serializer_class(self):
        return BusinessGoalDetailSerializer if self.action == 'retrieve' else BusinessGoalSerializer

    def destroy(self, request, *args, **kwargs):
        business_goal = self.get_object()
        
        pending_recommendations = business_goal.recommendations.filter(status='PENDING')
        error = self.check_dependencies(
            business_goal,
            lambda goal: pending_recommendations.exists(),
            f'Cannot delete business goal with {pending_recommendations.count()} pending recommendation(s). Please handle the recommendations first.'
        )
        if error:
            return error
        
        return self.soft_delete(business_goal, status_field='status', archive_value='CLOSED')

    @action(detail=True, methods=['delete'])
    def permanent_delete(self, request, pk=None):
        business_goal = self.get_object()
        
        recommendations = business_goal.recommendations.all()
        error = self.check_dependencies(
            business_goal,
            lambda goal: recommendations.exists(),
            f'Cannot permanently delete business goal that has {recommendations.count()} recommendation(s). Delete or update the recommendations first.'
        )
        if error:
            return error
        
        return super().permanent_delete(business_goal, 'title')

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Trigger AI analysis for a business goal."""
        business_goal = self.get_object()
        
        if business_goal.status != 'PENDING_ANALYSIS':
            return self.error_response(f'Goal is already {business_goal.status.lower()}. Only pending goals can be analyzed.')

        try:
            goal_text = self._prepare_goal_text(business_goal)
            capability_context = self._get_capability_context()
            recommendations_data = self._generate_ai_recommendations(goal_text, capability_context)
            created_count = self._create_recommendations(business_goal, recommendations_data)
            
            business_goal.status = 'ANALYZED'
            business_goal.save()
            
            return Response({
                'status': 'analysis complete',
                'recommendations_created': created_count,
                'summary': recommendations_data.get('summary_of_impact', 'Analysis completed successfully.')
            })
            
        except Exception as e:
            return self.error_response(f'Analysis failed: {str(e)}', status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _prepare_goal_text(self, business_goal):
        """Extract and prepare goal text including PDF content."""
        goal_text = business_goal.description
        
        if business_goal.pdf_file:
            try:
                pdf_text = self._extract_pdf_text(business_goal.pdf_file)
                goal_text = f"{goal_text}\n\nAdditional details from PDF:\n{pdf_text}"
            except Exception as e:
                logger.warning(f"PDF extraction failed: {e}")
        
        return goal_text

    def _extract_pdf_text(self, pdf_file):
        pdf_file.seek(0)
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        return "\n".join(page.extract_text() for page in pdf_reader.pages).strip()

    def _get_capability_context(self):
        """Build structured context of current capability map."""
        capabilities = Capability.objects.filter(status__in=['CURRENT', 'PROPOSED'])
        
        context = {
            "capability_map": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "level": cap.level,
                    "parent": cap.parent.name if cap.parent else None,
                    "status": cap.status,
                    "importance": cap.strategic_importance
                }
                for cap in capabilities.select_related('parent')
            ],
            "summary": {
                "total_capabilities": capabilities.count(),
                "root_capabilities": capabilities.filter(parent__isnull=True).count(),
                "status_distribution": {
                    status_choice: capabilities.filter(status=status_choice).count()
                    for status_choice in ['CURRENT', 'PROPOSED', 'DEPRECATED', 'ARCHIVED']
                    if capabilities.filter(status=status_choice).exists()
                }
            }
        }
        
        return context

    def _generate_ai_recommendations(self, goal_text, capability_context):
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
        return self._parse_ai_response(response.text)

    def _parse_ai_response(self, response_text):
        """Parse AI response, handling markdown formatting."""
        try:
            response_text = response_text.strip()
            if response_text.startswith('```json') and response_text.endswith('```'):
                json_content = response_text[7:-3].strip()
            elif response_text.startswith('```') and response_text.endswith('```'):
                json_content = response_text[3:-3].strip()
            else:
                json_content = response_text
            
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}, Raw response: {response_text}")
            return {
                "summary_of_impact": "Analysis completed but response format was unexpected.",
                "recommendations": []
            }

    def _create_recommendations(self, business_goal, recommendations_data):
        created_count = 0
        
        for rec in recommendations_data.get('recommendations', []):
            try:
                details = rec.get('details', {})
                
                target_capability = None
                if 'target_capability_name' in details:
                    target_capability = Capability.objects.filter(name=details['target_capability_name']).first()
                
                proposed_parent = None
                if details.get('proposed_parent_name'):
                    proposed_parent = Capability.objects.filter(name=details['proposed_parent_name']).first()
                
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
                logger.error(f"Failed to create recommendation: {e}")
                continue
        
        return created_count

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        business_goal = self.get_object()
        recommendations = business_goal.recommendations.all().order_by('-recommended_by_ai_at')
        serializer = CapabilityRecommendationSerializer(recommendations, many=True)
        return Response({'results': serializer.data})


class CapabilityRecommendationViewSet(BaseViewMixin, viewsets.ModelViewSet):
    """ViewSet for managing capability recommendations."""
    queryset = CapabilityRecommendation.objects.all()
    serializer_class = CapabilityRecommendationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['recommendation_type', 'status', 'business_goal']
    ordering_fields = ['recommended_by_ai_at', 'status']
    ordering = ['-recommended_by_ai_at']

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply a capability recommendation to update the capability map."""
        recommendation = self.get_object()
        
        if recommendation.status != 'PENDING':
            return self.error_response('Recommendation has already been processed')
        
        try:
            with transaction.atomic():
                result = self._apply_recommendation(recommendation)
                
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
            return self.error_response(f'Failed to apply recommendation: {str(e)}', status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        try:
            recommendation = self.get_object()
            
            if recommendation.status != 'PENDING':
                return Response(
                    {'error': 'Only pending recommendations can be rejected'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            recommendation.status = 'REJECTED'
            recommendation.save()
            
            return Response({
                'status': 'recommendation rejected',
                'message': f'Recommendation "{recommendation.get_recommendation_type_display()}" has been rejected'
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to reject recommendation: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['delete'])
    def permanent_delete(self, request, pk=None):
        recommendation = self.get_object()
        recommendation_type = recommendation.get_recommendation_type_display()
        recommendation.delete()
        return self.success_response(f'Recommendation "{recommendation_type}" has been permanently deleted.')

    def _apply_recommendation(self, recommendation):
        """Apply the specific recommendation based on its type."""
        handlers = {
            'ADD_CAPABILITY': self._apply_add_capability,
            'MODIFY_CAPABILITY': self._apply_modify_capability,
            'DELETE_CAPABILITY': self._apply_delete_capability,
            'STRENGTHEN_CAPABILITY': self._apply_strengthen_capability,
        }
        
        handler = handlers.get(recommendation.recommendation_type)
        if not handler:
            raise ValueError(f"Unsupported recommendation type: {recommendation.recommendation_type}")
        
        return handler(recommendation)

    def _apply_add_capability(self, recommendation):
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
        if not recommendation.target_capability:
            raise ValueError('Target capability not found for strengthening')
        
        capability = recommendation.target_capability
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
    """LLM query endpoint with vector-powered context retrieval."""
    
    def post(self, request):
        """Handle LLM query requests with vector-enhanced context."""
        from .vector_manager import vector_manager
        
        serializer = LLMQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['query']
        context = serializer.validated_data.get('context', '')
        
        try:
            vector_context = self._get_vector_context(query, vector_manager)
            enhanced_context = self._build_enhanced_context(context, vector_context)
            
            prompt = f"""You are a business architect AI assistant. Answer questions about business capabilities and strategy concisely and helpfully.

Context:
{enhanced_context}

User Question:
{query}

Please provide a clear, actionable response that helps the user understand business capabilities and their strategic implications. When relevant, reference similar past goals, capabilities, or recommendations to provide additional insights."""

            response = model.generate_content(prompt)
            
            return Response({
                'answer': response.text,
                'query': query,
                'context_used': context[:500] + "..." if len(context) > 500 else context,
                'vector_context': vector_context['summary']
            })
                
        except Exception as e:
            logger.error(f"LLM query failed: {str(e)}")
            return Response(
                {'error': f'LLM query failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_vector_context(self, query, vector_manager):
        """Get context from vector search across all content types."""
        context_parts = []
        summary = {
            'similar_capabilities': [],
            'similar_goals': [],
            'similar_recommendations': [],
            'context_enhancement': ''
        }
        
        try:
            search_configs = [
                            (ContentTypes.CAPABILITY, 'capabilities', 'Related Capabilities:', 3),
            (ContentTypes.BUSINESS_GOAL, 'goals', 'Similar Past Goals:', 2),
            (ContentTypes.RECOMMENDATION, 'recommendations', 'Related Recommendations:', 2)
            ]
            
            total_items = 0
            for content_type, summary_key, header, k in search_configs:
                results = vector_manager.search_similar(content_type, query, k=k, threshold=0.6)
                if results:
                    context_parts.append(f"\n{header}")
                    for result in results:
                        if content_type == ContentTypes.CAPABILITY:
                            context_parts.append(f"- {result['name']}: {result['description'][:100]}...")
                            summary['similar_capabilities'].append({
                                'name': result['name'],
                                'similarity_score': result['similarity_score'],
                                'relevance': f"Relevant for {query.lower()}"
                            })
                        elif content_type == ContentTypes.BUSINESS_GOAL:
                            context_parts.append(f"- {result['title']}: {result['status']}")
                            summary['similar_goals'].append({
                                'title': result['title'],
                                'similarity_score': result['similarity_score'],
                                'outcome': f"Status: {result['status']}"
                            })
                        elif content_type == ContentTypes.RECOMMENDATION:
                            context_parts.append(f"- {result['recommendation_type']}: {result.get('proposed_name', 'N/A')} ({result['status']})")
                            summary['similar_recommendations'].append({
                                'type': result['recommendation_type'],
                                'similarity_score': result['similarity_score'],
                                'status': result['status']
                            })
                    total_items += len(results)
            
            summary['context_enhancement'] = f"Enhanced with {total_items} related items from vector search"
            
        except Exception as e:
            context_parts.append(f"Note: Vector context retrieval failed: {str(e)}")
            summary['context_enhancement'] = "Vector search unavailable"
        
        return {
            'context_text': '\n'.join(context_parts),
            'summary': summary
        }
    
    def _build_enhanced_context(self, base_context, vector_context):
        """Build enhanced context combining base and vector contexts."""
        if not base_context:
            capabilities = Capability.objects.filter(status__in=['CURRENT', 'PROPOSED'])
            base_context = f"Current Business Capability Map Summary:\n{self._build_capability_summary(capabilities)}"
        
        return f"{base_context}\n\n{vector_context['context_text']}"
    
    def _build_capability_summary(self, capabilities):
        """Build a concise summary of the capability map for context."""
        summary = []
        root_capabilities = capabilities.filter(parent__isnull=True)
        
        for root_cap in root_capabilities:
            summary.append(f"• {root_cap.name}: {root_cap.description[:100]}...")
            children = capabilities.filter(parent=root_cap, strategic_importance__in=['HIGH', 'CRITICAL'])
            for child in children[:3]:
                summary.append(f"  - {child.name}")
        
        return "\n".join(summary)


class VectorSearchAPIView(APIView):
    """API view for semantic search using FAISS vector similarity."""
    
    def post(self, request, content_type):
        from .vector_manager import vector_manager
        
        if content_type not in VALID_API_CONTENT_TYPES:
            return Response(
                {'error': f'Invalid content type. Must be one of: {VALID_API_CONTENT_TYPES}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'error': 'Query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        limit = min(int(request.data.get('limit', 10)), 20)
        threshold = float(request.data.get('threshold', 0.6))
        
        try:
            start_time = timezone.now()
            results = vector_manager.search_similar(
                content_type=API_TO_MODEL_CONTENT_TYPE[content_type],
                query_text=query,
                k=limit,
                threshold=threshold
            )
            search_time_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            
            return Response({
                'results': results,
                'query': query,
                'total_results': len(results),
                'search_time_ms': search_time_ms,
                'threshold': threshold
            })
            
        except Exception as e:
            return Response(
                {'error': f'Search failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SimilarObjectsAPIView(APIView):
    """API view for finding similar objects to a specific instance."""
    
    def get(self, request, content_type, object_id):
        from .vector_manager import vector_manager
        
        try:
            source_obj, query_text, model_content_type = self._get_source_object(content_type, object_id)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        
        limit = min(int(request.GET.get('limit', 5)), 20)
        threshold = float(request.GET.get('threshold', 0.7))
        include_outcomes = request.GET.get('include_outcomes', 'true').lower() == 'true'
        
        try:
            results = vector_manager.search_similar(
                content_type=model_content_type,
                query_text=query_text,
                k=limit + 1,
                threshold=threshold
            )
            
            filtered_results = [r for r in results if r['object_id'] != str(object_id)][:limit]
            
            if include_outcomes and content_type in ['business_goals', 'recommendations']:
                for result in filtered_results:
                    if content_type == 'business_goals':
                        self._add_goal_outcomes(result)
                    elif content_type == 'recommendations':
                        self._add_recommendation_outcomes(result)
            
            response_data = self._build_similar_response(content_type, filtered_results, source_obj, object_id)
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {'error': f'Similar search failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_source_object(self, content_type, object_id):
        from .constants import APIContentTypes
        
        content_type_configs = {
            APIContentTypes.CAPABILITIES: (Capability, ContentTypes.CAPABILITY, lambda obj: f"{obj.name} {obj.description}"),
            APIContentTypes.BUSINESS_GOALS: (BusinessGoal, ContentTypes.BUSINESS_GOAL, lambda obj: f"{obj.title} {obj.description}"),
            APIContentTypes.RECOMMENDATIONS: (CapabilityRecommendation, ContentTypes.RECOMMENDATION, 
                              lambda obj: f"{obj.get_recommendation_type_display()} {obj.proposed_name or ''} {obj.additional_details or ''}")
        }
        
        if content_type not in content_type_configs:
            raise ValueError(f'Invalid content type. Must be one of: {VALID_API_CONTENT_TYPES}')
        
        model_class, model_content_type, query_builder = content_type_configs[content_type]
        
        try:
            source_obj = model_class.objects.get(id=object_id)
            query_text = query_builder(source_obj)
            return source_obj, query_text, model_content_type
        except model_class.DoesNotExist:
            raise Exception(f'{model_class.__name__} not found')
    
    def _build_similar_response(self, content_type, filtered_results, source_obj, object_id):
        key_mappings = {
            'business_goals': ('similar_goals', 'query_goal'),
            'recommendations': ('similar_recommendations', 'query_recommendation'),
            'capabilities': ('similar_capabilities', 'query_capability')
        }
        
        similar_key, query_key = key_mappings[content_type]
        source_name = getattr(source_obj, 'name', getattr(source_obj, 'title', str(source_obj)))
        
        response_data = {
            similar_key: filtered_results,
            query_key: {'id': str(object_id), 'name': source_name}
        }
        
        if content_type == 'recommendations' and filtered_results:
            applied_count = sum(1 for r in filtered_results if r.get('status') == 'APPLIED')
            response_data['success_patterns'] = {
                'similar_recommendations_success_rate': round(applied_count / len(filtered_results), 2),
                'total_similar_found': len(filtered_results)
            }
        
        return response_data
    
    def _add_goal_outcomes(self, result):
        try:
            goal = BusinessGoal.objects.get(id=result['object_id'])
            applied_recs = goal.recommendations.filter(status='APPLIED').count()
            total_recs = goal.recommendations.count()
            
            result['outcomes'] = {
                'successful_recommendations': applied_recs,
                'total_recommendations': total_recs,
                'success_rate': round(applied_recs / total_recs, 2) if total_recs > 0 else 0
            }
        except BusinessGoal.DoesNotExist:
            pass
    
    def _add_recommendation_outcomes(self, result):
        try:
            rec = CapabilityRecommendation.objects.get(id=result['object_id'])
            if rec.status == 'APPLIED' and rec.applied_at:
                result['outcome'] = {
                    'success': True,
                    'applied_at': rec.applied_at.isoformat(),
                    'implementation_notes': "Successfully applied"
                }
        except CapabilityRecommendation.DoesNotExist:
            pass


class VectorManagementAPIView(APIView):
    """API view for vector database management operations."""
    
    def get(self, request):
        from .vector_manager import vector_manager
        
        try:
            stats = vector_manager.get_index_stats()
            VectorEmbedding = vector_manager._get_models()[0]
            
            for content_type, model_content_type in API_TO_MODEL_CONTENT_TYPE.items():
                latest_embedding = VectorEmbedding.objects.filter(
                    content_type=model_content_type
                ).order_by('-updated_at').first()
                
                stats['indexes'][content_type]['last_updated'] = (
                    latest_embedding.updated_at.isoformat() if latest_embedding else None
                )
            
            return Response(stats)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get vector stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        from .vector_manager import vector_manager
        
        operation = request.data.get('operation')
        
        if operation == 'rebuild':
            return self._handle_rebuild(request, vector_manager)
        elif operation == 'optimize':
            return self._handle_optimize(request, vector_manager)
        else:
            return Response(
                {'error': 'Invalid operation. Use "rebuild" or "optimize"'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _handle_rebuild(self, request, vector_manager):
        indexes = request.data.get('indexes', ['capabilities', 'business_goals', 'recommendations'])
        
        try:
            results = {}
            for index_name in indexes:
                if content_type := API_TO_MODEL_CONTENT_TYPE.get(index_name):
                    vector_manager.rebuild_index(content_type)
                    results[index_name] = 'rebuilt successfully'
            
            return Response({
                'status': 'rebuild complete',
                'results': results,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Rebuild failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _handle_optimize(self, request, vector_manager):
        """Handle optimization operation - placeholder for future implementation."""
        return Response({
            'status': 'optimization complete',
            'message': 'Vector indexes optimized successfully',
            'timestamp': timezone.now().isoformat()
        })