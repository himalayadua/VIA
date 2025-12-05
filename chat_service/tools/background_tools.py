"""
Background Tools

Tools for the Background Intelligence Agent to automatically enhance canvas content.
These tools run automatically in response to canvas events (card creation/updates).

Tools:
- generate_learning_questions: Extract thoughtful questions from content
- extract_action_items: Detect actionable items and create Todo cards
- detect_deadlines: Find dates/deadlines and create Reminder cards
- extract_entities: Perform NER to extract people, concepts, techniques
- suggest_merge_duplicates: Detect duplicate cards for merging
- detect_contradictions: Find conflicting information across cards
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
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


@tool
def generate_learning_questions(
    content: str,
    card_id: str,
    canvas_id: str,
    num_questions: int = 3
) -> dict:
    """
    Generate thoughtful learning questions from content.
    
    Analyzes content using LLM to extract key concepts as questions.
    Creates question cards linked to the source card.
    
    Args:
        content: Content to analyze
        card_id: Source card ID
        canvas_id: Canvas ID
        num_questions: Number of questions to generate (default 3, max 5)
        
    Returns:
        {
            "success": bool,
            "questions": list[dict],
            "question_card_ids": list[str],
            "summary": str
        }
    """
    logger.info(f"Generating {num_questions} learning questions for card {card_id}")
    
    try:
        # Validate parameters
        num_questions = max(1, min(num_questions, 5))  # Clamp between 1 and 5
        
        # Check if content is substantial enough
        if len(content.strip()) < 50:
            logger.info("Content too short for question generation")
            return {
                "success": True,
                "questions": [],
                "question_card_ids": [],
                "summary": "Content too short for meaningful questions"
            }
        
        # Get source card for context
        source_card = get_card(card_id)
        card_title = source_card.get("title", "") if source_card else ""
        
        # Build prompt for question generation
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.generate_questions_prompt(
            content=content,
            title=card_title,
            num_questions=num_questions
        )
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # Parse JSON response
        try:
            from prompts import PromptFormatter
            questions = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(questions, list):
                raise ValueError("Response is not a JSON array")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "success": False,
                "error": "Failed to generate questions",
                "questions": [],
                "question_card_ids": []
            }
        
        # Create question cards
        question_card_ids = []
        
        for i, q in enumerate(questions[:num_questions]):
            # Calculate position in circular arrangement
            child_x, child_y = calculate_child_position(
                parent_x=source_card["position_x"],
                parent_y=source_card["position_y"],
                child_index=i,
                total_children=len(questions[:num_questions]),
                radius=280
            )
            
            # Format question card content
            question_text = q.get("question", "")
            difficulty = q.get("difficulty", "intermediate")
            focus_area = q.get("focus_area", "general")
            
            card_content = f"**Difficulty:** {difficulty}\n**Focus:** {focus_area}\n\n{q.get('explanation', '')}"
            
            # Create question card
            question_card = create_card(
                canvas_id=canvas_id,
                title=f"❓ {question_text}",
                content=card_content,
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                parent_id=card_id,
                tags=["question", focus_area, difficulty]
            )
            
            question_card_ids.append(question_card["id"])
            
            # Create connection
            create_connection(
                canvas_id=canvas_id,
                source_id=card_id,
                target_id=question_card["id"],
                connection_type="parent-child"
            )
        
        logger.info(f"Created {len(question_card_ids)} question cards")
        
        return {
            "success": True,
            "questions": questions[:num_questions],
            "question_card_ids": question_card_ids,
            "summary": f"Generated {len(question_card_ids)} learning questions"
        }
        
    except Exception as e:
        logger.error(f"Error generating questions: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "questions": [],
            "question_card_ids": []
        }


@tool
def extract_action_items(
    content: str,
    card_id: str,
    canvas_id: str
) -> dict:
    """
    Extract actionable items and create Todo cards.
    
    Detects frameworks, steps, and action items in content.
    Creates Todo cards with checklist items linked to source.
    
    Args:
        content: Content to analyze
        card_id: Source card ID
        canvas_id: Canvas ID
        
    Returns:
        {
            "success": bool,
            "action_items": list[dict],
            "todo_card_ids": list[str],
            "summary": str
        }
    """
    logger.info(f"Extracting action items from card {card_id}")
    
    try:
        # Check if content has actionable indicators
        actionable_keywords = ["step", "todo", "action", "implement", "create", "build", "setup", "configure"]
        has_actionable = any(keyword in content.lower() for keyword in actionable_keywords)
        
        if not has_actionable or len(content.strip()) < 50:
            logger.info("No actionable content detected")
            return {
                "success": True,
                "action_items": [],
                "todo_card_ids": [],
                "summary": "No actionable items found"
            }
        
        # Get source card for context
        source_card = get_card(card_id)
        card_title = source_card.get("title", "") if source_card else ""
        
        # Build prompt for action extraction
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.extract_actions_prompt(
            content=content,
            title=card_title
        )
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # Parse JSON response
        try:
            from prompts import PromptFormatter
            action_items = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(action_items, list):
                raise ValueError("Response is not a JSON array")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "success": False,
                "error": "Failed to extract action items",
                "action_items": [],
                "todo_card_ids": []
            }
        
        # Create todo cards
        todo_card_ids = []
        
        for i, item in enumerate(action_items):
            # Calculate position
            child_x, child_y = calculate_child_position(
                parent_x=source_card["position_x"],
                parent_y=source_card["position_y"],
                child_index=i,
                total_children=len(action_items),
                radius=280
            )
            
            # Create todo items list
            todo_items = [
                {"text": step, "completed": False}
                for step in item.get("steps", [])
            ]
            
            # Create todo card
            todo_card = create_card(
                canvas_id=canvas_id,
                title=f"✓ {item.get('title', 'Action Item')}",
                content=item.get("description", ""),
                card_type="todo",
                position_x=child_x,
                position_y=child_y,
                parent_id=card_id,
                tags=["action", item.get("priority", "medium")],
                card_data={
                    "items": todo_items,
                    "progress": 0,
                    "priority": item.get("priority", "medium"),
                    "estimated_time": item.get("estimated_time", "")
                }
            )
            
            todo_card_ids.append(todo_card["id"])
            
            # Create connection
            create_connection(
                canvas_id=canvas_id,
                source_id=card_id,
                target_id=todo_card["id"],
                connection_type="parent-child"
            )
        
        logger.info(f"Created {len(todo_card_ids)} todo cards")
        
        return {
            "success": True,
            "action_items": action_items,
            "todo_card_ids": todo_card_ids,
            "summary": f"Extracted {len(todo_card_ids)} action items"
        }
        
    except Exception as e:
        logger.error(f"Error extracting action items: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "action_items": [],
            "todo_card_ids": []
        }


@tool
def detect_deadlines(
    content: str,
    card_id: str,
    canvas_id: str
) -> dict:
    """
    Detect dates and deadlines, create Reminder cards.
    
    Uses NLP to extract dates and deadlines from content.
    Creates Reminder cards with countdown linked to source.
    
    Args:
        content: Content to analyze
        card_id: Source card ID
        canvas_id: Canvas ID
        
    Returns:
        {
            "success": bool,
            "deadlines": list[dict],
            "reminder_card_ids": list[str],
            "summary": str
        }
    """
    logger.info(f"Detecting deadlines in card {card_id}")
    
    try:
        # Check for date-related keywords
        date_keywords = ["deadline", "due", "by", "until", "before", "date", "schedule"]
        has_dates = any(keyword in content.lower() for keyword in date_keywords)
        
        if not has_dates:
            logger.info("No date-related content detected")
            return {
                "success": True,
                "deadlines": [],
                "reminder_card_ids": [],
                "summary": "No deadlines found"
            }
        
        # Try to parse dates using dateparser
        try:
            import dateparser
        except ImportError:
            logger.warning("dateparser not installed, using LLM-only approach")
            dateparser = None
        
        # Get source card for context
        source_card = get_card(card_id)
        card_title = source_card.get("title", "") if source_card else ""
        
        # Build prompt for deadline extraction
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.extract_deadlines_prompt(
            content=content,
            title=card_title
        )
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # Parse JSON response
        try:
            from prompts import PromptFormatter
            deadlines = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(deadlines, list):
                raise ValueError("Response is not a JSON array")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "success": False,
                "error": "Failed to extract deadlines",
                "deadlines": [],
                "reminder_card_ids": []
            }
        
        # Create reminder cards
        reminder_card_ids = []
        
        for i, deadline in enumerate(deadlines):
            # Calculate position
            child_x, child_y = calculate_child_position(
                parent_x=source_card["position_x"],
                parent_y=source_card["position_y"],
                child_index=i,
                total_children=len(deadlines),
                radius=280
            )
            
            # Parse date if dateparser available
            deadline_date = deadline.get("date", "")
            parsed_date = None
            
            if dateparser and deadline_date:
                parsed_date = dateparser.parse(deadline_date)
            
            # Format reminder content
            reminder_content = deadline.get("description", "")
            if parsed_date:
                days_until = (parsed_date - datetime.now()).days
                reminder_content += f"\n\n**Days until deadline:** {days_until}"
            
            # Create reminder card
            reminder_card = create_card(
                canvas_id=canvas_id,
                title=f"⏰ {deadline.get('title', 'Deadline')}",
                content=reminder_content,
                card_type="reminder",
                position_x=child_x,
                position_y=child_y,
                parent_id=card_id,
                tags=["deadline", "reminder"],
                card_data={
                    "date": deadline_date,
                    "parsed_date": parsed_date.isoformat() if parsed_date else None,
                    "priority": deadline.get("priority", "medium")
                }
            )
            
            reminder_card_ids.append(reminder_card["id"])
            
            # Create connection
            create_connection(
                canvas_id=canvas_id,
                source_id=card_id,
                target_id=reminder_card["id"],
                connection_type="parent-child"
            )
        
        logger.info(f"Created {len(reminder_card_ids)} reminder cards")
        
        return {
            "success": True,
            "deadlines": deadlines,
            "reminder_card_ids": reminder_card_ids,
            "summary": f"Detected {len(reminder_card_ids)} deadlines"
        }
        
    except Exception as e:
        logger.error(f"Error detecting deadlines: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "deadlines": [],
            "reminder_card_ids": []
        }


@tool
def extract_entities(
    content: str,
    card_id: str,
    canvas_id: str
) -> dict:
    """
    Extract entities (people, concepts, techniques) using NER.
    
    Uses LLM for Named Entity Recognition to extract:
    - People (authors, researchers, inventors)
    - Concepts (theories, principles, ideas)
    - Techniques (methods, algorithms, frameworks)
    
    Creates entity cards and establishes relationships.
    Avoids duplicates by checking existing cards.
    
    Args:
        content: Content to analyze
        card_id: Source card ID
        canvas_id: Canvas ID
        
    Returns:
        {
            "success": bool,
            "entities": dict,  # {people: [], concepts: [], techniques: []}
            "entity_card_ids": list[str],
            "summary": str
        }
    """
    logger.info(f"Extracting entities from card {card_id}")
    
    try:
        # Check if content is substantial enough
        if len(content.strip()) < 100:
            logger.info("Content too short for entity extraction")
            return {
                "success": True,
                "entities": {"people": [], "concepts": [], "techniques": []},
                "entity_card_ids": [],
                "summary": "Content too short for entity extraction"
            }
        
        # Get source card for context
        source_card = get_card(card_id)
        card_title = source_card.get("title", "") if source_card else ""
        
        # Build prompt for entity extraction
        from agents.model_provider import get_nvidia_nim_model
        
        prompt = PromptTemplates.extract_entities_prompt(
            content=content,
            title=card_title
        )
        
        # Get LLM response
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # Parse JSON response
        try:
            from prompts import PromptFormatter
            entities = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(entities, dict):
                raise ValueError("Response is not a JSON object")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "success": False,
                "error": "Failed to extract entities",
                "entities": {"people": [], "concepts": [], "techniques": []},
                "entity_card_ids": []
            }
        
        # Get existing cards to avoid duplicates
        existing_cards = get_canvas_cards(canvas_id)
        existing_titles = {card.get("title", "").lower() for card in existing_cards}
        
        # Create entity cards
        entity_card_ids = []
        all_entities = []
        
        # Process people
        for person in entities.get("people", []):
            name = person.get("name", "")
            if name.lower() not in existing_titles:
                all_entities.append(("person", person))
        
        # Process concepts
        for concept in entities.get("concepts", []):
            name = concept.get("name", "")
            if name.lower() not in existing_titles:
                all_entities.append(("concept", concept))
        
        # Process techniques
        for technique in entities.get("techniques", []):
            name = technique.get("name", "")
            if name.lower() not in existing_titles:
                all_entities.append(("technique", technique))
        
        # Create cards for unique entities
        for i, (entity_type, entity) in enumerate(all_entities):
            # Calculate position
            child_x, child_y = calculate_child_position(
                parent_x=source_card["position_x"],
                parent_y=source_card["position_y"],
                child_index=i,
                total_children=len(all_entities),
                radius=300
            )
            
            # Choose icon based on type
            icon = {"person": "👤", "concept": "💡", "technique": "🔧"}.get(entity_type, "📌")
            
            # Create entity card
            entity_card = create_card(
                canvas_id=canvas_id,
                title=f"{icon} {entity.get('name', 'Entity')}",
                content=entity.get("description", ""),
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                parent_id=card_id,
                tags=[entity_type, "entity"]
            )
            
            entity_card_ids.append(entity_card["id"])
            
            # Create connection
            create_connection(
                canvas_id=canvas_id,
                source_id=card_id,
                target_id=entity_card["id"],
                connection_type="mentions"
            )
        
        logger.info(f"Created {len(entity_card_ids)} entity cards")
        
        return {
            "success": True,
            "entities": entities,
            "entity_card_ids": entity_card_ids,
            "summary": f"Extracted {len(entity_card_ids)} unique entities"
        }
        
    except Exception as e:
        logger.error(f"Error extracting entities: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "entities": {"people": [], "concepts": [], "techniques": []},
            "entity_card_ids": []
        }


@tool
def suggest_merge_duplicates(
    canvas_id: str,
    duplicate_threshold: float = 0.9
) -> dict:
    """
    Detect duplicate cards and suggest merging.
    
    Calculates pairwise similarity for all cards on canvas.
    Detects duplicates (similarity > threshold).
    Generates merge suggestions with preview.
    
    Args:
        canvas_id: Canvas ID to analyze
        duplicate_threshold: Similarity threshold for duplicates (default 0.9)
        
    Returns:
        {
            "success": bool,
            "duplicates": list[dict],  # [{card1_id, card2_id, similarity, preview}]
            "summary": str
        }
    """
    logger.info(f"Detecting duplicates on canvas {canvas_id}")
    
    try:
        # Use existing detect_conflicts tool
        from tools.canvas_tools import detect_conflicts
        
        result = detect_conflicts(
            canvas_id=canvas_id,
            duplicate_threshold=duplicate_threshold
        )
        
        if not result.get("success"):
            return result
        
        # Extract just the duplicates
        duplicates = [
            conflict for conflict in result.get("conflicts", [])
            if conflict.get("type") == "duplicate"
        ]
        
        logger.info(f"Found {len(duplicates)} duplicate pairs")
        
        return {
            "success": True,
            "duplicates": duplicates,
            "summary": f"Found {len(duplicates)} duplicate card pairs"
        }
        
    except Exception as e:
        logger.error(f"Error detecting duplicates: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "duplicates": []
        }


@tool
def detect_contradictions(
    canvas_id: str,
    conflict_threshold: float = 0.6
) -> dict:
    """
    Detect contradictions and conflicting information across cards.
    
    Finds related cards by similarity.
    Uses LLM to detect contradictions.
    Calculates contradiction severity.
    Creates conflict cards for high-severity contradictions.
    
    Args:
        canvas_id: Canvas ID to analyze
        conflict_threshold: Similarity threshold for checking conflicts (default 0.6)
        
    Returns:
        {
            "success": bool,
            "contradictions": list[dict],  # [{card1_id, card2_id, severity, explanation}]
            "conflict_card_ids": list[str],
            "summary": str
        }
    """
    logger.info(f"Detecting contradictions on canvas {canvas_id}")
    
    try:
        # Use existing detect_conflicts tool
        from tools.canvas_tools import detect_conflicts
        
        result = detect_conflicts(
            canvas_id=canvas_id,
            conflict_threshold=conflict_threshold
        )
        
        if not result.get("success"):
            return result
        
        # Extract just the contradictions
        contradictions = [
            conflict for conflict in result.get("conflicts", [])
            if conflict.get("type") == "conflicting_info"
        ]
        
        # Create conflict cards for high-severity contradictions
        conflict_card_ids = []
        
        for contradiction in contradictions:
            if contradiction.get("severity") == "high":
                # Get the conflicting cards
                card_ids = contradiction.get("card_ids", [])
                if len(card_ids) >= 2:
                    card1 = get_card(card_ids[0])
                    card2 = get_card(card_ids[1])
                    
                    if card1 and card2:
                        # Create conflict card
                        conflict_content = f"""**Contradiction Detected**

**Card 1:** {card1.get('title', 'Untitled')}
{card1.get('content', '')[:200]}...

**Card 2:** {card2.get('title', 'Untitled')}
{card2.get('content', '')[:200]}...

**Explanation:** {contradiction.get('suggestion', 'These cards contain conflicting information.')}
"""
                        
                        conflict_card = create_card(
                            canvas_id=canvas_id,
                            title="⚠️ Contradiction Detected",
                            content=conflict_content,
                            card_type="rich_text",
                            position_x=0,
                            position_y=0,
                            tags=["contradiction", "conflict", "warning"]
                        )
                        
                        conflict_card_ids.append(conflict_card["id"])
                        
                        # Create connections to both conflicting cards
                        create_connection(
                            canvas_id=canvas_id,
                            source_id=conflict_card["id"],
                            target_id=card_ids[0],
                            connection_type="challenges"
                        )
                        create_connection(
                            canvas_id=canvas_id,
                            source_id=conflict_card["id"],
                            target_id=card_ids[1],
                            connection_type="challenges"
                        )
        
        logger.info(f"Found {len(contradictions)} contradictions, created {len(conflict_card_ids)} conflict cards")
        
        return {
            "success": True,
            "contradictions": contradictions,
            "conflict_card_ids": conflict_card_ids,
            "summary": f"Found {len(contradictions)} contradictions, created {len(conflict_card_ids)} conflict cards"
        }
        
    except Exception as e:
        logger.error(f"Error detecting contradictions: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "contradictions": [],
            "conflict_card_ids": []
        }
