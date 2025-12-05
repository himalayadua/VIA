"""Category Retriever - Stage A: Fast Candidate Retrieval.

Implements dual-index system for fast category candidate retrieval:
1. Vector index (ANN) for semantic matching
2. Keyword index (BM25) for lexical matching

Combines both signals to retrieve top-K candidates in < 50ms.
"""

import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
from collections import defaultdict, Counter
import math

from .category_profile import CategoryProfile, CategoryProfileStore

logger = logging.getLogger(__name__)


class VectorIndex:
    """Simple vector index using numpy for semantic search.
    
    For production, consider using FAISS or Annoy for better performance.
    """
    
    def __init__(self):
        """Initialize vector index."""
        self.embeddings: Dict[str, np.ndarray] = {}
        self.profile_ids: List[str] = []
    
    def add(self, profile_id: str, embedding: np.ndarray) -> None:
        """Add embedding to index."""
        self.embeddings[profile_id] = embedding
        if profile_id not in self.profile_ids:
            self.profile_ids.append(profile_id)
    
    def search(self, query_embedding: np.ndarray, top_k: int = 20) -> List[Tuple[str, float]]:
        """Search for similar embeddings using cosine similarity.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            
        Returns:
            List of (profile_id, similarity_score) tuples
        """
        if not self.embeddings:
            return []
        
        similarities = []
        
        for profile_id, embedding in self.embeddings.items():
            # Cosine similarity
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding) + 1e-10
            )
            similarities.append((profile_id, float(similarity)))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def remove(self, profile_id: str) -> None:
        """Remove embedding from index."""
        if profile_id in self.embeddings:
            del self.embeddings[profile_id]
            self.profile_ids.remove(profile_id)


class KeywordIndex:
    """Inverted index for keyword-based search (BM25-style).
    
    Maps terms → profile IDs with TF-IDF-like scoring.
    """
    
    def __init__(self):
        """Initialize keyword index."""
        self.index: Dict[str, Dict[str, float]] = defaultdict(dict)  # term → {profile_id: score}
        self.doc_lengths: Dict[str, int] = {}  # profile_id → keyword count
        self.avg_doc_length: float = 0.0
        self.num_docs: int = 0
    
    def add(self, profile_id: str, keywords: List[str], keyword_scores: Dict[str, float]) -> None:
        """Add keywords to index.
        
        Args:
            profile_id: Profile identifier
            keywords: List of keywords
            keyword_scores: Keyword importance scores
        """
        # Store document length
        self.doc_lengths[profile_id] = len(keywords)
        self.num_docs += 1
        self._update_avg_doc_length()
        
        # Add to inverted index
        for keyword in keywords:
            score = keyword_scores.get(keyword, 1.0)
            self.index[keyword.lower()][profile_id] = score
    
    def search(self, query_keywords: List[str], top_k: int = 20) -> List[Tuple[str, float]]:
        """Search using BM25-style scoring.
        
        Args:
            query_keywords: Query keywords
            top_k: Number of results to return
            
        Returns:
            List of (profile_id, bm25_score) tuples
        """
        if not self.index or not query_keywords:
            return []
        
        # BM25 parameters
        k1 = 1.5
        b = 0.75
        
        # Calculate scores for each document
        scores = defaultdict(float)
        
        for keyword in query_keywords:
            keyword_lower = keyword.lower()
            
            if keyword_lower not in self.index:
                continue
            
            # IDF calculation
            df = len(self.index[keyword_lower])  # Document frequency
            idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0)
            
            # Score each document containing this keyword
            for profile_id, tf_score in self.index[keyword_lower].items():
                doc_length = self.doc_lengths.get(profile_id, 1)
                
                # BM25 formula
                numerator = tf_score * (k1 + 1)
                denominator = tf_score + k1 * (1 - b + b * (doc_length / self.avg_doc_length))
                
                scores[profile_id] += idf * (numerator / denominator)
        
        # Sort by score descending
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def remove(self, profile_id: str) -> None:
        """Remove profile from index."""
        # Remove from inverted index
        for term_dict in self.index.values():
            if profile_id in term_dict:
                del term_dict[profile_id]
        
        # Remove document length
        if profile_id in self.doc_lengths:
            del self.doc_lengths[profile_id]
            self.num_docs -= 1
            self._update_avg_doc_length()
    
    def _update_avg_doc_length(self) -> None:
        """Update average document length."""
        if self.num_docs > 0:
            self.avg_doc_length = sum(self.doc_lengths.values()) / self.num_docs
        else:
            self.avg_doc_length = 0.0


class CategoryRetriever:
    """Fast category candidate retrieval using dual indexes.
    
    Stage A of the two-stage classification system.
    Retrieves top-K candidates in < 50ms using:
    1. Vector index (semantic matching)
    2. Keyword index (lexical matching)
    """
    
    def __init__(self, profile_store: CategoryProfileStore):
        """Initialize retriever.
        
        Args:
            profile_store: Category profile storage
        """
        self.profile_store = profile_store
        self.vector_index = VectorIndex()
        self.keyword_index = KeywordIndex()
        
        # Build indexes from existing profiles
        self._build_indexes()
        
        logger.info(f"Initialized CategoryRetriever with {len(profile_store.profiles)} profiles")
    
    def _build_indexes(self) -> None:
        """Build indexes from existing profiles."""
        for profile in self.profile_store.get_all():
            self.add_profile(profile)
        
        logger.info("Built indexes for category retrieval")
    
    def add_profile(self, profile: CategoryProfile) -> None:
        """Add profile to indexes.
        
        Args:
            profile: Category profile to add
        """
        # Add to vector index
        self.vector_index.add(profile.id, profile.centroid_embedding)
        
        # Add to keyword index
        self.keyword_index.add(profile.id, profile.keywords, profile.keyword_scores)
    
    def remove_profile(self, profile_id: str) -> None:
        """Remove profile from indexes.
        
        Args:
            profile_id: Profile to remove
        """
        self.vector_index.remove(profile_id)
        self.keyword_index.remove(profile_id)
    
    def update_profile(self, profile: CategoryProfile) -> None:
        """Update profile in indexes.
        
        Args:
            profile: Updated profile
        """
        # Remove old version
        self.remove_profile(profile.id)
        
        # Add new version
        self.add_profile(profile)
    
    def retrieve_candidates(
        self,
        card_content: str,
        card_embedding: np.ndarray,
        card_keywords: List[str],
        top_k: int = 10,
        alpha: float = 0.6
    ) -> List[Tuple[CategoryProfile, float]]:
        """Retrieve top-K candidate categories using hybrid retrieval.
        
        Args:
            card_content: Card content text
            card_embedding: Card embedding vector
            card_keywords: Extracted keywords from card
            top_k: Number of candidates to return
            alpha: Weight for semantic vs lexical (0.0 = all lexical, 1.0 = all semantic)
            
        Returns:
            List of (CategoryProfile, combined_score) tuples
        """
        # Stage A.1: Semantic search
        semantic_results = self.vector_index.search(card_embedding, top_k=20)
        
        # Stage A.2: Lexical search
        lexical_results = self.keyword_index.search(card_keywords, top_k=20)
        
        # Stage A.3: Combine scores
        combined_scores = self._combine_scores(
            semantic_results,
            lexical_results,
            alpha=alpha
        )
        
        # Get top-K profiles
        candidates = []
        for profile_id, score in combined_scores[:top_k]:
            profile = self.profile_store.get(profile_id)
            if profile:
                candidates.append((profile, score))
        
        logger.debug(f"Retrieved {len(candidates)} candidates for card")
        
        return candidates
    
    def _combine_scores(
        self,
        semantic_results: List[Tuple[str, float]],
        lexical_results: List[Tuple[str, float]],
        alpha: float = 0.6
    ) -> List[Tuple[str, float]]:
        """Combine semantic and lexical scores.
        
        Args:
            semantic_results: Results from vector search
            lexical_results: Results from keyword search
            alpha: Weight for semantic (1-alpha for lexical)
            
        Returns:
            Combined and sorted results
        """
        # Normalize scores to [0, 1]
        semantic_dict = self._normalize_scores(dict(semantic_results))
        lexical_dict = self._normalize_scores(dict(lexical_results))
        
        # Combine scores
        all_profile_ids = set(semantic_dict.keys()) | set(lexical_dict.keys())
        
        combined = []
        for profile_id in all_profile_ids:
            semantic_score = semantic_dict.get(profile_id, 0.0)
            lexical_score = lexical_dict.get(profile_id, 0.0)
            
            # Weighted combination
            combined_score = alpha * semantic_score + (1 - alpha) * lexical_score
            
            combined.append((profile_id, combined_score))
        
        # Sort by combined score descending
        combined.sort(key=lambda x: x[1], reverse=True)
        
        return combined
    
    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize scores to [0, 1] range.
        
        Args:
            scores: Dictionary of profile_id → score
            
        Returns:
            Normalized scores
        """
        if not scores:
            return {}
        
        min_score = min(scores.values())
        max_score = max(scores.values())
        
        if max_score == min_score:
            return {k: 1.0 for k in scores.keys()}
        
        return {
            k: (v - min_score) / (max_score - min_score)
            for k, v in scores.items()
        }
    
    def get_statistics(self) -> Dict:
        """Get retriever statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'vector_index_size': len(self.vector_index.embeddings),
            'keyword_index_terms': len(self.keyword_index.index),
            'avg_doc_length': round(self.keyword_index.avg_doc_length, 1),
        }
