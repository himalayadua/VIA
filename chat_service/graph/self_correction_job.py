"""Self-Correction Background Job.

Periodic background job that improves the knowledge graph quality.
Detects issues and applies corrections automatically.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

from .knowledge_graph_state import KnowledgeGraphState

logger = logging.getLogger(__name__)


class SelfCorrectionJob:
    """Periodic background job for graph self-correction.
    
    Runs every N minutes/hours to:
    1. Detect graph issues
    2. Use LLM to suggest corrections (optional)
    3. Apply corrections with history tracking
    """
    
    def __init__(self, kg_state: KnowledgeGraphState, category_system=None):
        """Initialize self-correction job.
        
        Args:
            kg_state: Knowledge graph state instance
            category_system: Dynamic category system instance (optional)
        """
        self.kg_state = kg_state
        self.category_system = category_system
        self.correction_history = []
        
        logger.info("Initialized SelfCorrectionJob")
    
    def run(self) -> Dict[str, Any]:
        """Execute self-correction cycle.
        
        Returns:
            Dictionary with correction results
        """
        logger.info("Starting self-correction cycle")
        start_time = datetime.now()
        
        # 1. Detection Phase
        issues = self._detect_issues()
        
        # 2. Correction Phase
        corrections = self._generate_corrections(issues)
        
        # 3. Update Phase
        applied = self._apply_corrections(corrections)
        
        # Save graph after corrections
        self.kg_state.save()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration,
            'issues_detected': {
                'orphaned_cards': len(issues['orphaned_cards']),
                'weak_connections': len(issues['weak_connections']),
                'missing_categories': len(issues['missing_categories']),
                'duplicate_content': len(issues['duplicate_content']),
            },
            'corrections_applied': applied,
        }
        
        self.correction_history.append(result)
        
        logger.info(f"Self-correction cycle completed in {duration:.2f}s: "
                   f"{applied} corrections applied")
        
        return result
    
    def _detect_issues(self) -> Dict[str, List]:
        """Detect graph quality issues.
        
        Returns:
            Dictionary with different types of issues
        """
        logger.info("Detecting graph quality issues")
        
        # Get issues from knowledge graph
        issues = self.kg_state.detect_issues()
        
        # Add missing categories
        issues['missing_categories'] = []
        all_nodes = self.kg_state.backend.get_all_nodes()
        for node_id in all_nodes:
            node = self.kg_state.backend.get_node(node_id)
            if not node or not node.get('category'):
                issues['missing_categories'].append(node_id)
        
        logger.info(f"Detected {len(issues['orphaned_cards'])} orphaned cards, "
                   f"{len(issues['weak_connections'])} weak connections, "
                   f"{len(issues['missing_categories'])} missing categories, "
                   f"{len(issues['duplicate_content'])} potential duplicates")
        
        return issues
    
    def _generate_corrections(self, issues: Dict[str, List]) -> List[Dict]:
        """Generate corrections for detected issues.
        
        Args:
            issues: Dictionary of detected issues
            
        Returns:
            List of correction actions
        """
        logger.info("Generating corrections")
        corrections = []
        
        # 1. Fix orphaned cards - find parents
        for card_id in issues['orphaned_cards'][:10]:  # Limit to 10 per run
            try:
                node = self.kg_state.backend.get_node(card_id)
                if not node:
                    continue
                
                # Find similar cards
                similar = self.kg_state.backend.find_similar_nodes(
                    card_id, limit=5, min_similarity=0.3
                )
                
                if similar:
                    # Suggest parent (most similar)
                    parent_id, similarity = similar[0]
                    corrections.append({
                        'type': 'add_parent',
                        'card_id': card_id,
                        'parent_id': parent_id,
                        'similarity': similarity,
                        'reason': 'Orphaned card - found similar parent'
                    })
            except Exception as e:
                logger.error(f"Error generating correction for orphaned card {card_id}: {e}")
        
        # 2. Remove weak connections
        for source_id, target_id, similarity in issues['weak_connections'][:20]:
            corrections.append({
                'type': 'remove_weak_connection',
                'source_id': source_id,
                'target_id': target_id,
                'similarity': similarity,
                'reason': f'Weak connection (similarity: {similarity:.2f})'
            })
        
        # 3. Add missing categories
        for card_id in issues['missing_categories'][:20]:
            try:
                node = self.kg_state.backend.get_node(card_id)
                if not node:
                    continue
                
                content = node.get('content', '')
                title = node.get('title', '')
                
                # Suggest category using dynamic system if available
                if self.category_system:
                    try:
                        category = self.category_system.suggest_category(content, title)
                        corrections.append({
                            'type': 'add_category',
                            'card_id': card_id,
                            'category': category,
                            'reason': 'Missing category - auto-categorized with dynamic system'
                        })
                    except Exception as e:
                        logger.error(f"Error in dynamic categorization: {e}")
                        corrections.append({
                            'type': 'add_category',
                            'card_id': card_id,
                            'category': 'Uncategorized',
                            'reason': 'Missing category - fallback due to error'
                        })
                else:
                    corrections.append({
                        'type': 'add_category',
                        'card_id': card_id,
                        'category': 'Uncategorized',
                        'reason': 'Missing category - no category system available'
                    })
            except Exception as e:
                logger.error(f"Error generating correction for uncategorized card {card_id}: {e}")
        
        # 4. Flag duplicates (don't auto-merge, just flag)
        for card1_id, card2_id, similarity in issues['duplicate_content'][:10]:
            corrections.append({
                'type': 'flag_duplicate',
                'card1_id': card1_id,
                'card2_id': card2_id,
                'similarity': similarity,
                'reason': f'Potential duplicate (similarity: {similarity:.2f})'
            })
        
        logger.info(f"Generated {len(corrections)} corrections")
        return corrections
    
    def _apply_corrections(self, corrections: List[Dict]) -> int:
        """Apply corrections to the graph.
        
        Args:
            corrections: List of correction actions
            
        Returns:
            Number of corrections successfully applied
        """
        logger.info(f"Applying {len(corrections)} corrections")
        applied = 0
        
        for correction in corrections:
            try:
                correction_type = correction['type']
                
                if correction_type == 'add_parent':
                    # Add parent-child edge
                    self.kg_state.backend.add_edge(
                        source_id=correction['parent_id'],
                        target_id=correction['card_id'],
                        edge_type='parent-child',
                        similarity_score=correction['similarity'],
                        auto_corrected=True,
                        correction_reason=correction['reason']
                    )
                    applied += 1
                    logger.debug(f"Added parent {correction['parent_id']} to {correction['card_id']}")
                
                elif correction_type == 'remove_weak_connection':
                    # Remove weak edge
                    self.kg_state.backend.remove_edge(
                        source_id=correction['source_id'],
                        target_id=correction['target_id'],
                        edge_type='similar'
                    )
                    applied += 1
                    logger.debug(f"Removed weak connection {correction['source_id']} → {correction['target_id']}")
                
                elif correction_type == 'add_category':
                    # Add category to node
                    self.kg_state.backend.update_node(
                        node_id=correction['card_id'],
                        category=correction['category'],
                        auto_categorized=True
                    )
                    
                    # Update category system if available
                    if self.category_system:
                        try:
                            node = self.kg_state.backend.get_node(correction['card_id'])
                            if node:
                                card_data = {
                                    'content': node.get('content', ''),
                                    'title': node.get('title', ''),
                                    'embedding': self.category_system.embedding_provider.get_embedding(node.get('content', '')),
                                    'keywords': self.category_system._extract_keywords(node.get('content', ''), node.get('title', ''))
                                }
                                
                                self.category_system.update_card_category(
                                    card_id=correction['card_id'],
                                    new_category=correction['category'],
                                    card_data=card_data,
                                    is_user_correction=False
                                )
                        except Exception as e:
                            logger.error(f"Error updating category system: {e}")
                    
                    applied += 1
                    logger.debug(f"Added category '{correction['category']}' to {correction['card_id']}")
                
                elif correction_type == 'flag_duplicate':
                    # Add duplicate flag (don't auto-merge)
                    self.kg_state.backend.update_node(
                        node_id=correction['card1_id'],
                        potential_duplicate_of=correction['card2_id'],
                        duplicate_similarity=correction['similarity']
                    )
                    applied += 1
                    logger.debug(f"Flagged {correction['card1_id']} as potential duplicate of {correction['card2_id']}")
                
            except Exception as e:
                logger.error(f"Error applying correction {correction}: {e}")
                continue
        
        logger.info(f"Applied {applied}/{len(corrections)} corrections")
        return applied
    
    def get_correction_history(self, limit: int = 10) -> List[Dict]:
        """Get recent correction history.
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            List of correction result dicts
        """
        return self.correction_history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get self-correction statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_corrections = sum(
            result['corrections_applied'] 
            for result in self.correction_history
        )
        
        return {
            'total_runs': len(self.correction_history),
            'total_corrections': total_corrections,
            'last_run': self.correction_history[-1] if self.correction_history else None,
        }
