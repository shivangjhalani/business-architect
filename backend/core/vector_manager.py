import os
import json
import logging
import numpy as np
import faiss

faiss.omp_set_num_threads(1)  # Optimize CPU performance

from typing import List, Dict, Tuple, Optional, Any
from django.conf import settings
from django.db import transaction
import google.generativeai as genai

logger = logging.getLogger(__name__)

class VectorManager:
    
    def __init__(self):
        self.vector_storage_path = os.path.join(settings.BASE_DIR, 'vector_storage')
        self.embedding_dimension = 768  # Gemini embedding dimension
        self.indexes = {}
        self.metadata = {}
        
        os.makedirs(self.vector_storage_path, exist_ok=True)
        
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        self._load_indexes()
    
    def _get_models(self):
        from .models import VectorEmbedding, Capability, BusinessGoal, CapabilityRecommendation
        return VectorEmbedding, Capability, BusinessGoal, CapabilityRecommendation
    
    def _get_index_path(self, content_type: str) -> str:
        return os.path.join(self.vector_storage_path, f"{content_type.lower()}.faiss")
    
    def _load_indexes(self):
        """Load existing FAISS indexes from disk."""
        content_types = ['capabilities', 'business_goals', 'recommendations']
        
        for content_type in content_types:
            index_path = self._get_index_path(content_type)
            
            if os.path.exists(index_path):
                try:
                    self.indexes[content_type] = faiss.read_index(index_path)
                    logger.info(f"Loaded {content_type} index with {self.indexes[content_type].ntotal} vectors")
                except Exception as e:
                    logger.error(f"Error loading {content_type} index: {e}")
                    self.indexes[content_type] = faiss.IndexFlatIP(self.embedding_dimension)
            else:
                # Create new index using Inner Product (cosine similarity with normalized vectors)
                self.indexes[content_type] = faiss.IndexFlatIP(self.embedding_dimension)
                logger.info(f"Created new {content_type} index")

        # Load metadata
        metadata_path = self._get_metadata_path()
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _save_indexes(self):
        """Save all FAISS indexes to disk."""
        for content_type, index in self.indexes.items():
            try:
                index_path = self._get_index_path(content_type)
                faiss.write_index(index, index_path)
                logger.info(f"Saved {content_type} index with {index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Error saving {content_type} index: {e}")
        
        # Save metadata
        try:
            metadata_path = self._get_metadata_path()
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def _get_metadata_path(self) -> str:
        return os.path.join(self.vector_storage_path, "metadata.json")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using Gemini API."""
        try:
            text = text.strip()
            if not text:
                raise ValueError("Text cannot be empty")
            
            # Now embeddings make
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="semantic_similarity"
            )
            
            # Convert to numpy array and normalize for cosine similarity
            embedding = np.array(result['embedding'], dtype=np.float32)
            embedding = embedding / np.linalg.norm(embedding)  # Normalize for cosine similarity
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def add_vector(self, content_type: str, object_id: str, text: str) -> int:
        """Add a new vector to the appropriate FAISS index."""
        try:
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            # Convert content_type to index key
            index_key = content_type.lower() + 's' if not content_type.lower().endswith('s') else content_type.lower()
            if content_type == 'BUSINESS_GOAL':
                index_key = 'business_goals'
            elif content_type == 'RECOMMENDATION':
                index_key = 'recommendations'
            elif content_type == 'CAPABILITY':
                index_key = 'capabilities'
            
            # Add to FAISS index
            index = self.indexes[index_key]
            vector_index = index.ntotal  # Current count becomes the new index
            index.add(embedding.reshape(1, -1))
            
            # Store or update VectorEmbedding record
            with transaction.atomic():
                vector_embedding, created = self._get_models()[0].objects.update_or_create(
                    content_type=content_type,
                    object_id=object_id,
                    defaults={
                        'vector_index': vector_index,
                        'text_content': text,
                        'embedding_model': 'text-embedding-004'
                    }
                )
            
            # Save indexes
            self._save_indexes()
            
            logger.info(f"Added vector for {content_type} {object_id} at index {vector_index}")
            return vector_index
            
        except Exception as e:
            logger.error(f"Error adding vector for {content_type} {object_id}: {e}")
            raise
    
    def search_similar(self, content_type: str, query_text: str, k: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find similar vectors using FAISS similarity search."""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query_text)
            
            # Convert content_type to index key
            index_key = content_type.lower() + 's' if not content_type.lower().endswith('s') else content_type.lower()
            if content_type == 'BUSINESS_GOAL':
                index_key = 'business_goals'
            elif content_type == 'RECOMMENDATION':
                index_key = 'recommendations'
            elif content_type == 'CAPABILITY':
                index_key = 'capabilities'
            
            index = self.indexes[index_key]
            
            if index.ntotal == 0:
                return []
            
            # Search for similar vectors
            scores, indices = index.search(query_embedding.reshape(1, -1), min(k, index.ntotal))
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if score >= threshold:
                    # Find the corresponding VectorEmbedding record
                    try:
                        vector_embedding = self._get_models()[0].objects.get(
                            content_type=content_type,
                            vector_index=idx
                        )
                        
                        # Get the related object
                        related_obj = vector_embedding.related_object
                        if related_obj:
                            result = {
                                'object_id': str(vector_embedding.object_id),
                                'similarity_score': float(score),
                                'vector_index': idx,
                                'text_content': vector_embedding.text_content,
                            }
                            
                            # Add object-specific fields
                            if content_type == 'CAPABILITY':
                                result.update({
                                    'name': related_obj.name,
                                    'description': related_obj.description,
                                    'full_path': related_obj.full_path,
                                    'strategic_importance': related_obj.strategic_importance,
                                    'status': related_obj.status,
                                })
                            elif content_type == 'BUSINESS_GOAL':
                                result.update({
                                    'title': related_obj.title,
                                    'description': related_obj.description,
                                    'status': related_obj.status,
                                    'submitted_at': related_obj.submitted_at.isoformat(),
                                    'recommendations_count': related_obj.recommendations_count,
                                })
                            elif content_type == 'RECOMMENDATION':
                                result.update({
                                    'recommendation_type': related_obj.recommendation_type,
                                    'proposed_name': related_obj.proposed_name,
                                    'proposed_description': related_obj.proposed_description,
                                    'status': related_obj.status,
                                    'business_goal_title': related_obj.business_goal.title,
                                })
                            
                            results.append(result)
                    
                    except self._get_models()[0].DoesNotExist:
                        logger.warning(f"VectorEmbedding not found for {content_type} at index {idx}")
                        continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar {content_type}: {e}")
            return []
    
    def update_vector(self, content_type: str, object_id: str, new_text: str):
        """Update an existing vector with new content."""
        try:
            # Remove old vector
            self.remove_vector(content_type, object_id)
            
            # Add new vector
            self.add_vector(content_type, object_id, new_text)
            
            logger.info(f"Updated vector for {content_type} {object_id}")
            
        except Exception as e:
            logger.error(f"Error updating vector for {content_type} {object_id}: {e}")
            raise
    
    def remove_vector(self, content_type: str, object_id: str):
        """Remove a vector from the index."""
        try:
            # Find and delete the VectorEmbedding record
            vector_embedding = self._get_models()[0].objects.filter(
                content_type=content_type,
                object_id=object_id
            ).first()
            
            if vector_embedding:
                vector_embedding.delete() # !!!!! INEFFICIENT IN FAISS
                logger.info(f"Removed vector embedding for {content_type} {object_id}")
                            
        except Exception as e:
            logger.error(f"Error removing vector for {content_type} {object_id}: {e}")
            raise
    
    def rebuild_index(self, content_type: str):
        """Rebuild a FAISS index from scratch."""
        try:
            logger.info(f"Rebuilding {content_type} index...")
            
            # Convert content_type to index key
            index_key = content_type.lower() + 's' if not content_type.lower().endswith('s') else content_type.lower()
            if content_type == 'BUSINESS_GOAL':
                index_key = 'business_goals'
            elif content_type == 'RECOMMENDATION':
                index_key = 'recommendations'
            elif content_type == 'CAPABILITY':
                index_key = 'capabilities'
            
            # Create new index
            self.indexes[index_key] = faiss.IndexFlatIP(self.embedding_dimension)
            
            # Clear existing VectorEmbedding records for this content type
            self._get_models()[0].objects.filter(content_type=content_type).delete()
            
            # Rebuild from source objects
            if content_type == 'CAPABILITY':
                objects = self._get_models()[1].objects.filter(status__in=['CURRENT', 'PROPOSED'])
                for obj in objects:
                    text = f"{obj.name} {obj.description}"
                    self.add_vector('CAPABILITY', str(obj.id), text)
                    
            elif content_type == 'BUSINESS_GOAL':
                objects = self._get_models()[2].objects.all()
                for obj in objects:
                    text = f"{obj.title} {obj.description}"
                    self.add_vector('BUSINESS_GOAL', str(obj.id), text)
                    
            elif content_type == 'RECOMMENDATION':
                objects = self._get_models()[3].objects.all()
                for obj in objects:
                    text = f"{obj.get_recommendation_type_display()} {obj.proposed_name or ''} {obj.proposed_description or ''} {obj.additional_details or ''}"
                    self.add_vector('RECOMMENDATION', str(obj.id), text)
            
            logger.info(f"Successfully rebuilt {content_type} index with {self.indexes[index_key].ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Error rebuilding {content_type} index: {e}")
            raise
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about all indexes."""
        stats = {
            'indexes': {},
            'overall_health': 'healthy',
            'embedding_model': 'text-embedding-004',
            'vector_dimension': self.embedding_dimension,
            'total_storage_mb': 0
        }
        
        for content_type, index in self.indexes.items():
            index_path = self._get_index_path(content_type)
            size_mb = 0
            
            if os.path.exists(index_path):
                size_mb = os.path.getsize(index_path) / (1024 * 1024)
            
            stats['indexes'][content_type] = {
                'total_vectors': index.ntotal,
                'index_size_mb': round(size_mb, 2),
                'health': 'healthy'
            }
            
            stats['total_storage_mb'] += size_mb
        
        stats['total_storage_mb'] = round(stats['total_storage_mb'], 2)
        return stats

# Global instance
vector_manager = VectorManager() 