"""Category Taxonomy Management.

Hierarchical category system for organizing cards.
Provides category suggestions and relationship management.
"""

import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class CategoryTaxonomy:
    """Hierarchical category management system.
    
    Maintains a tree structure of categories and tracks
    which cards belong to each category.
    
    Example hierarchy:
    - Technology
      - Programming
        - Python
        - JavaScript
      - AI/ML
        - Machine Learning
        - Deep Learning
    - Business
      - Marketing
      - Finance
    """
    
    def __init__(self):
        """Initialize category taxonomy with default categories."""
        self.tree = self._build_default_taxonomy()
        self.card_categories = {}  # card_id → category_path
        self.category_cards = {}  # category → set of card_ids
        
        logger.info("Initialized CategoryTaxonomy")
    
    def _build_default_taxonomy(self) -> Dict:
        """Build default category hierarchy.
        
        Returns:
            Nested dictionary representing category tree
        """
        return {
            'Technology': {
                'Programming': {
                    'Python': {},
                    'JavaScript': {},
                    'Java': {},
                    'C++': {},
                    'Go': {},
                    'Rust': {},
                },
                'AI/ML': {
                    'Machine Learning': {},
                    'Deep Learning': {},
                    'NLP': {},
                    'Computer Vision': {},
                },
                'Web Development': {
                    'Frontend': {},
                    'Backend': {},
                    'Full Stack': {},
                },
                'DevOps': {
                    'CI/CD': {},
                    'Containers': {},
                    'Cloud': {},
                },
            },
            'Business': {
                'Marketing': {},
                'Finance': {},
                'Sales': {},
                'Management': {},
            },
            'Science': {
                'Mathematics': {},
                'Physics': {},
                'Biology': {},
                'Chemistry': {},
            },
            'Design': {
                'UI/UX': {},
                'Graphic Design': {},
                '3D Modeling': {},
            },
            'Education': {
                'Tutorial': {},
                'Course': {},
                'Documentation': {},
                'Reference': {},
            },
            'Research': {
                'Academic Paper': {},
                'Case Study': {},
                'Experiment': {},
            },
        }
    
    def add_card(self, card_id: str, category: str) -> None:
        """Add a card to a category.
        
        Args:
            card_id: Card identifier
            category: Category name (can be path like "Technology/Programming/Python")
        """
        # Store card's category
        self.card_categories[card_id] = category
        
        # Add card to category's card set
        if category not in self.category_cards:
            self.category_cards[category] = set()
        self.category_cards[category].add(card_id)
        
        # Ensure category exists in tree
        self._ensure_category_exists(category)
        
        logger.debug(f"Added card {card_id} to category '{category}'")
    
    def remove_card(self, card_id: str) -> None:
        """Remove a card from its category.
        
        Args:
            card_id: Card identifier
        """
        if card_id in self.card_categories:
            category = self.card_categories[card_id]
            
            # Remove from category's card set
            if category in self.category_cards:
                self.category_cards[category].discard(card_id)
            
            # Remove from card_categories
            del self.card_categories[card_id]
            
            logger.debug(f"Removed card {card_id} from category '{category}'")
    
    def update_card_category(self, card_id: str, new_category: str) -> None:
        """Update a card's category.
        
        Args:
            card_id: Card identifier
            new_category: New category name
        """
        # Remove from old category
        self.remove_card(card_id)
        
        # Add to new category
        self.add_card(card_id, new_category)
        
        logger.debug(f"Updated card {card_id} category to '{new_category}'")
    
    def get_card_category(self, card_id: str) -> Optional[str]:
        """Get a card's category.
        
        Args:
            card_id: Card identifier
            
        Returns:
            Category name or None if not categorized
        """
        return self.card_categories.get(card_id)
    
    def get_cards_in_category(self, category: str) -> Set[str]:
        """Get all cards in a category.
        
        Args:
            category: Category name
            
        Returns:
            Set of card IDs
        """
        return self.category_cards.get(category, set())
    
    def suggest_category(self, content: str, title: str = "") -> str:
        """Suggest a category based on content and title.
        
        Uses keyword matching to suggest the most appropriate category.
        
        Args:
            content: Card content
            title: Card title
            
        Returns:
            Suggested category name
        """
        text = f"{title} {content}".lower()
        
        # Category keywords for matching
        category_keywords = {
            'Technology/Programming/Python': ['python', 'django', 'flask', 'pandas', 'numpy'],
            'Technology/Programming/JavaScript': ['javascript', 'js', 'react', 'vue', 'node', 'npm'],
            'Technology/Programming/Java': ['java', 'spring', 'maven', 'gradle'],
            'Technology/AI/ML/Machine Learning': ['machine learning', 'ml', 'scikit', 'model', 'training'],
            'Technology/AI/ML/Deep Learning': ['deep learning', 'neural network', 'tensorflow', 'pytorch', 'keras'],
            'Technology/AI/ML/NLP': ['nlp', 'natural language', 'text processing', 'tokenization'],
            'Technology/Web Development/Frontend': ['frontend', 'html', 'css', 'ui', 'component'],
            'Technology/Web Development/Backend': ['backend', 'api', 'server', 'database', 'rest'],
            'Technology/DevOps/CI/CD': ['ci/cd', 'pipeline', 'deployment', 'jenkins', 'github actions'],
            'Technology/DevOps/Containers': ['docker', 'kubernetes', 'container', 'k8s'],
            'Technology/DevOps/Cloud': ['aws', 'azure', 'gcp', 'cloud', 's3', 'lambda'],
            'Business/Marketing': ['marketing', 'seo', 'campaign', 'advertising'],
            'Business/Finance': ['finance', 'accounting', 'budget', 'revenue'],
            'Science/Mathematics': ['math', 'equation', 'theorem', 'proof', 'calculus'],
            'Design/UI/UX': ['ui', 'ux', 'user experience', 'interface', 'usability'],
            'Education/Tutorial': ['tutorial', 'how to', 'guide', 'step by step'],
            'Education/Documentation': ['documentation', 'docs', 'reference', 'api docs'],
            'Research/Academic Paper': ['paper', 'research', 'study', 'journal', 'abstract'],
        }
        
        # Score each category
        scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[category] = score
        
        # Return category with highest score
        if scores:
            best_category = max(scores, key=scores.get)
            logger.debug(f"Suggested category '{best_category}' with score {scores[best_category]}")
            return best_category
        
        # Default to general category
        logger.debug("No specific category match, using default 'Education/Reference'")
        return 'Education/Reference'
    
    def get_related_categories(self, category: str) -> List[str]:
        """Get sibling and parent categories.
        
        Args:
            category: Category name (can be path)
            
        Returns:
            List of related category names
        """
        related = []
        
        # Parse category path
        parts = category.split('/')
        
        # Add parent category
        if len(parts) > 1:
            parent = '/'.join(parts[:-1])
            related.append(parent)
        
        # Add sibling categories
        siblings = self._get_siblings(category)
        related.extend(siblings)
        
        return related
    
    def get_category_hierarchy(self) -> Dict:
        """Get the complete category hierarchy.
        
        Returns:
            Nested dictionary representing category tree
        """
        return self.tree
    
    def get_all_categories(self) -> List[str]:
        """Get all category paths as flat list.
        
        Returns:
            List of category path strings
        """
        categories = []
        self._flatten_tree(self.tree, "", categories)
        return categories
    
    def _ensure_category_exists(self, category: str) -> None:
        """Ensure a category path exists in the tree.
        
        Args:
            category: Category path (e.g., "Technology/Programming/Python")
        """
        parts = category.split('/')
        current = self.tree
        
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]
    
    def _get_siblings(self, category: str) -> List[str]:
        """Get sibling categories (same parent).
        
        Args:
            category: Category path
            
        Returns:
            List of sibling category paths
        """
        parts = category.split('/')
        if len(parts) < 2:
            # Top-level category, return other top-level categories
            return [cat for cat in self.tree.keys() if cat != parts[0]]
        
        # Navigate to parent
        parent_parts = parts[:-1]
        current = self.tree
        for part in parent_parts:
            if part in current:
                current = current[part]
            else:
                return []
        
        # Get siblings
        parent_path = '/'.join(parent_parts)
        siblings = []
        for sibling in current.keys():
            if sibling != parts[-1]:
                siblings.append(f"{parent_path}/{sibling}")
        
        return siblings
    
    def _flatten_tree(self, tree: Dict, prefix: str, result: List[str]) -> None:
        """Recursively flatten category tree into list of paths.
        
        Args:
            tree: Category tree (nested dict)
            prefix: Current path prefix
            result: List to append paths to
        """
        for key, subtree in tree.items():
            path = f"{prefix}/{key}" if prefix else key
            result.append(path)
            if subtree:
                self._flatten_tree(subtree, path, result)
