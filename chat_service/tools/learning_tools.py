"""
Learning Tools

Tools for the Learning Assistant Agent to provide educational features.
These tools are USER-TRIGGERED (not automatic) and help users learn and understand content.

Phase 1 Tools (Core Learning):
- simplify_explanation: ELI5 simplification with analogies
- find_real_examples: Real-world applications and use cases
- analyze_knowledge_gaps: Find missing prerequisites/advanced topics
- create_action_plan: Convert knowledge to implementation steps
- talk_to_canvas: Conversational knowledge queries

Phase 2 Tools (Research & Critical Thinking):
- find_academic_sources: Academic papers and research (hybrid LLM + arXiv search)
- find_counterpoints: Counter-arguments and alternative perspectives
- update_information: Refresh outdated content with recent developments
"""

import logging
import json
from typing import Dict, List, Optional
from strands import tool

# Import canvas API helpers
from tools.canvas_api import (
    create_card,
    get_card,
    get_canvas_cards,
    create_connection,
    calculate_child_position
)

# Import prompts
from prompts import PromptTemplates

logger = logging.getLogger(__name__)


# ============================================================================
# PHASE 1: CORE LEARNING TOOLS
# ============================================================================

@tool
def simplify_explanation(
    card_id: str,
    canvas_id: str,
    create_card_option: bool = False
) -> dict:
    """
    Simplify complex content into easy-to-understand explanations (ELI5).
    
    Uses LLM to create simplified versions with:
    - Analogies and metaphors
    - Removal of jargon
    - Everyday examples
    - Visual metaphors
    
    Args:
        card_id: Card to simplify
        canvas_id: Canvas ID
        create_card_option: If True, creates a simplified card; if False, returns preview
        
    Returns:
        {
            "success": bool,
            "original_content": str,
            "simplified_content": str,
            "simplified_card_id": str | None,
            "preview": bool
        }
    """
    logger.info(f"Simplifying card {card_id}")
    
    try:
        # Get card content
        card = get_card(card_id)
        if not card:
            return {
                "success": False,
                "error": "Card not found"
            }
        
        card_title = card.get("title", "")
        card_content = card.get("content", "")
        
        # Analyze canvas to determine user's knowledge level
        canvas_cards = get_canvas_cards(canvas_id)
        complexity_level = _analyze_canvas_complexity(canvas_cards)
        
        # Build prompt for simplification
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.simplify_explanation_prompt(
            title=card_title,
            content=card_content,
            complexity_level=complexity_level
        )
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        simplified_content = str(response).strip()
        
        # If create_card_option is False, return preview
        if not create_card_option:
            return {
                "success": True,
                "original_content": card_content,
                "simplified_content": simplified_content,
                "simplified_card_id": None,
                "preview": True,
                "message": "Preview generated. Set create_card_option=True to create a card."
            }
        
        # Create simplified card
        child_x, child_y = calculate_child_position(
            parent_x=card["position_x"],
            parent_y=card["position_y"],
            child_index=0,
            total_children=1,
            radius=280
        )
        
        simplified_card = create_card(
            canvas_id=canvas_id,
            title=f"📖 {card_title} (Simplified)",
            content=simplified_content,
            card_type="rich_text",
            position_x=child_x,
            position_y=child_y,
            parent_id=card_id,
            tags=["simplified", "eli5", complexity_level]
        )
        
        # Create connection
        create_connection(
            canvas_id=canvas_id,
            source_id=card_id,
            target_id=simplified_card["id"],
            connection_type="simplifies"
        )
        
        logger.info(f"Created simplified card: {simplified_card['id']}")
        
        return {
            "success": True,
            "original_content": card_content,
            "simplified_content": simplified_content,
            "simplified_card_id": simplified_card["id"],
            "preview": False,
            # Chat integration fields
            "cards": [{
                "id": simplified_card["id"],
                "title": f"📖 {card_title} (Simplified)",
                "type": "rich_text",
                "parent_id": card_id
            }],
            "summary": f"Created simplified explanation for '{card_title}'",
            "operation_type": "simplify"
        }
        
    except Exception as e:
        logger.error(f"Error simplifying explanation: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def _analyze_canvas_complexity(cards: List[Dict]) -> str:
    """Analyze canvas to determine user's knowledge level."""
    if not cards or len(cards) < 5:
        return "beginner"
    
    # Simple heuristic: count technical terms
    technical_keywords = ["algorithm", "implementation", "architecture", "framework", "protocol"]
    technical_count = sum(
        1 for card in cards
        for keyword in technical_keywords
        if keyword in card.get("content", "").lower()
    )
    
    if technical_count > len(cards) * 0.3:
        return "advanced"
    elif technical_count > len(cards) * 0.1:
        return "intermediate"
    else:
        return "beginner"


@tool
def find_real_examples(
    topic: str,
    card_id: str,
    canvas_id: str,
    create_card_option: bool = False
) -> dict:
    """
    Find real-world applications and use cases for a topic.
    
    Uses LLM to generate concrete examples of how abstract concepts
    are applied in industry, products, and real-world scenarios.
    
    Args:
        topic: Topic to find examples for
        card_id: Source card ID
        canvas_id: Canvas ID
        create_card_option: If True, creates example cards
        
    Returns:
        {
            "success": bool,
            "examples": list[dict],
            "example_card_ids": list[str],
            "preview": bool
        }
    """
    logger.info(f"Finding real examples for topic: {topic}")
    
    try:
        # Build prompt for example generation
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.find_examples_prompt(topic)
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # Parse JSON response
        try:
            from prompts import PromptFormatter
            examples = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(examples, list):
                raise ValueError("Response is not a JSON array")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "success": False,
                "error": "Failed to generate examples",
                "examples": []
            }
        
        # If create_card_option is False, return preview
        if not create_card_option:
            return {
                "success": True,
                "examples": examples,
                "example_card_ids": [],
                "preview": True,
                "message": f"Found {len(examples)} examples. Set create_card_option=True to create cards."
            }
        
        # Create example cards
        source_card = get_card(card_id)
        example_card_ids = []
        
        for i, example in enumerate(examples):
            # Calculate position
            child_x, child_y = calculate_child_position(
                parent_x=source_card["position_x"],
                parent_y=source_card["position_y"],
                child_index=i,
                total_children=len(examples),
                radius=300
            )
            
            # Create example card
            example_card = create_card(
                canvas_id=canvas_id,
                title=f"🌍 {example.get('name', 'Real-World Example')}",
                content=f"**Industry:** {example.get('industry', 'N/A')}\n\n{example.get('description', '')}\n\n**Impact:** {example.get('impact', 'N/A')}",
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                parent_id=card_id,
                tags=["example", "real-world", example.get("industry", "general").lower()]
            )
            
            example_card_ids.append(example_card["id"])
            
            # Create connection
            create_connection(
                canvas_id=canvas_id,
                source_id=card_id,
                target_id=example_card["id"],
                connection_type="exemplifies"
            )
        
        logger.info(f"Created {len(example_card_ids)} example cards")
        
        # Build cards array for chat display
        cards_for_chat = []
        for i, example in enumerate(examples):
            if i < len(example_card_ids):
                cards_for_chat.append({
                    "id": example_card_ids[i],
                    "title": f"🌍 {example.get('name', 'Real-World Example')}",
                    "type": "rich_text",
                    "parent_id": card_id
                })
        
        return {
            "success": True,
            "examples": examples,
            "example_card_ids": example_card_ids,
            "preview": False,
            # Chat integration fields
            "cards": cards_for_chat,
            "summary": f"Found {len(example_card_ids)} real-world examples for {topic}",
            "operation_type": "find_examples"
        }
        
    except Exception as e:
        logger.error(f"Error finding examples: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "examples": []
        }


@tool
def analyze_knowledge_gaps(
    card_ids: List[str],
    canvas_id: str,
    create_card_option: bool = False
) -> dict:
    """
    Analyze knowledge gaps - find missing prerequisites and advanced topics.
    
    Maps concept dependencies and identifies:
    - Missing prerequisites (what you need to know first)
    - Missing advanced topics (what to learn next)
    - Importance ratings for each gap
    
    Args:
        card_ids: List of card IDs to analyze
        canvas_id: Canvas ID
        create_card_option: If True, creates gap cards
        
    Returns:
        {
            "success": bool,
            "gaps": dict,  # {prerequisites: [], advanced: []}
            "gap_card_ids": list[str],
            "preview": bool
        }
    """
    logger.info(f"Analyzing knowledge gaps for {len(card_ids)} cards")
    
    try:
        # Get card contents
        cards_content = []
        for card_id in card_ids:
            card = get_card(card_id)
            if card:
                cards_content.append({
                    "id": card_id,
                    "title": card.get("title", ""),
                    "content": card.get("content", "")
                })
        
        if not cards_content:
            return {
                "success": False,
                "error": "No valid cards found"
            }
        
        # Build prompt for gap analysis
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.analyze_gaps_prompt(cards_content)
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # Parse JSON response
        try:
            from prompts import PromptFormatter
            gaps_data = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(gaps_data, dict):
                raise ValueError("Response is not a JSON object")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "success": False,
                "error": "Failed to analyze knowledge gaps",
                "gaps": {"prerequisites": [], "advanced": []}
            }
        
        gaps = {
            "prerequisites": gaps_data.get("prerequisites", []),
            "advanced": gaps_data.get("advanced", [])
        }
        
        # If create_card_option is False, return preview
        if not create_card_option:
            return {
                "success": True,
                "gaps": gaps,
                "gap_card_ids": [],
                "preview": True,
                "message": f"Found {len(gaps['prerequisites'])} prerequisites and {len(gaps['advanced'])} advanced topics. Set create_card_option=True to create cards."
            }
        
        # Create gap cards
        gap_card_ids = []
        all_gaps = gaps["prerequisites"] + gaps["advanced"]
        
        # Use first card as reference for positioning
        reference_card = get_card(card_ids[0])
        
        for i, gap in enumerate(all_gaps):
            # Calculate position
            child_x, child_y = calculate_child_position(
                parent_x=reference_card["position_x"],
                parent_y=reference_card["position_y"],
                child_index=i,
                total_children=len(all_gaps),
                radius=320
            )
            
            # Determine gap type and icon
            gap_type = "prerequisite" if gap in gaps["prerequisites"] else "advanced"
            icon = "🔍" if gap_type == "prerequisite" else "🎯"
            
            # Create gap card
            gap_card = create_card(
                canvas_id=canvas_id,
                title=f"{icon} {gap.get('topic', 'Knowledge Gap')}",
                content=f"**Type:** {gap_type.title()}\n**Importance:** {gap.get('importance', 'Medium')}\n\n{gap.get('description', '')}\n\n**Why Important:** {gap.get('reasoning', 'N/A')}",
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                tags=["gap", gap_type, gap.get("importance", "medium").lower()]
            )
            
            gap_card_ids.append(gap_card["id"])
            
            # Create connections to related cards
            for card_id in card_ids:
                create_connection(
                    canvas_id=canvas_id,
                    source_id=gap_card["id"],
                    target_id=card_id,
                    connection_type="prerequisite" if gap_type == "prerequisite" else "extends"
                )
        
        logger.info(f"Created {len(gap_card_ids)} gap cards")
        
        # Build cards array for chat display
        cards_for_chat = []
        for i, gap in enumerate(all_gaps):
            if i < len(gap_card_ids):
                gap_type = "prerequisite" if gap in gaps["prerequisites"] else "advanced"
                icon = "🔍" if gap_type == "prerequisite" else "🎯"
                cards_for_chat.append({
                    "id": gap_card_ids[i],
                    "title": f"{icon} {gap.get('topic', 'Knowledge Gap')}",
                    "type": "rich_text",
                    "parent_id": None
                })
        
        return {
            "success": True,
            "gaps": gaps,
            "gap_card_ids": gap_card_ids,
            "preview": False,
            # Chat integration fields
            "cards": cards_for_chat,
            "summary": f"Identified {len(gaps['prerequisites'])} prerequisites and {len(gaps['advanced'])} advanced topics",
            "operation_type": "find_gaps"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing knowledge gaps: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "gaps": {"prerequisites": [], "advanced": []}
        }


@tool
def create_action_plan(
    topic: str,
    card_ids: List[str],
    canvas_id: str,
    create_card_option: bool = False
) -> dict:
    """
    Convert knowledge to actionable implementation steps.
    
    Creates step-by-step implementation plan with:
    - Setup steps
    - Implementation steps
    - Code snippets/templates
    - Time and difficulty estimates
    
    Args:
        topic: Topic to create action plan for
        card_ids: Related knowledge card IDs
        canvas_id: Canvas ID
        create_card_option: If True, creates action plan cards
        
    Returns:
        {
            "success": bool,
            "action_plan": dict,
            "plan_card_ids": list[str],
            "preview": bool
        }
    """
    logger.info(f"Creating action plan for topic: {topic}")
    
    try:
        # Get knowledge context from cards
        knowledge_context = []
        for card_id in card_ids:
            card = get_card(card_id)
            if card:
                knowledge_context.append({
                    "title": card.get("title", ""),
                    "content": card.get("content", "")
                })
        
        # Build prompt for action plan
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.create_action_plan_prompt(topic, knowledge_context)
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # Parse JSON response
        try:
            from prompts import PromptFormatter
            action_plan = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(action_plan, dict):
                raise ValueError("Response is not a JSON object")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "success": False,
                "error": "Failed to create action plan",
                "action_plan": {}
            }
        
        # If create_card_option is False, return preview
        if not create_card_option:
            return {
                "success": True,
                "action_plan": action_plan,
                "plan_card_ids": [],
                "preview": True,
                "message": f"Generated action plan with {len(action_plan.get('steps', []))} steps. Set create_card_option=True to create cards."
            }
        
        # Create action plan cards
        plan_card_ids = []
        steps = action_plan.get("steps", [])
        
        # Use first card as reference for positioning
        reference_card = get_card(card_ids[0]) if card_ids else None
        if not reference_card:
            # Default position if no reference
            reference_card = {"position_x": 0, "position_y": 0}
        
        for i, step in enumerate(steps):
            # Calculate position
            child_x, child_y = calculate_child_position(
                parent_x=reference_card["position_x"],
                parent_y=reference_card["position_y"],
                child_index=i,
                total_children=len(steps),
                radius=350
            )
            
            # Format step content
            content = f"**Phase:** {step.get('phase', 'Implementation')}\n"
            content += f"**Difficulty:** {step.get('difficulty', 'Medium')}\n"
            content += f"**Estimated Time:** {step.get('estimated_time', 'Unknown')}\n\n"
            content += f"{step.get('description', '')}\n\n"
            
            if step.get("code_snippet"):
                content += f"**Code Example:**\n```\n{step['code_snippet']}\n```\n\n"
            
            if step.get("resources"):
                content += f"**Resources:**\n"
                for resource in step["resources"]:
                    content += f"- {resource}\n"
            
            # Create action step card
            step_card = create_card(
                canvas_id=canvas_id,
                title=f"✓ Step {i+1}: {step.get('title', 'Action Step')}",
                content=content,
                card_type="todo",
                position_x=child_x,
                position_y=child_y,
                tags=["action", "implementation", step.get("difficulty", "medium").lower()],
                card_data={
                    "items": [{"text": step.get("title", "Complete this step"), "completed": False}],
                    "progress": 0,
                    "priority": step.get("difficulty", "medium"),
                    "estimated_time": step.get("estimated_time", "")
                }
            )
            
            plan_card_ids.append(step_card["id"])
            
            # Create connections to knowledge cards
            for card_id in card_ids:
                create_connection(
                    canvas_id=canvas_id,
                    source_id=card_id,
                    target_id=step_card["id"],
                    connection_type="implements"
                )
        
        logger.info(f"Created {len(plan_card_ids)} action plan cards")
        
        # Build cards array for chat display
        cards_for_chat = []
        for i, step in enumerate(steps):
            if i < len(plan_card_ids):
                cards_for_chat.append({
                    "id": plan_card_ids[i],
                    "title": f"✓ Step {i+1}: {step.get('title', 'Action Step')}",
                    "type": "todo",
                    "parent_id": None
                })
        
        return {
            "success": True,
            "action_plan": action_plan,
            "plan_card_ids": plan_card_ids,
            "preview": False,
            # Chat integration fields
            "cards": cards_for_chat,
            "summary": f"Created action plan with {len(plan_card_ids)} implementation steps for {topic}",
            "operation_type": "action_plan"
        }
        
    except Exception as e:
        logger.error(f"Error creating action plan: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "action_plan": {}
        }



@tool
def talk_to_canvas(
    question: str,
    canvas_id: str,
    conversation_history: Optional[List[Dict]] = None
) -> dict:
    """
    Conversational knowledge queries with canvas context.
    
    Analyzes canvas to answer questions with:
    - Relevant card selection (max 20 cards)
    - Context-aware responses
    - Card references in answers
    - Personalized recommendations
    
    Args:
        question: User's question
        canvas_id: Canvas ID for context
        conversation_history: Previous conversation messages
        
    Returns:
        {
            "success": bool,
            "answer": str,
            "referenced_cards": list[dict],
            "recommendations": list[str],
            "conversation_id": str
        }
    """
    logger.info(f"Processing canvas conversation: {question[:50]}...")
    
    try:
        # Get all canvas cards
        all_cards = get_canvas_cards(canvas_id)
        
        if not all_cards:
            return {
                "success": True,
                "answer": "Your canvas appears to be empty. Add some cards first, then I can help answer questions about your knowledge!",
                "referenced_cards": [],
                "recommendations": ["Create some cards with your knowledge", "Try asking questions after adding content"]
            }
        
        # Find relevant cards (max 20)
        relevant_cards = _find_relevant_cards(question, all_cards, max_cards=20)
        
        # Build context from relevant cards
        context = _build_context_from_cards(relevant_cards)
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-3:]:  # Last 3 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation_context += f"{role}: {content}\n"
        
        # Build prompt for canvas conversation
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.talk_to_canvas_prompt(
            question=question,
            context=context,
            conversation_context=conversation_context,
            canvas_stats={
                "total_cards": len(all_cards),
                "relevant_cards": len(relevant_cards)
            }
        )
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        answer = str(response).strip()
        
        # Extract recommendations (simple heuristic)
        recommendations = _extract_recommendations(answer, all_cards)
        
        logger.info(f"Answered canvas question using {len(relevant_cards)} relevant cards")
        
        return {
            "success": True,
            "answer": answer,
            "referenced_cards": [{
                "id": card["id"],
                "title": card.get("title", "Untitled"),
                "relevance_score": card.get("_relevance_score", 0.0)
            } for card in relevant_cards],
            "recommendations": recommendations,
            "conversation_id": f"conv_{canvas_id}_{len(conversation_history or [])}"
        }
        
    except Exception as e:
        logger.error(f"Error in canvas conversation: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "answer": "I encountered an error while processing your question. Please try again."
        }


def _find_relevant_cards(question: str, cards: List[Dict], max_cards: int = 20) -> List[Dict]:
    """Find cards relevant to the question using keyword matching and TF-IDF."""
    try:
        # Simple keyword matching for now
        question_words = set(question.lower().split())
        
        scored_cards = []
        for card in cards:
            title = card.get("title", "").lower()
            content = card.get("content", "").lower()
            
            # Calculate relevance score
            title_matches = len(question_words.intersection(set(title.split())))
            content_matches = len(question_words.intersection(set(content.split())))
            
            relevance_score = title_matches * 2 + content_matches  # Title matches weighted higher
            
            if relevance_score > 0:
                card_copy = card.copy()
                card_copy["_relevance_score"] = relevance_score
                scored_cards.append(card_copy)
        
        # Sort by relevance and return top cards
        scored_cards.sort(key=lambda x: x["_relevance_score"], reverse=True)
        return scored_cards[:max_cards]
        
    except Exception as e:
        logger.error(f"Error finding relevant cards: {e}")
        return cards[:max_cards]  # Fallback to first N cards


def _build_context_from_cards(cards: List[Dict]) -> str:
    """Build context string from relevant cards."""
    context = "Relevant knowledge from your canvas:\n\n"
    
    for i, card in enumerate(cards[:10]):  # Limit to top 10 for context window
        title = card.get("title", f"Card {i+1}")
        content = card.get("content", "")[:200]  # Truncate long content
        
        context += f"**{title}:**\n{content}\n\n"
    
    return context


def _extract_recommendations(answer: str, cards: List[Dict]) -> List[str]:
    """Extract simple recommendations based on answer and canvas state."""
    recommendations = []
    
    # Simple heuristics
    if "learn more" in answer.lower():
        recommendations.append("Consider adding more detailed cards about this topic")
    
    if "example" in answer.lower():
        recommendations.append("Try using the 'Find Examples' tool for real-world applications")
    
    if "research" in answer.lower():
        recommendations.append("Use 'Find Academic Sources' to get research papers")
    
    if len(cards) < 5:
        recommendations.append("Your canvas is small - add more cards for richer conversations")
    
    return recommendations[:3]  # Max 3 recommendations


# ============================================================================
# PHASE 2: RESEARCH & CRITICAL THINKING TOOLS
# ============================================================================

@tool
def find_academic_sources(
    topic: str,
    card_id: str,
    canvas_id: str,
    create_card_option: bool = False,
    max_papers: int = 5
) -> dict:
    """
    Find academic papers and research sources using hybrid LLM + arXiv approach.
    
    Based on temp/arxiv implementation:
    1. LLM generates optimized search query
    2. Search arXiv with generated query
    3. LLM analyzes and ranks results
    4. Fallback to LLM-only if arXiv fails
    
    Args:
        topic: Research topic
        card_id: Source card ID
        canvas_id: Canvas ID
        create_card_option: If True, creates source cards
        max_papers: Maximum papers to return (default 5)
        
    Returns:
        {
            "success": bool,
            "papers": list[dict],
            "source_card_ids": list[str],
            "search_method": str,  # "arxiv" or "llm_fallback"
            "preview": bool
        }
    """
    logger.info(f"Finding academic sources for topic: {topic}")
    
    try:
        papers = []
        search_method = "llm_fallback"  # Default fallback
        
        # Try arXiv search first (hybrid approach)
        try:
            import arxiv
            
            # Step 1: LLM generates optimized search query
            from agents.model_provider import get_nvidia_nim_model
            model = get_nvidia_nim_model()
            
            query_prompt = PromptTemplates.suggest_arxiv_query_prompt(topic)
            query_response = model(query_prompt)
            
            # Parse query suggestion
            try:
                from prompts import PromptFormatter
                query_data = PromptFormatter.parse_json_response(str(query_response))
                search_query = query_data.get("query", topic)
                categories = query_data.get("categories", [])
            except:
                search_query = topic  # Fallback to original topic
                categories = []
            
            logger.info(f"Generated arXiv search query: {search_query}")
            
            # Step 2: Search arXiv
            client = arxiv.Client()
            search = arxiv.Search(
                query=search_query,
                max_results=max_papers * 2,  # Get more to filter
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            arxiv_papers = []
            for result in client.results(search):
                # Filter by categories if specified
                if categories and not any(cat in result.categories for cat in categories):
                    continue
                    
                arxiv_papers.append({
                    "title": result.title,
                    "authors": [a.name for a in result.authors],
                    "published": result.published.isoformat(),
                    "abstract": result.summary,
                    "pdf_url": result.pdf_url,
                    "categories": result.categories,
                    "source": "arXiv"
                })
                
                if len(arxiv_papers) >= max_papers:
                    break
            
            if arxiv_papers:
                # Step 3: LLM analyzes and ranks results
                ranking_prompt = PromptTemplates.rank_papers_prompt(topic, arxiv_papers)
                ranking_response = model(ranking_prompt)
                
                try:
                    ranked_data = PromptFormatter.parse_json_response(str(ranking_response))
                    papers = ranked_data.get("papers", arxiv_papers)[:max_papers]
                    search_method = "arxiv"
                    logger.info(f"Successfully found {len(papers)} papers via arXiv")
                except:
                    papers = arxiv_papers[:max_papers]  # Use unranked if ranking fails
                    search_method = "arxiv"
            
        except ImportError:
            logger.warning("arxiv library not installed, using LLM fallback")
        except Exception as e:
            logger.warning(f"arXiv search failed: {e}, using LLM fallback")
        
        # Fallback: LLM-only approach
        if not papers:
            logger.info("Using LLM fallback for academic sources")
            
            from agents.model_provider import get_nvidia_nim_model
            model = get_nvidia_nim_model()
            
            prompt = PromptTemplates.find_academic_sources_prompt(topic, max_papers)
            response = model(prompt)
            
            try:
                from prompts import PromptFormatter
                papers = PromptFormatter.parse_json_response(str(response))
                
                if not isinstance(papers, list):
                    raise ValueError("Response is not a JSON array")
                    
                # Add source field
                for paper in papers:
                    paper["source"] = "LLM Generated"
                    
                search_method = "llm_fallback"
                logger.info(f"Generated {len(papers)} papers via LLM fallback")
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse LLM response: {e}")
                return {
                    "success": False,
                    "error": "Failed to find academic sources",
                    "papers": []
                }
        
        # If create_card_option is False, return preview
        if not create_card_option:
            return {
                "success": True,
                "papers": papers,
                "source_card_ids": [],
                "search_method": search_method,
                "preview": True,
                "message": f"Found {len(papers)} papers via {search_method}. Set create_card_option=True to create cards."
            }
        
        # Create source cards
        source_card = get_card(card_id)
        source_card_ids = []
        
        for i, paper in enumerate(papers):
            # Calculate position
            child_x, child_y = calculate_child_position(
                parent_x=source_card["position_x"],
                parent_y=source_card["position_y"],
                child_index=i,
                total_children=len(papers),
                radius=350
            )
            
            # Format paper content
            authors_str = ", ".join(paper.get("authors", [])[:3])  # First 3 authors
            if len(paper.get("authors", [])) > 3:
                authors_str += " et al."
            
            content = f"**Authors:** {authors_str}\n"
            content += f"**Published:** {paper.get('published', 'N/A')}\n"
            content += f"**Source:** {paper.get('source', 'Unknown')}\n\n"
            content += f"**Abstract:**\n{paper.get('abstract', 'No abstract available')}"
            
            if paper.get("pdf_url"):
                content += f"\n\n**PDF:** {paper['pdf_url']}"
            
            # Create source card
            source_card_obj = create_card(
                canvas_id=canvas_id,
                title=f"📄 {paper.get('title', 'Academic Paper')}",
                content=content,
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                parent_id=card_id,
                tags=["academic", "research", "paper", search_method]
            )
            
            source_card_ids.append(source_card_obj["id"])
            
            # Create connection
            create_connection(
                canvas_id=canvas_id,
                source_id=card_id,
                target_id=source_card_obj["id"],
                connection_type="references"
            )
        
        logger.info(f"Created {len(source_card_ids)} source cards via {search_method}")
        
        # Build cards array for chat display
        cards_for_chat = []
        for i, paper in enumerate(papers):
            if i < len(source_card_ids):
                cards_for_chat.append({
                    "id": source_card_ids[i],
                    "title": f"📄 {paper.get('title', 'Academic Paper')}",
                    "type": "rich_text",
                    "parent_id": card_id
                })
        
        return {
            "success": True,
            "papers": papers,
            "source_card_ids": source_card_ids,
            "search_method": search_method,
            "preview": False,
            # Chat integration fields
            "cards": cards_for_chat,
            "summary": f"Found {len(source_card_ids)} academic sources via {search_method}",
            "operation_type": "go_deeper"
        }
        
    except Exception as e:
        logger.error(f"Error finding academic sources: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "papers": [],
            "search_method": "error"
        }



@tool
def find_counterpoints(
    card_id: str,
    canvas_id: str,
    create_card_option: bool = False
) -> dict:
    """
    Find counter-arguments and alternative perspectives.
    
    Analyzes card content to find:
    - Counter-arguments
    - Limitations and trade-offs
    - Alternative viewpoints
    - Evidence and reasoning
    
    Args:
        card_id: Card to find counterpoints for
        canvas_id: Canvas ID
        create_card_option: If True, creates counterpoint cards
        
    Returns:
        {
            "success": bool,
            "counterpoints": list[dict],
            "counterpoint_card_ids": list[str],
            "preview": bool
        }
    """
    logger.info(f"Finding counterpoints for card {card_id}")
    
    try:
        # Get card content
        card = get_card(card_id)
        if not card:
            return {
                "success": False,
                "error": "Card not found"
            }
        
        card_title = card.get("title", "")
        card_content = card.get("content", "")
        
        # Build prompt for counterpoint generation
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.find_counterpoints_prompt(
            title=card_title,
            content=card_content
        )
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # Parse JSON response
        try:
            from prompts import PromptFormatter
            counterpoints = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(counterpoints, list):
                raise ValueError("Response is not a JSON array")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "success": False,
                "error": "Failed to find counterpoints",
                "counterpoints": []
            }
        
        # If create_card_option is False, return preview
        if not create_card_option:
            return {
                "success": True,
                "counterpoints": counterpoints,
                "counterpoint_card_ids": [],
                "preview": True,
                "message": f"Found {len(counterpoints)} counterpoints. Set create_card_option=True to create cards."
            }
        
        # Create counterpoint cards
        counterpoint_card_ids = []
        
        for i, counterpoint in enumerate(counterpoints):
            # Calculate position
            child_x, child_y = calculate_child_position(
                parent_x=card["position_x"],
                parent_y=card["position_y"],
                child_index=i,
                total_children=len(counterpoints),
                radius=300
            )
            
            # Create counterpoint card
            counterpoint_card = create_card(
                canvas_id=canvas_id,
                title=f"⚖️ {counterpoint.get('title', 'Counterpoint')}",
                content=f"**Type:** {counterpoint.get('type', 'Counter-argument')}\n\n{counterpoint.get('argument', '')}\n\n**Evidence:** {counterpoint.get('evidence', 'N/A')}",
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                parent_id=card_id,
                tags=["counterpoint", "challenge", counterpoint.get("type", "argument").lower()]
            )
            
            counterpoint_card_ids.append(counterpoint_card["id"])
            
            # Create connection
            create_connection(
                canvas_id=canvas_id,
                source_id=counterpoint_card["id"],
                target_id=card_id,
                connection_type="challenges"
            )
        
        logger.info(f"Created {len(counterpoint_card_ids)} counterpoint cards")
        
        # Build cards array for chat display
        cards_for_chat = []
        for i, counterpoint in enumerate(counterpoints):
            if i < len(counterpoint_card_ids):
                cards_for_chat.append({
                    "id": counterpoint_card_ids[i],
                    "title": f"⚖️ {counterpoint.get('title', 'Counterpoint')}",
                    "type": "rich_text",
                    "parent_id": card_id
                })
        
        return {
            "success": True,
            "counterpoints": counterpoints,
            "counterpoint_card_ids": counterpoint_card_ids,
            "preview": False,
            # Chat integration fields
            "cards": cards_for_chat,
            "summary": f"Found {len(counterpoint_card_ids)} counterpoints and challenges",
            "operation_type": "challenge"
        }
        
    except Exception as e:
        logger.error(f"Error finding counterpoints: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "counterpoints": []
        }


@tool
def update_information(
    card_id: str,
    canvas_id: str,
    create_card_option: bool = False
) -> dict:
    """
    Refresh outdated content with recent developments.
    
    Analyzes card content and searches for:
    - Recent developments
    - New features or changes
    - Deprecated information
    - Updated best practices
    
    Args:
        card_id: Card to update
        canvas_id: Canvas ID
        create_card_option: If True, creates update card
        
    Returns:
        {
            "success": bool,
            "updates": dict,
            "update_card_id": str | None,
            "preview": bool
        }
    """
    logger.info(f"Updating information for card {card_id}")
    
    try:
        # Get card content
        card = get_card(card_id)
        if not card:
            return {
                "success": False,
                "error": "Card not found"
            }
        
        card_title = card.get("title", "")
        card_content = card.get("content", "")
        card_date = card.get("created_at", "")
        
        # Build prompt for update generation
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.update_information_prompt(
            title=card_title,
            content=card_content,
            date=card_date
        )
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # Parse JSON response
        try:
            from prompts import PromptFormatter
            updates = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(updates, dict):
                raise ValueError("Response is not a JSON object")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "success": False,
                "error": "Failed to generate updates",
                "updates": {}
            }
        
        # If create_card_option is False, return preview
        if not create_card_option:
            return {
                "success": True,
                "updates": updates,
                "update_card_id": None,
                "preview": True,
                "message": f"Found {len(updates.get('changes', []))} updates. Set create_card_option=True to create update card."
            }
        
        # Create update card
        child_x, child_y = calculate_child_position(
            parent_x=card["position_x"],
            parent_y=card["position_y"],
            child_index=0,
            total_children=1,
            radius=280
        )
        
        # Format update content
        content = f"**Last Updated:** {updates.get('update_date', 'Recent')}\n\n"
        
        if updates.get("changes"):
            content += "**Recent Changes:**\n"
            for change in updates["changes"]:
                content += f"• {change}\n"
            content += "\n"
        
        if updates.get("new_features"):
            content += "**New Features:**\n"
            for feature in updates["new_features"]:
                content += f"• {feature}\n"
            content += "\n"
        
        if updates.get("deprecated"):
            content += "**Deprecated:**\n"
            for deprecated in updates["deprecated"]:
                content += f"• {deprecated}\n"
            content += "\n"
        
        content += f"**Summary:** {updates.get('summary', 'Information has been updated.')}"
        
        # Create update card
        update_card = create_card(
            canvas_id=canvas_id,
            title=f"🔄 {card_title} (Updated)",
            content=content,
            card_type="rich_text",
            position_x=child_x,
            position_y=child_y,
            parent_id=card_id,
            tags=["update", "recent", "refresh"]
        )
        
        # Create connection
        create_connection(
            canvas_id=canvas_id,
            source_id=card_id,
            target_id=update_card["id"],
            connection_type="updates"
        )
        
        logger.info(f"Created update card: {update_card['id']}")
        
        return {
            "success": True,
            "updates": updates,
            "update_card_id": update_card["id"],
            "preview": False,
            # Chat integration fields
            "cards": [{
                "id": update_card["id"],
                "title": f"🔄 {card_title} (Updated)",
                "type": "rich_text",
                "parent_id": card_id
            }],
            "summary": f"Updated information for '{card_title}' with {len(updates.get('changes', []))} recent changes",
            "operation_type": "update"
        }
        
    except Exception as e:
        logger.error(f"Error updating information: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "updates": {}
        }



@tool
def find_surprising_connections(
    card_ids: List[str],
    canvas_id: str,
    create_card_option: bool = False
) -> dict:
    """
    Discover non-obvious connections between disparate topics.
    
    Analyzes multiple cards to find:
    - Shared mathematical principles
    - Analogies and metaphors
    - Interdisciplinary links
    - Historical parallels
    - Underlying common principles
    
    Args:
        card_ids: List of card IDs to analyze (minimum 2)
        canvas_id: Canvas ID
        create_card_option: If True, creates connection cards
        
    Returns:
        {
            "success": bool,
            "connections": list[dict],
            "connection_card_ids": list[str],
            "preview": bool
        }
    """
    logger.info(f"Finding surprising connections between {len(card_ids)} cards")
    
    try:
        # Validate input
        if len(card_ids) < 2:
            return {
                "success": False,
                "error": "Need at least 2 cards to find connections"
            }
        
        # Get card contents
        cards_content = []
        for card_id in card_ids:
            card = get_card(card_id)
            if card:
                cards_content.append({
                    "id": card_id,
                    "title": card.get("title", ""),
                    "content": card.get("content", "")
                })
        
        if len(cards_content) < 2:
            return {
                "success": False,
                "error": "Need at least 2 valid cards"
            }
        
        # Build prompt for connection finding
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.find_surprising_connections_prompt(cards_content)
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # Parse JSON response
        try:
            from prompts import PromptFormatter
            connections = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(connections, list):
                raise ValueError("Response is not a JSON array")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "success": False,
                "error": "Failed to find connections",
                "connections": []
            }
        
        # If create_card_option is False, return preview
        if not create_card_option:
            return {
                "success": True,
                "connections": connections,
                "connection_card_ids": [],
                "preview": True,
                "message": f"Found {len(connections)} surprising connections. Set create_card_option=True to create cards."
            }
        
        # Create connection cards
        connection_card_ids = []
        
        # Calculate center position from all cards
        all_cards = [get_card(cid) for cid in card_ids]
        avg_x = sum(c["position_x"] for c in all_cards) / len(all_cards)
        avg_y = sum(c["position_y"] for c in all_cards) / len(all_cards)
        
        for i, connection in enumerate(connections):
            # Calculate position around center
            child_x, child_y = calculate_child_position(
                parent_x=avg_x,
                parent_y=avg_y,
                child_index=i,
                total_children=len(connections),
                radius=350
            )
            
            # Format connection content
            content = f"**Type:** {connection.get('type', 'Connection')}\n"
            content += f"**Surprise Factor:** {connection.get('surprise_factor', 'Medium')}\n\n"
            content += f"{connection.get('explanation', '')}\n\n"
            
            if connection.get("shared_principle"):
                content += f"**Shared Principle:** {connection['shared_principle']}\n\n"
            
            if connection.get("interdisciplinary_fields"):
                fields = ", ".join(connection["interdisciplinary_fields"])
                content += f"**Fields Connected:** {fields}\n\n"
            
            if connection.get("examples"):
                content += "**Examples:**\n"
                for example in connection["examples"]:
                    content += f"• {example}\n"
            
            # Create connection card
            connection_card = create_card(
                canvas_id=canvas_id,
                title=f"🔗 {connection.get('title', 'Surprising Connection')}",
                content=content,
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                tags=["connection", "interdisciplinary", connection.get("type", "link").lower()]
            )
            
            connection_card_ids.append(connection_card["id"])
            
            # Create connections to all involved cards
            involved_cards = connection.get("cards_involved", card_ids)
            for card_id in involved_cards:
                if card_id in card_ids:  # Only connect to cards that were analyzed
                    create_connection(
                        canvas_id=canvas_id,
                        source_id=connection_card["id"],
                        target_id=card_id,
                        connection_type="connects"
                    )
        
        logger.info(f"Created {len(connection_card_ids)} connection cards")
        
        # Build cards array for chat display
        cards_for_chat = []
        for i, connection in enumerate(connections):
            if i < len(connection_card_ids):
                cards_for_chat.append({
                    "id": connection_card_ids[i],
                    "title": f"🔗 {connection.get('title', 'Surprising Connection')}",
                    "type": "rich_text",
                    "parent_id": None
                })
        
        return {
            "success": True,
            "connections": connections,
            "connection_card_ids": connection_card_ids,
            "preview": False,
            # Chat integration fields
            "cards": cards_for_chat,
            "summary": f"Discovered {len(connection_card_ids)} surprising connections between topics",
            "operation_type": "connect_dots"
        }
        
    except Exception as e:
        logger.error(f"Error finding surprising connections: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "connections": []
        }


@tool
def comprehensive_learn(
    topic: str,
    canvas_id: str,
    create_card_option: bool = False,
    depth: str = "standard"
) -> dict:
    """
    Execute comprehensive learning workflow for a topic.
    
    Creates a complete knowledge cluster by executing multiple learning actions:
    1. Create main topic card
    2. Extract core concepts
    3. Find prerequisites
    4. Find advanced topics
    5. Generate learning questions
    6. Find real-world examples
    7. Identify challenges/counterpoints
    8. Create learning path
    
    Args:
        topic: Topic to learn comprehensively
        canvas_id: Canvas ID
        create_card_option: If True, creates complete cluster
        depth: "quick" (10-15 cards), "standard" (20-30 cards), "deep" (40+ cards)
        
    Returns:
        {
            "success": bool,
            "cluster_summary": dict,
            "learning_path": dict,
            "estimated_study_time": str,
            "card_ids": dict,
            "preview": bool
        }
    """
    logger.info(f"Starting comprehensive learning for topic: {topic} (depth: {depth})")
    
    try:
        from agents.model_provider import get_nvidia_nim_model
        model = get_nvidia_nim_model()
        
        # Build comprehensive learning plan
        prompt = PromptTemplates.comprehensive_learn_prompt(topic, depth)
        response = model(prompt)
        
        # Parse learning plan
        try:
            from prompts import PromptFormatter
            learning_plan = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(learning_plan, dict):
                raise ValueError("Response is not a JSON object")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "success": False,
                "error": "Failed to create learning plan",
                "cluster_summary": {}
            }
        
        # If create_card_option is False, return preview
        if not create_card_option:
            total_cards = (
                1 +  # main topic
                len(learning_plan.get("core_concepts", [])) +
                len(learning_plan.get("prerequisites", [])) +
                len(learning_plan.get("advanced_topics", [])) +
                len(learning_plan.get("questions", [])) +
                len(learning_plan.get("examples", [])) +
                len(learning_plan.get("challenges", [])) +
                1  # learning path
            )
            
            return {
                "success": True,
                "cluster_summary": {
                    "total_cards": total_cards,
                    "breakdown": {
                        "main_topic": 1,
                        "core_concepts": len(learning_plan.get("core_concepts", [])),
                        "prerequisites": len(learning_plan.get("prerequisites", [])),
                        "advanced_topics": len(learning_plan.get("advanced_topics", [])),
                        "questions": len(learning_plan.get("questions", [])),
                        "examples": len(learning_plan.get("examples", [])),
                        "challenges": len(learning_plan.get("challenges", []))
                    }
                },
                "learning_path": learning_plan.get("learning_path", {}),
                "estimated_study_time": learning_plan.get("estimated_study_time", "Unknown"),
                "preview": True,
                "message": f"Will create {total_cards} cards. Set create_card_option=True to create cluster."
            }
        
        # Create comprehensive learning cluster
        card_ids = {}
        
        # Step 1: Create main topic card (center)
        main_card = create_card(
            canvas_id=canvas_id,
            title=f"📚 {topic}",
            content=learning_plan.get("overview", f"Comprehensive learning cluster for {topic}"),
            card_type="rich_text",
            position_x=0,
            position_y=0,
            tags=["learning", "main-topic", "comprehensive"]
        )
        card_ids["main"] = main_card["id"]
        
        # Step 2: Create core concept cards
        concept_ids = []
        concepts = learning_plan.get("core_concepts", [])
        for i, concept in enumerate(concepts):
            child_x, child_y = calculate_child_position(
                parent_x=0, parent_y=0,
                child_index=i,
                total_children=len(concepts),
                radius=300
            )
            
            concept_card = create_card(
                canvas_id=canvas_id,
                title=f"💡 {concept.get('title', 'Concept')}",
                content=concept.get("description", ""),
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                parent_id=main_card["id"],
                tags=["concept", "core"]
            )
            concept_ids.append(concept_card["id"])
            create_connection(canvas_id, main_card["id"], concept_card["id"], "contains")
        
        card_ids["concepts"] = concept_ids
        
        # Step 3: Create prerequisite cards
        prereq_ids = []
        prerequisites = learning_plan.get("prerequisites", [])
        for i, prereq in enumerate(prerequisites):
            child_x, child_y = calculate_child_position(
                parent_x=-400, parent_y=0,
                child_index=i,
                total_children=len(prerequisites),
                radius=200
            )
            
            prereq_card = create_card(
                canvas_id=canvas_id,
                title=f"🔍 {prereq.get('title', 'Prerequisite')}",
                content=f"**Importance:** {prereq.get('importance', 'Medium')}\n\n{prereq.get('description', '')}",
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                tags=["prerequisite", "foundation"]
            )
            prereq_ids.append(prereq_card["id"])
            create_connection(canvas_id, prereq_card["id"], main_card["id"], "prerequisite")
        
        card_ids["prerequisites"] = prereq_ids
        
        # Step 4: Create advanced topic cards
        advanced_ids = []
        advanced_topics = learning_plan.get("advanced_topics", [])
        for i, advanced in enumerate(advanced_topics):
            child_x, child_y = calculate_child_position(
                parent_x=400, parent_y=0,
                child_index=i,
                total_children=len(advanced_topics),
                radius=200
            )
            
            advanced_card = create_card(
                canvas_id=canvas_id,
                title=f"🎯 {advanced.get('title', 'Advanced Topic')}",
                content=advanced.get("description", ""),
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                tags=["advanced", "next-level"]
            )
            advanced_ids.append(advanced_card["id"])
            create_connection(canvas_id, main_card["id"], advanced_card["id"], "extends")
        
        card_ids["advanced"] = advanced_ids
        
        # Step 5: Create question cards
        question_ids = []
        questions = learning_plan.get("questions", [])
        for i, question in enumerate(questions):
            child_x, child_y = calculate_child_position(
                parent_x=0, parent_y=400,
                child_index=i,
                total_children=len(questions),
                radius=250
            )
            
            question_card = create_card(
                canvas_id=canvas_id,
                title=f"❓ {question.get('question', 'Learning Question')}",
                content=f"**Difficulty:** {question.get('difficulty', 'Medium')}\n\n**Answer:** {question.get('answer', 'Think about this...')}",
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                tags=["question", "learning"]
            )
            question_ids.append(question_card["id"])
        
        card_ids["questions"] = question_ids
        
        # Step 6: Create example cards
        example_ids = []
        examples = learning_plan.get("examples", [])
        for i, example in enumerate(examples):
            child_x, child_y = calculate_child_position(
                parent_x=0, parent_y=-400,
                child_index=i,
                total_children=len(examples),
                radius=250
            )
            
            example_card = create_card(
                canvas_id=canvas_id,
                title=f"🌍 {example.get('name', 'Example')}",
                content=f"**Industry:** {example.get('industry', 'N/A')}\n\n{example.get('description', '')}",
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                tags=["example", "real-world"]
            )
            example_ids.append(example_card["id"])
            create_connection(canvas_id, main_card["id"], example_card["id"], "exemplifies")
        
        card_ids["examples"] = example_ids
        
        # Step 7: Create challenge/counterpoint cards
        challenge_ids = []
        challenges = learning_plan.get("challenges", [])
        for i, challenge in enumerate(challenges):
            child_x, child_y = calculate_child_position(
                parent_x=300, parent_y=300,
                child_index=i,
                total_children=len(challenges),
                radius=200
            )
            
            challenge_card = create_card(
                canvas_id=canvas_id,
                title=f"⚖️ {challenge.get('title', 'Challenge')}",
                content=challenge.get("description", ""),
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                tags=["challenge", "counterpoint"]
            )
            challenge_ids.append(challenge_card["id"])
            create_connection(canvas_id, challenge_card["id"], main_card["id"], "challenges")
        
        card_ids["challenges"] = challenge_ids
        
        # Step 8: Create learning path card
        learning_path_content = "**Suggested Learning Path:**\n\n"
        path = learning_plan.get("learning_path", {})
        for phase, topics in path.items():
            learning_path_content += f"**{phase.replace('_', ' ').title()}:**\n"
            for topic_item in topics:
                learning_path_content += f"• {topic_item}\n"
            learning_path_content += "\n"
        
        path_card = create_card(
            canvas_id=canvas_id,
            title=f"🗺️ Learning Path: {topic}",
            content=learning_path_content,
            card_type="rich_text",
            position_x=-300,
            position_y=-300,
            tags=["learning-path", "roadmap"]
        )
        card_ids["learning_path"] = path_card["id"]
        create_connection(canvas_id, path_card["id"], main_card["id"], "guides")
        
        # Calculate totals
        total_cards = (
            1 +  # main
            len(concept_ids) +
            len(prereq_ids) +
            len(advanced_ids) +
            len(question_ids) +
            len(example_ids) +
            len(challenge_ids) +
            1  # learning path
        )
        
        logger.info(f"Created comprehensive learning cluster with {total_cards} cards")
        
        return {
            "success": True,
            "cluster_summary": {
                "total_cards_created": total_cards,
                "breakdown": {
                    "main_topic": 1,
                    "core_concepts": len(concept_ids),
                    "prerequisites": len(prereq_ids),
                    "advanced_topics": len(advanced_ids),
                    "questions": len(question_ids),
                    "examples": len(example_ids),
                    "challenges": len(challenge_ids),
                    "learning_path": 1
                }
            },
            "learning_path": path,
            "estimated_study_time": learning_plan.get("estimated_study_time", "8-12 hours"),
            "card_ids": card_ids,
            "preview": False
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive learning: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "cluster_summary": {}
        }
