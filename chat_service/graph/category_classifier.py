"""Category Classifier - Stage B: LLM Reasoning.

Uses LLM to reason over shortlisted category profiles and decide:
1. Best matching category
2. Whether to create a new category
3. Hierarchy relationships (parent/siblings)
4. Confidence score
"""

import logging
from typing import Dict, List, Optional, Tuple
import json

from .category_profile import CategoryProfile, CategoryProfileStore
from .category_retriever import CategoryRetriever

logger = logging.getLogger(__name__)


class CategoryClassifier:
    """LLM-based category classification.
    
    Stage B of the two-stage classification system.
    Reasons over shortlisted profiles to make final decision.
    """
    
    def __init__(
        self,
        profile_store: CategoryProfileStore,
        retriever: CategoryRetriever,
        model=None
    ):
        """Initialize classifier.
        
        Args:
            profile_store: Category profile storage
            retriever: Category retriever for Stage A
            model: LLM model for reasoning (from model_provider)
        """
        self.profile_store = profile_store
        self.retriever = retriever
        self.model = model
        
        logger.info("Initialized CategoryClassifier")
    
    def classify(
        self,
        card_content: str,
        card_title: str,
        card_embedding,
        card_keywords: List[str],
        top_k_candidates: int = 10
    ) -> Dict:
        """Classify card into category using two-stage process.
        
        Args:
            card_content: Card content text
            card_title: Card title
            card_embedding: Card embedding vector
            card_keywords: Extracted keywords
            top_k_candidates: Number of candidates to retrieve
            
        Returns:
            Classification result:
            {
                "action": "match" | "create_new" | "uncategorized",
                "category_id": str (if match),
                "category_name": str,
                "new_category": dict (if create_new),
                "confidence": float,
                "reasoning": str,
                "candidates_considered": int
            }
        """
        logger.info(f"Classifying card: {card_title[:50]}...")
        
        # Stage A: Fast retrieval
        candidates = self.retriever.retrieve_candidates(
            card_content=card_content,
            card_embedding=card_embedding,
            card_keywords=card_keywords,
            top_k=top_k_candidates
        )
        
        if not candidates:
            logger.info("No candidates found, assigning to uncategorized")
            return {
                "action": "uncategorized",
                "category_id": None,
                "category_name": "Uncategorized",
                "confidence": 0.0,
                "reasoning": "No existing categories to match against",
                "candidates_considered": 0
            }
        
        # Stage B: LLM reasoning
        result = self._classify_with_llm(
            card_content=card_content,
            card_title=card_title,
            card_keywords=card_keywords,
            candidates=candidates
        )
        
        result["candidates_considered"] = len(candidates)
        
        logger.info(f"Classification result: {result['action']} - {result.get('category_name', 'N/A')}")
        
        return result
    
    def _classify_with_llm(
        self,
        card_content: str,
        card_title: str,
        card_keywords: List[str],
        candidates: List[Tuple[CategoryProfile, float]]
    ) -> Dict:
        """Use LLM to reason over candidates and make decision.
        
        Args:
            card_content: Card content
            card_title: Card title
            card_keywords: Card keywords
            candidates: List of (CategoryProfile, score) tuples
            
        Returns:
            Classification decision
        """
        # Build compact prompt
        prompt = self._build_classification_prompt(
            card_content=card_content,
            card_title=card_title,
            card_keywords=card_keywords,
            candidates=candidates
        )
        
        # Call LLM
        if self.model is None:
            # Fallback: use highest scoring candidate
            logger.warning("No LLM model provided, using fallback (highest score)")
            return self._fallback_classification(candidates)
        
        try:
            response = self.model.generate(
                prompt,
                response_format="json",
                max_tokens=500
            )
            
            result = json.loads(response)
            
            # Validate result
            if not self._validate_result(result):
                logger.warning("Invalid LLM response, using fallback")
                return self._fallback_classification(candidates)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            return self._fallback_classification(candidates)
    
    def _build_classification_prompt(
        self,
        card_content: str,
        card_title: str,
        card_keywords: List[str],
        candidates: List[Tuple[CategoryProfile, float]]
    ) -> str:
        """Build compact prompt for LLM.
        
        Args:
            card_content: Card content
            card_title: Card title
            card_keywords: Card keywords
            candidates: Candidate profiles with scores
            
        Returns:
            Formatted prompt string
        """
        # Format candidates compactly
        candidates_text = self._format_candidates(candidates)
        
        prompt = f"""You are a category classification system. Analyze the card and decide the best action.

## New Card
**Title:** {card_title}
**Content:** {card_content[:500]}{"..." if len(card_content) > 500 else ""}
**Keywords:** {", ".join(card_keywords[:15])}

## Candidate Categories (Top {len(candidates)})
{candidates_text}

## Instructions
Decide the best action:
1. **match** - If a candidate is a good fit (similarity > 0.6)
2. **create_new** - If no good match and this represents a distinct new category
3. **uncategorized** - If uncertain or too generic

## Response Format (JSON)
{{
    "action": "match" | "create_new" | "uncategorized",
    "category_id": "cat_xxx" (if match),
    "category_name": "Category Name",
    "new_category": {{
        "name": "New Category Name",
        "description": "One sentence description",
        "keywords": ["keyword1", "keyword2", ...],
        "parent_id": "cat_xxx" (optional)
    }} (if create_new),
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of decision"
}}

**Important:**
- Only create new categories for distinct, well-defined topics
- Prefer matching to existing categories when reasonable
- Be conservative with new category creation
"""
        
        return prompt
    
    def _format_candidates(
        self,
        candidates: List[Tuple[CategoryProfile, float]]
    ) -> str:
        """Format candidates compactly for prompt.
        
        Args:
            candidates: List of (profile, score) tuples
            
        Returns:
            Formatted string
        """
        lines = []
        
        for i, (profile, score) in enumerate(candidates, 1):
            compact = profile.to_compact_dict()
            
            lines.append(f"{i}. **{compact['name']}** (score: {score:.2f}, confidence: {compact['confidence']})")
            lines.append(f"   ID: {profile.id}")
            lines.append(f"   Description: {compact['description']}")
            lines.append(f"   Keywords: {', '.join(compact['keywords'][:8])}")
            
            if compact['snippets']:
                lines.append(f"   Examples: {'; '.join(compact['snippets'][:2])}")
            
            lines.append(f"   Cards: {compact['card_count']}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _fallback_classification(
        self,
        candidates: List[Tuple[CategoryProfile, float]]
    ) -> Dict:
        """Fallback classification when LLM unavailable.
        
        Uses simple heuristic: match to highest scoring candidate if score > threshold.
        
        Args:
            candidates: List of (profile, score) tuples
            
        Returns:
            Classification result
        """
        if not candidates:
            return {
                "action": "uncategorized",
                "category_id": None,
                "category_name": "Uncategorized",
                "confidence": 0.0,
                "reasoning": "No candidates available"
            }
        
        best_profile, best_score = candidates[0]
        
        # Threshold for matching
        MATCH_THRESHOLD = 0.6
        
        if best_score >= MATCH_THRESHOLD:
            return {
                "action": "match",
                "category_id": best_profile.id,
                "category_name": best_profile.name,
                "confidence": best_score,
                "reasoning": f"Matched to highest scoring candidate (score: {best_score:.2f})"
            }
        else:
            return {
                "action": "uncategorized",
                "category_id": None,
                "category_name": "Uncategorized",
                "confidence": 0.0,
                "reasoning": f"Best match score ({best_score:.2f}) below threshold ({MATCH_THRESHOLD})"
            }
    
    def _validate_result(self, result: Dict) -> bool:
        """Validate LLM response format.
        
        Args:
            result: LLM response dict
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["action", "confidence", "reasoning"]
        
        # Check required fields
        for field in required_fields:
            if field not in result:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate action
        valid_actions = ["match", "create_new", "uncategorized"]
        if result["action"] not in valid_actions:
            logger.warning(f"Invalid action: {result['action']}")
            return False
        
        # Validate action-specific fields
        if result["action"] == "match":
            if "category_id" not in result:
                logger.warning("Match action missing category_id")
                return False
        
        if result["action"] == "create_new":
            if "new_category" not in result:
                logger.warning("Create_new action missing new_category")
                return False
            
            required_new_cat_fields = ["name", "description", "keywords"]
            for field in required_new_cat_fields:
                if field not in result["new_category"]:
                    logger.warning(f"New category missing field: {field}")
                    return False
        
        return True
    
    def should_create_category(
        self,
        card_content: str,
        card_embedding,
        min_similar_cards: int = 3,
        similarity_threshold: float = 0.7
    ) -> Tuple[bool, List[str]]:
        """Decide if we should create a new category.
        
        Checks if there are enough similar "orphan" cards (uncategorized)
        to justify creating a new category.
        
        Args:
            card_content: Card content
            card_embedding: Card embedding
            min_similar_cards: Minimum similar cards needed
            similarity_threshold: Similarity threshold for "similar"
            
        Returns:
            (should_create, similar_card_ids)
        """
        # TODO: Implement orphan card detection
        # For now, return False (conservative approach)
        return False, []
