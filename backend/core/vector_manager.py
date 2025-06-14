import faiss
import numpy as np
import os
import google.generativeai as genai

faiss.omp_set_num_threads(2)

from django.conf import settings
from django.apps import apps
from .constants import ContentTypes
from .models import VectorEmbedding

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


class VectorManager:
    def __init__(self):
        self.indexes = {}
        self.embedding_dimension = 768
        self.load_indexes()
    
    def get_model_classes(self):
        return {
            ContentTypes.CAPABILITY: apps.get_model('core', 'Capability'),
            ContentTypes.BUSINESS_GOAL: apps.get_model('core', 'BusinessGoal'),
            ContentTypes.RECOMMENDATION: apps.get_model('core', 'CapabilityRecommendation'),
        }
    
    def get_index_file_path(self, content_type):
        return os.path.join(settings.BASE_DIR, 'vector_indexes', f'{content_type.lower()}_index.faiss')
    
    def load_indexes(self):
        for content_type in [ContentTypes.CAPABILITY, ContentTypes.BUSINESS_GOAL, ContentTypes.RECOMMENDATION]:
            index_path = self.get_index_file_path(content_type)
            
            if os.path.exists(index_path):
                try:
                    self.indexes[content_type] = faiss.read_index(index_path)
                except Exception as e:
                    print(f"Error loading index for {content_type}: {e}")
                    self.indexes[content_type] = faiss.IndexFlatIP(self.embedding_dimension)
            else:
                self.indexes[content_type] = faiss.IndexFlatIP(self.embedding_dimension)

    def save_indexes(self):
        os.makedirs(os.path.join(settings.BASE_DIR, 'vector_indexes'), exist_ok=True)
        
        for content_type, index in self.indexes.items():
            index_path = self.get_index_file_path(content_type)
            try:
                faiss.write_index(index, index_path)
            except Exception as e:
                print(f"Error saving index for {content_type}: {e}")

    def generate_embedding(self, text):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Use the correct Gemini embedding API
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document",
                title="Business Capability Analysis"
            )
            
            embedding = np.array(result['embedding'], dtype=np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            logger.info(f"Successfully generated embedding for text: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding for text '{text[:50]}...': {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Return random embedding as fallback
            random_embedding = np.random.random(self.embedding_dimension).astype(np.float32)
            logger.warning("Using random embedding as fallback")
            return random_embedding

    def add_vector(self, content_type, object_id, text):
        try:
            embedding = self.generate_embedding(text)
            
            index_key = content_type
            if index_key not in self.indexes:
                print(f"Unknown content type: {content_type}")
                return False
            
            index = self.indexes[index_key]
            vector_index = index.ntotal
            
            index.add(np.array([embedding]))
            
            VectorEmbedding.objects.update_or_create(
                content_type=content_type,
                object_id=str(object_id),
                defaults={
                    'vector_index': vector_index,
                    'text_content': text[:1000]
                }
            )
            
            self.save_indexes()
            return True
            
        except Exception as e:
            print(f"Error adding vector: {e}")
            return False
    
    def search_similar(self, content_type, query_text, k=5, threshold=0.5):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            query_embedding = self.generate_embedding(query_text)
            
            index_key = content_type
            if index_key not in self.indexes:
                logger.error(f"Unknown content type: {content_type}")
                return []
            
            index = self.indexes[index_key]
            logger.info(f"Index for {content_type} has {index.ntotal} vectors")
            
            if index.ntotal == 0:
                logger.warning(f"No vectors in index for {content_type}")
                return []
            
            k = min(k, index.ntotal)
            logger.info(f"Searching for top {k} results with threshold {threshold}")
            
            scores, indices = index.search(np.array([query_embedding]), k)
            logger.info(f"Search returned scores: {scores[0][:5]} and indices: {indices[0][:5]}")
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                logger.info(f"Processing result {i}: score={score}, idx={idx}, threshold={threshold}")
                if score < threshold:
                    logger.info(f"Skipping result {i} due to low score: {score} < {threshold}")
                    continue
                
                try:
                    # Handle multiple VectorEmbeddings with same vector_index
                    vector_embeddings = VectorEmbedding.objects.filter(
                        content_type=content_type,
                        vector_index=idx
                    )
                    
                    if not vector_embeddings.exists():
                        logger.warning(f"No VectorEmbedding found for index {idx}")
                        continue
                    
                    # Use the most recent one if there are duplicates
                    vector_embedding = vector_embeddings.order_by('-updated_at').first()
                    logger.info(f"Found VectorEmbedding for index {idx}: {vector_embedding.object_id} (from {vector_embeddings.count()} candidates)")
                    
                    related_object = self.get_related_object(vector_embedding)
                    if related_object:
                        result = {
                            'object_id': vector_embedding.object_id,
                            'similarity_score': float(score),
                            'text_content': vector_embedding.text_content,
                            'content_type': content_type
                        }
                        
                        if hasattr(related_object, 'name'):
                            result['name'] = related_object.name
                        elif hasattr(related_object, 'title'):
                            result['name'] = related_object.title
                        
                        if hasattr(related_object, 'description'):
                            result['description'] = related_object.description
                        
                        results.append(result)
                        logger.info(f"Added result: {result['name']}")
                        
                except VectorEmbedding.DoesNotExist:
                    logger.warning(f"VectorEmbedding not found for index {idx}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing search result: {e}")
                    continue
            
            logger.info(f"Returning {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def get_related_object(self, vector_embedding):
        try:
            model_classes = self.get_model_classes()
            model_class = model_classes.get(vector_embedding.content_type)
            
            if not model_class:
                return None
            
            return model_class.objects.get(id=vector_embedding.object_id)
            
        except Exception as e:
            print(f"Error getting related object: {e}")
            return None
    
    def update_vector(self, content_type, object_id, new_text):
        try:
            self.remove_vector(content_type, object_id)
            return self.add_vector(content_type, object_id, new_text)
        except Exception as e:
            print(f"Error updating vector: {e}")
            return False

    def remove_vector(self, content_type, object_id):
        try:
            vector_embedding = VectorEmbedding.objects.get(
                content_type=content_type,
                object_id=str(object_id)
            )
            vector_embedding.delete()
            return True
            
        except VectorEmbedding.DoesNotExist:
            return False
        except Exception as e:
            print(f"Error removing vector: {e}")
            return False

    def rebuild_index(self, content_type):
        try:
            self.indexes[content_type] = faiss.IndexFlatIP(self.embedding_dimension)
            
            VectorEmbedding.objects.filter(content_type=content_type).delete()
            
            model_classes = self.get_model_classes()
            model_class = model_classes.get(content_type)
            
            if not model_class:
                return False
            
            objects = model_class.objects.all()
            for obj in objects:
                if content_type == ContentTypes.CAPABILITY:
                    text = f"{obj.name} {obj.description}"
                elif content_type == ContentTypes.BUSINESS_GOAL:
                    text = f"{obj.title} {obj.description}"
                elif content_type == ContentTypes.RECOMMENDATION:
                    text = f"{obj.proposed_name or ''} {obj.proposed_description or ''} {obj.additional_details or ''}"
                else:
                    continue
                
                self.add_vector(content_type, obj.id, text)
            
            return True
            
        except Exception as e:
            print(f"Error rebuilding index for {content_type}: {e}")
            return False

    def get_stats(self):
        stats = {}
        for content_type, index in self.indexes.items():
            stats[content_type] = {
                'total_vectors': index.ntotal,
                'dimension': self.embedding_dimension,
                'index_type': type(index).__name__
            }
        return stats


vector_manager = VectorManager() 