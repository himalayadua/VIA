"""
Canvas Tools

Tools for AI agents to interact with the canvas:
- extract_url_content: Extract content from URLs and create cards
- grow_card_content: Expand cards by extracting key concepts
- find_similar_cards: Find semantically similar cards
- categorize_content: Auto-categorize and tag content
- detect_conflicts: Find duplicate or conflicting cards
"""

import logging
import json
from typing import Dict, List, Optional
from strands import tool

# Import extractors
from extractors import (
    URLExtractor,
    URLType,
    DocumentationExtractor,
    GitHubExtractor,
    VideoExtractor
)
from extractors.cache import get_extraction_cache
from extractors.rate_limiter import get_global_rate_limiter

# Import canvas API helpers
from .canvas_api import (
    create_card,
    get_card,
    get_canvas_cards,
    create_connection,
    calculate_child_position
)

# Import events for background processing
from events import canvas_events, CanvasEvents

logger = logging.getLogger(__name__)


@tool
def extract_url_content(url: str, canvas_id: str, parent_id: Optional[str] = None, session_id: Optional[str] = None) -> dict:
    """
    Extract structured content from a URL and create canvas cards with progress tracking.
    
    This tool:
    1. Detects the URL type (documentation, GitHub, video, etc.)
    2. Uses the appropriate extractor to fetch and parse content
    3. Creates a parent card with the main content
    4. Creates child cards for each section
    5. Creates connections between parent and children
    6. Uses caching to avoid re-fetching the same URL
    7. Respects rate limits to avoid overwhelming external services
    8. Tracks progress and emits real-time updates via SSE
    9. Saves checkpoints for recovery from interruptions
    
    Args:
        url: The URL to extract content from
        canvas_id: Canvas ID where cards will be created
        parent_id: Optional parent card ID to attach extracted content to
        session_id: Optional session ID for SSE routing
        
    Returns:
        {
            "success": bool,
            "url": str,
            "url_type": str,
            "parent_card_id": str,
            "child_card_ids": list[str],
            "total_cards": int,
            "cached": bool,
            "summary": str,
            "operation_id": str
        }
    """
    logger.info(f"Extracting content from URL: {url} for canvas: {canvas_id}")
    
    # Initialize progress tracker
    from progress import ProgressTracker, CheckpointManager
    
    tracker = ProgressTracker(
        operation_type="url_extraction",
        total_steps=5,
        canvas_id=canvas_id,
        session_id=session_id
    )
    
    checkpoint_manager = CheckpointManager()
    
    try:
        # Step 1: Check cache and rate limit (10%)
        tracker.update_progress("initializing", 0.1, f"Checking cache for {url}...")
        
        cache = get_extraction_cache()
        rate_limiter = get_global_rate_limiter()
        
        # Check cache first
        cached_result = cache.get(url)
        if cached_result:
            logger.info(f"Using cached extraction for: {url}")
            extraction_data = cached_result
            from_cache = True
            tracker.update_progress("cache_hit", 0.3, "Using cached content")
        else:
            # Check rate limit
            if not rate_limiter.wait_if_needed(timeout=30):
                logger.error(f"Rate limit timeout for URL: {url}")
                tracker.fail("Rate limit exceeded")
                return {
                    "success": False,
                    "error": "Rate limit exceeded. Please try again in a moment.",
                    "url": url,
                    "operation_id": tracker.operation_id
                }
            
            # Step 2: Fetch and parse content (30%)
            tracker.update_progress("fetching", 0.3, f"Fetching content from {url}...")
            
            # Detect URL type
            url_type = URLExtractor.detect_url_type(url)
            logger.info(f"Detected URL type: {url_type.value}")
            
            # Choose appropriate extractor
            if url_type == URLType.DOCUMENTATION:
                extractor = DocumentationExtractor(url)
            elif url_type == URLType.GITHUB:
                extractor = GitHubExtractor(url)
            elif url_type == URLType.VIDEO:
                extractor = VideoExtractor(url)
            else:
                # Default to documentation extractor for generic URLs
                extractor = DocumentationExtractor(url)
            
            # Extract content
            tracker.update_progress("parsing", 0.5, "Parsing and extracting content...")
            extraction_data = extractor.extract()
            
            # Cache the result
            cache.set(url, extraction_data)
            from_cache = False
        
        # Save checkpoint before creating cards
        if tracker.should_save_checkpoint():
            checkpoint_manager.save_checkpoint(tracker.get_checkpoint_data())
        
        # Step 3: Create cards (70%)
        sections_count = len(extraction_data.get("sections", []))
        tracker.update_progress(
            "creating_cards",
            0.7,
            f"Creating cards for {sections_count} sections..."
        )
        
        cards_created = _create_cards_from_extraction(
            extraction_data=extraction_data,
            canvas_id=canvas_id,
            parent_id=parent_id
        )
        
        # Track created cards
        tracker.add_cards_created(cards_created["all_card_ids"])
        
        # Save checkpoint after card creation
        if tracker.should_save_checkpoint():
            checkpoint_manager.save_checkpoint(tracker.get_checkpoint_data())
        
        # Step 4: Emit events for background processing (90%)
        tracker.update_progress("finalizing", 0.9, "Triggering background processing...")
        
        for card_id in cards_created["all_card_ids"]:
            canvas_events.emit(CanvasEvents.CARD_CREATED, {
                "card_id": card_id,
                "canvas_id": canvas_id,
                "source": "url_extraction",
                "url": url
            })
        
        # Step 5: Complete (100%)
        result = {
            "success": True,
            "url": url,
            "url_type": extraction_data.get("metadata", {}).get("type", "unknown"),
            "parent_card_id": cards_created["parent_card_id"],
            "child_card_ids": cards_created["child_card_ids"],
            "total_cards": len(cards_created["all_card_ids"]),
            "cached": from_cache,
            "summary": f"Created {len(cards_created['all_card_ids'])} cards from {url}",
            "operation_id": tracker.operation_id
        }
        
        tracker.complete(f"Successfully created {len(cards_created['all_card_ids'])} cards")
        
        # Clean up checkpoint on success
        checkpoint_manager.delete_checkpoint(tracker.operation_id)
        
        logger.info(f"Successfully extracted {url}: {result['total_cards']} cards created")
        return result
        
    except Exception as e:
        logger.error(f"Error extracting URL {url}: {e}", exc_info=True)
        tracker.fail(str(e))
        
        # Save checkpoint on failure for potential recovery
        checkpoint_manager.save_checkpoint(tracker.get_checkpoint_data())
        
        return {
            "success": False,
            "error": str(e),
            "url": url,
            "suggestion": "Try creating a simple link card instead, or check if the URL is accessible.",
            "operation_id": tracker.operation_id
        }


def _create_cards_from_extraction(
    extraction_data: Dict,
    canvas_id: str,
    parent_id: Optional[str] = None
) -> Dict:
    """
    Create canvas cards from extracted content with pattern extraction.
    
    Args:
        extraction_data: Extracted content structure from extractor
        canvas_id: Canvas ID where cards will be created
        parent_id: Optional parent card ID
        
    Returns:
        {
            "parent_card_id": str,
            "child_card_ids": list[str],
            "all_card_ids": list[str],
            "patterns_extracted": int,
            "examples_count": int,
            "patterns_count": int
        }
    """
    all_card_ids = []
    
    # Determine card type
    card_type = extraction_data.get("card_type", "rich_text")
    
    # Prepare card data based on type
    card_data = {}
    if card_type == "link":
        card_data = {
            "url": extraction_data.get("metadata", {}).get("url", ""),
            "description": extraction_data.get("description", "")
        }
    elif card_type == "video":
        card_data = {
            "videoUrl": extraction_data.get("metadata", {}).get("url", ""),
            "videoId": extraction_data.get("metadata", {}).get("video_id", "")
        }
    
    # Use intelligent parent selection if no parent specified
    if parent_id is None:
        from graph import CardPlacer
        
        placer = CardPlacer()
        
        # Find best parent based on content similarity
        content_for_matching = extraction_data.get("description", "")
        suggested_parent_id, similarity = placer.find_best_parent(
            content_for_matching,
            canvas_id
        )
        
        # Use suggested parent if found
        if suggested_parent_id:
            parent_id = suggested_parent_id
            logger.info(f"Intelligent parent selection: parent={suggested_parent_id}, similarity={similarity:.2f}")
    
    # Use placeholder position - frontend layout algorithms will calculate actual positions
    position_x, position_y = 0, 0
    
    # Create parent card
    parent_card = create_card(
        canvas_id=canvas_id,
        title=extraction_data.get("title", "Extracted Content"),
        content=extraction_data.get("description", ""),
        card_type=card_type,
        position_x=position_x,
        position_y=position_y,
        parent_id=parent_id,
        tags=extraction_data.get("metadata", {}).get("topics", []),
        card_data=card_data
    )
    
    parent_card_id = parent_card["id"]
    all_card_ids.append(parent_card_id)
    
    # Extract patterns and examples from content
    from extractors.pattern_extractor import PatternExtractor
    
    full_content = extraction_data.get("description", "")
    for section in extraction_data.get("sections", []):
        full_content += "\n\n" + section.get("content", "")
    
    pattern_extractor = PatternExtractor(full_content)
    patterns = pattern_extractor.extract_patterns()
    grouped = pattern_extractor.parse_pattern_relationships(patterns)
    
    logger.info(f"Extracted {len(patterns)} patterns from content")
    
    # Create child cards for sections
    child_card_ids = []
    sections = extraction_data.get("sections", [])
    
    for i, section in enumerate(sections):
        # Calculate position in circular arrangement around parent
        # Use larger radius to prevent overlap (card width is 300px)
        child_x, child_y = calculate_child_position(
            parent_x=parent_card["position_x"],
            parent_y=parent_card["position_y"],
            child_index=i,
            total_children=len(sections),
            radius=400  # Increased from 280 to prevent overlap
        )
        
        # Create child card
        child_card = create_card(
            canvas_id=canvas_id,
            title=section.get("title", f"Section {i+1}"),
            content=section.get("content", ""),
            card_type="rich_text",
            position_x=child_x,
            position_y=child_y,
            parent_id=parent_card_id,
            tags=[]
        )
        
        child_card_ids.append(child_card["id"])
        all_card_ids.append(child_card["id"])
        
        # Create connection from parent to child
        create_connection(
            canvas_id=canvas_id,
            source_id=parent_card_id,
            target_id=child_card["id"],
            connection_type="default"  # Use 'default' instead of 'parent-child'
        )
    
    # Create "Examples" parent card if examples exist
    examples_parent_id = None
    if grouped["groups"]["examples"]:
        examples_parent = create_card(
            canvas_id=canvas_id,
            title="Examples",
            content=f"{len(grouped['groups']['examples'])} code examples extracted from content",
            card_type="rich_text",
            position_x=0,
            position_y=0,
            parent_id=parent_card_id,
            tags=["examples"]
        )
        examples_parent_id = examples_parent["id"]
        all_card_ids.append(examples_parent_id)
        
        # Create connection
        create_connection(
            canvas_id=canvas_id,
            source_id=parent_card_id,
            target_id=examples_parent_id,
            connection_type="default"
        )
        
        # Create individual example cards
        for example in grouped["groups"]["examples"]:
            # Format content with code block
            example_content = example.get("description", "")
            if example.get("code"):
                example_content += f"\n\n```{example.get('language', 'unknown')}\n{example['code']}\n```"
            
            example_card = create_card(
                canvas_id=canvas_id,
                title=example.get("title", "Example"),
                content=example_content,
                card_type="rich_text",
                position_x=0,
                position_y=0,
                parent_id=examples_parent_id,
                tags=["example", example.get("language", "unknown")]
            )
            all_card_ids.append(example_card["id"])
            
            # Create connection
            create_connection(
                canvas_id=canvas_id,
                source_id=examples_parent_id,
                target_id=example_card["id"],
                connection_type="default"
            )
        
        logger.info(f"Created {len(grouped['groups']['examples'])} example cards")
    
    # Create "Patterns" parent card if patterns exist
    patterns_parent_id = None
    if grouped["groups"]["patterns"]:
        patterns_parent = create_card(
            canvas_id=canvas_id,
            title="Patterns",
            content=f"{len(grouped['groups']['patterns'])} design patterns extracted from content",
            card_type="rich_text",
            position_x=0,
            position_y=0,
            parent_id=parent_card_id,
            tags=["patterns"]
        )
        patterns_parent_id = patterns_parent["id"]
        all_card_ids.append(patterns_parent_id)
        
        # Create connection
        create_connection(
            canvas_id=canvas_id,
            source_id=parent_card_id,
            target_id=patterns_parent_id,
            connection_type="default"
        )
        
        # Create individual pattern cards
        for pattern in grouped["groups"]["patterns"]:
            # Format content with code block
            pattern_content = pattern.get("description", "")
            if pattern.get("code"):
                pattern_content += f"\n\n```{pattern.get('language', 'unknown')}\n{pattern['code']}\n```"
            
            pattern_card = create_card(
                canvas_id=canvas_id,
                title=pattern.get("title", "Pattern"),
                content=pattern_content,
                card_type="rich_text",
                position_x=0,
                position_y=0,
                parent_id=patterns_parent_id,
                tags=["pattern", pattern.get("language", "unknown")]
            )
            all_card_ids.append(pattern_card["id"])
            
            # Create connection
            create_connection(
                canvas_id=canvas_id,
                source_id=patterns_parent_id,
                target_id=pattern_card["id"],
                connection_type="default"
            )
        
        logger.info(f"Created {len(grouped['groups']['patterns'])} pattern cards")
    
    # Create relationship connections (patterns/examples → concepts they demonstrate)
    # This links examples to concept cards if they exist on the canvas
    for relationship in grouped["relationships"]:
        concept_name = relationship.get("concept", "")
        pattern_title = relationship.get("pattern", "")
        
        # Try to find concept card on canvas
        try:
            canvas_cards = get_canvas_cards(canvas_id)
            concept_card = next(
                (card for card in canvas_cards if concept_name.lower() in card.get("title", "").lower()),
                None
            )
            
            # Find the pattern/example card we just created
            pattern_card = next(
                (card for card in canvas_cards if pattern_title == card.get("title", "")),
                None
            )
            
            if concept_card and pattern_card:
                # Create "demonstrates" connection
                create_connection(
                    canvas_id=canvas_id,
                    source_id=pattern_card["id"],
                    target_id=concept_card["id"],
                    connection_type="default"
                )
                logger.debug(f"Linked pattern '{pattern_title}' to concept '{concept_name}'")
        except Exception as e:
            logger.debug(f"Could not create relationship connection: {e}")
    
    logger.info(f"Created {len(all_card_ids)} total cards: 1 parent + {len(child_card_ids)} sections + {len(patterns)} patterns/examples")
    
    return {
        "parent_card_id": parent_card_id,
        "child_card_ids": child_card_ids,
        "all_card_ids": all_card_ids,
        "patterns_extracted": len(patterns),
        "examples_count": len(grouped["groups"]["examples"]),
        "patterns_count": len(grouped["groups"]["patterns"])
    }



@tool
def grow_card_content(card_id: str, canvas_id: str, num_concepts: int = 3, session_id: Optional[str] = None) -> dict:
    """
    Analyze a card's content and create connected child cards with key concepts.
    
    This is the "Grow" feature that expands a card by:
    1. Fetching the card content from the database
    2. Using LLM to extract key concepts
    3. Creating child cards for each concept
    4. Positioning them in a circular arrangement around the parent
    5. Creating connections between parent and children
    6. Tracks progress and emits real-time updates
    
    Args:
        card_id: The card to expand
        canvas_id: Canvas ID
        num_concepts: Number of concepts to extract (default 3, max 5)
        session_id: Optional session ID for SSE routing
        
    Returns:
        {
            "success": bool,
            "parent_card_id": str,
            "concepts": list[dict],
            "child_card_ids": list[str],
            "connections": list[str],
            "summary": str,
            "operation_id": str
        }
    """
    logger.info(f"Growing card {card_id} with {num_concepts} concepts")
    
    # Initialize progress tracker
    from progress import ProgressTracker
    
    tracker = ProgressTracker(
        operation_type="grow_card",
        total_steps=4,
        canvas_id=canvas_id,
        session_id=session_id
    )
    
    try:
        # Validate num_concepts
        num_concepts = max(1, min(num_concepts, 5))  # Clamp between 1 and 5
        
        # Step 1: Get card content (25%)
        tracker.update_progress("fetching_card", 0.25, f"Fetching card content...")
        
        card = get_card(card_id)
        
        if not card:
            tracker.fail("Card not found")
            return {
                "success": False,
                "error": f"Card {card_id} not found",
                "operation_id": tracker.operation_id
            }
        
        # Extract content
        card_title = card.get("title", "")
        card_content = card.get("content", "")
        
        if not card_content:
            tracker.fail("Card has no content")
            return {
                "success": False,
                "error": "Card has no content to analyze",
                "operation_id": tracker.operation_id
            }
        
        # Step 2: Analyze with LLM (50%)
        tracker.update_progress("analyzing", 0.5, f"Analyzing content with AI to extract {num_concepts} concepts...")
        
        from prompts import PromptTemplates
        prompt = PromptTemplates.grow_card_prompt(card_title, card_content, num_concepts)

        # 3. Call LLM to extract concepts
        from agents.model_provider import get_nvidia_nim_model
        
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # Parse JSON response
        try:
            from prompts import PromptFormatter
            concepts = PromptFormatter.parse_json_response(str(response))
            
            if not isinstance(concepts, list):
                raise ValueError("Response is not a JSON array")
                
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.error(f"Response was: {response}")
            tracker.fail("Failed to parse AI response")
            return {
                "success": False,
                "error": "Failed to extract concepts from content. The content might be too short or unclear.",
                "operation_id": tracker.operation_id
            }
        
        # Step 3: Create child cards (75%)
        tracker.update_progress("creating_cards", 0.75, f"Creating {len(concepts[:num_concepts])} concept cards...")
        
        child_card_ids = []
        connection_ids = []
        
        for i, concept in enumerate(concepts[:num_concepts]):  # Limit to requested number
            # Calculate position in circular arrangement
            child_x, child_y = calculate_child_position(
                parent_x=card["position_x"],
                parent_y=card["position_y"],
                child_index=i,
                total_children=len(concepts[:num_concepts]),
                radius=280
            )
            
            # Create child card
            child_card = create_card(
                canvas_id=canvas_id,
                title=concept.get("title", f"Concept {i+1}"),
                content=concept.get("description", ""),
                card_type="rich_text",
                position_x=child_x,
                position_y=child_y,
                parent_id=card_id,
                tags=[concept.get("category", "concept")]
            )
            
            child_card_ids.append(child_card["id"])
            
            # Create connection from parent to child
            connection = create_connection(
                canvas_id=canvas_id,
                source_id=card_id,
                target_id=child_card["id"],
                connection_type="parent-child"
            )
            
            connection_ids.append(connection["id"])
        
        # Track created cards
        tracker.add_cards_created(child_card_ids)
        
        # Step 4: Finalize (100%)
        tracker.update_progress("finalizing", 0.95, "Triggering background processing...")
        
        # Emit events for background processing
        for child_id in child_card_ids:
            canvas_events.emit(CanvasEvents.CARD_CREATED, {
                "card_id": child_id,
                "canvas_id": canvas_id,
                "source": "grow_feature",
                "parent_id": card_id
            })
        
        result = {
            "success": True,
            "parent_card_id": card_id,
            "concepts": concepts[:num_concepts],
            "child_card_ids": child_card_ids,
            "connections": connection_ids,
            "summary": f"Created {len(child_card_ids)} concept cards from '{card_title}'",
            "operation_id": tracker.operation_id
        }
        
        tracker.complete(f"Successfully created {len(child_card_ids)} concept cards")
        
        logger.info(f"Successfully grew card {card_id}: {len(child_card_ids)} concepts created")
        return result
        
    except Exception as e:
        logger.error(f"Error growing card {card_id}: {e}", exc_info=True)
        tracker.fail(str(e))
        return {
            "success": False,
            "error": str(e),
            "suggestion": "Try with a card that has more detailed content, or reduce the number of concepts.",
            "operation_id": tracker.operation_id
        }



@tool
def find_similar_cards(content: str, canvas_id: str, limit: int = 5, min_similarity: float = 0.3) -> dict:
    """
    Find cards with similar content using TF-IDF and cosine similarity.
    
    This tool helps with:
    - Finding related cards for intelligent placement
    - Suggesting parent cards for new content
    - Discovering connections between existing cards
    - Organizing canvas by semantic relationships
    
    Uses TF-IDF (Term Frequency-Inverse Document Frequency) vectorization
    and cosine similarity to measure semantic similarity between card content.
    
    Args:
        content: Content to compare against (can be from a new card or query)
        canvas_id: Canvas to search in
        limit: Maximum number of similar cards to return (default 5)
        min_similarity: Minimum similarity threshold 0-1 (default 0.3)
        
    Returns:
        {
            "success": bool,
            "similar_cards": list[dict],  # [{id, title, similarity_score, content_preview}]
            "suggested_parent": str | None,  # Card ID with highest similarity
            "total_cards_analyzed": int
        }
    """
    logger.info(f"Finding similar cards on canvas {canvas_id}")
    
    try:
        # Validate parameters
        limit = max(1, min(limit, 20))  # Clamp between 1 and 20
        min_similarity = max(0.0, min(min_similarity, 1.0))  # Clamp between 0 and 1
        
        # 1. Get all cards on canvas
        cards = get_canvas_cards(canvas_id)
        
        if not cards or len(cards) == 0:
            return {
                "success": True,
                "similar_cards": [],
                "suggested_parent": None,
                "total_cards_analyzed": 0,
                "message": "No cards found on canvas"
            }
        
        # 2. Prepare documents for TF-IDF
        # Combine title and content for better matching
        documents = [content]  # Query document first
        card_texts = []
        
        for card in cards:
            card_title = card.get("title", "")
            card_content = card.get("content", "")
            # Combine title (weighted more) and content
            combined_text = f"{card_title} {card_title} {card_content}"
            card_texts.append(combined_text)
            documents.append(combined_text)
        
        # Check if we have enough content
        if len(documents) < 2:
            return {
                "success": True,
                "similar_cards": [],
                "suggested_parent": None,
                "total_cards_analyzed": len(cards),
                "message": "Not enough cards with content to compare"
            }
        
        # 3. Calculate TF-IDF vectors
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=1000,  # Limit vocabulary size
                stop_words='english',  # Remove common English words
                ngram_range=(1, 2),  # Use unigrams and bigrams
                min_df=1,  # Minimum document frequency
                max_df=0.8  # Maximum document frequency (ignore very common terms)
            )
            
            # Fit and transform documents
            tfidf_matrix = vectorizer.fit_transform(documents)
            
            # 4. Calculate cosine similarity between query and all cards
            # First row is the query, rest are cards
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
        except ImportError:
            logger.error("sklearn not available - falling back to simple text matching")
            # Fallback: simple word overlap
            query_words = set(content.lower().split())
            similarities = []
            for card_text in card_texts:
                card_words = set(card_text.lower().split())
                if len(query_words) == 0 or len(card_words) == 0:
                    similarities.append(0.0)
                else:
                    overlap = len(query_words & card_words)
                    similarity = overlap / max(len(query_words), len(card_words))
                    similarities.append(similarity)
            similarities = [float(s) for s in similarities]
        
        # 5. Get top N similar cards above threshold
        similar_cards = []
        
        for i, similarity in enumerate(similarities):
            if similarity >= min_similarity:
                card = cards[i]
                similar_cards.append({
                    "id": card["id"],
                    "title": card.get("title", "Untitled"),
                    "similarity_score": round(float(similarity), 3),
                    "content_preview": card.get("content", "")[:100] + "..." if len(card.get("content", "")) > 100 else card.get("content", "")
                })
        
        # Sort by similarity (highest first)
        similar_cards.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Limit results
        similar_cards = similar_cards[:limit]
        
        # 6. Suggest parent (highest similarity)
        suggested_parent = similar_cards[0]["id"] if similar_cards else None
        
        result = {
            "success": True,
            "similar_cards": similar_cards,
            "suggested_parent": suggested_parent,
            "total_cards_analyzed": len(cards),
            "query_length": len(content),
            "threshold_used": min_similarity
        }
        
        logger.info(f"Found {len(similar_cards)} similar cards (analyzed {len(cards)} total)")
        return result
        
    except Exception as e:
        logger.error(f"Error finding similar cards: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "similar_cards": [],
            "suggested_parent": None
        }



@tool
def categorize_content(content: str, title: str = "") -> dict:
    """
    Automatically categorize content and suggest relevant tags using LLM.
    
    This tool helps with:
    - Auto-tagging new cards
    - Organizing canvas by categories
    - Detecting code languages
    - Suggesting relevant topics
    
    Uses LLM to analyze content and determine appropriate category and tags.
    Also detects programming languages if code is present.
    
    Args:
        content: Content to categorize
        title: Optional title for additional context
        
    Returns:
        {
            "success": bool,
            "category": str,  # e.g., "Programming", "Research", "Tutorial", "Reference"
            "tags": list[str],  # 2-3 specific tags
            "confidence": float,  # 0-1 confidence score
            "detected_language": str | None  # Programming language if code detected
        }
    """
    logger.info(f"Categorizing content: {title[:50] if title else 'Untitled'}")
    
    try:
        # Check if content is too short
        if len(content.strip()) < 10:
            return {
                "success": False,
                "error": "Content too short to categorize (minimum 10 characters)"
            }
        
        # 1. Detect code language if applicable
        detected_language = None
        if "```" in content or any(keyword in content for keyword in ["def ", "function ", "class ", "import ", "const ", "let ", "var "]):
            detected_language = _detect_code_language(content)
        
        # 2. Build LLM prompt for categorization
        from prompts import PromptTemplates
        prompt = PromptTemplates.categorize_content_prompt(content, title)

        # 3. Call LLM
        from agents.model_provider import get_nvidia_nim_model
        
        model = get_nvidia_nim_model()
        response = model(prompt)
        
        # 4. Parse JSON response
        try:
            from prompts import PromptFormatter
            result = PromptFormatter.parse_json_response(str(response))
            
            # Validate required fields
            if not PromptFormatter.validate_json_structure(result, ["category", "tags"]):
                raise ValueError("Missing required fields in response")
                
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Fallback categorization
            result = {
                "category": "General",
                "tags": ["uncategorized"],
                "confidence": 0.5
            }
        
        # 5. Add detected language as tag if found
        tags = result.get("tags", [])
        if detected_language and detected_language != "unknown":
            if detected_language not in tags:
                tags.insert(0, detected_language)
        
        # 6. Ensure confidence is in valid range
        confidence = float(result.get("confidence", 0.7))
        confidence = max(0.0, min(confidence, 1.0))
        
        final_result = {
            "success": True,
            "category": result.get("category", "General"),
            "tags": tags[:5],  # Limit to 5 tags
            "confidence": round(confidence, 2),
            "detected_language": detected_language
        }
        
        logger.info(f"Categorized as '{final_result['category']}' with tags: {final_result['tags']}")
        return final_result
        
    except Exception as e:
        logger.error(f"Error categorizing content: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "category": "General",
            "tags": [],
            "confidence": 0.0
        }


def _detect_code_language(content: str) -> str:
    """
    Detect programming language from code content.
    
    Args:
        content: Content that may contain code
        
    Returns:
        Language name (lowercase) or "unknown"
    """
    content_lower = content.lower()
    
    # Check for language-specific keywords and patterns
    if "def " in content and ("import " in content or "from " in content):
        return "python"
    elif ("function " in content or "const " in content or "let " in content) and ("=>" in content or "var " in content):
        return "javascript"
    elif "func " in content and ("package " in content or "import " in content):
        return "go"
    elif "#include" in content or "int main" in content:
        return "cpp"
    elif ("public class" in content or "private " in content) and ("void " in content or "static " in content):
        return "java"
    elif "fn " in content and ("let " in content or "mut " in content):
        return "rust"
    elif "<?php" in content:
        return "php"
    elif "SELECT " in content_lower and "FROM " in content_lower:
        return "sql"
    elif "<html" in content_lower or "<div" in content_lower:
        return "html"
    elif "interface " in content and "type " in content:
        return "typescript"
    else:
        return "unknown"



@tool
def detect_conflicts(canvas_id: str, duplicate_threshold: float = 0.9, conflict_threshold: float = 0.6) -> dict:
    """
    Detect duplicate or conflicting cards on the canvas.
    
    This tool helps with:
    - Finding duplicate cards (very similar content)
    - Detecting conflicts (same title, different content)
    - Maintaining canvas quality
    - Suggesting merge operations
    
    Uses similarity calculation to find duplicates and analyzes titles
    to detect potential conflicts.
    
    Args:
        canvas_id: Canvas to analyze
        duplicate_threshold: Similarity threshold for duplicates (default 0.9)
        conflict_threshold: Similarity threshold for conflicts (default 0.6)
        
    Returns:
        {
            "success": bool,
            "conflicts": list[dict],  # [{type, card_ids, severity, similarity, suggestion}]
            "duplicates": list[list[str]],  # Groups of duplicate card IDs
            "summary": dict  # Statistics
        }
    """
    logger.info(f"Detecting conflicts on canvas {canvas_id}")
    
    try:
        # Validate thresholds
        duplicate_threshold = max(0.5, min(duplicate_threshold, 1.0))
        conflict_threshold = max(0.3, min(conflict_threshold, 0.9))
        
        # 1. Get all cards on canvas
        cards = get_canvas_cards(canvas_id)
        
        if not cards or len(cards) < 2:
            return {
                "success": True,
                "conflicts": [],
                "duplicates": [],
                "summary": {
                    "total_cards": len(cards) if cards else 0,
                    "total_conflicts": 0,
                    "duplicates": 0,
                    "conflicting_info": 0
                },
                "message": "Not enough cards to detect conflicts (need at least 2)"
            }
        
        # 2. Prepare card data
        card_data = []
        for card in cards:
            card_data.append({
                "id": card["id"],
                "title": card.get("title", "").strip(),
                "content": card.get("content", "").strip(),
                "combined": f"{card.get('title', '')} {card.get('content', '')}"
            })
        
        # 3. Calculate pairwise similarity
        conflicts = []
        duplicates = []
        seen_pairs = set()
        
        for i, card_a in enumerate(card_data):
            for j, card_b in enumerate(card_data[i+1:], start=i+1):
                # Skip if already processed
                pair_key = tuple(sorted([card_a["id"], card_b["id"]]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                
                # Calculate similarity
                similarity = _calculate_text_similarity(card_a["combined"], card_b["combined"])
                
                # Check for duplicates (high similarity)
                if similarity >= duplicate_threshold:
                    duplicates.append([card_a["id"], card_b["id"]])
                    conflicts.append({
                        "type": "duplicate",
                        "card_ids": [card_a["id"], card_b["id"]],
                        "card_titles": [card_a["title"], card_b["title"]],
                        "severity": "medium",
                        "similarity": round(similarity, 3),
                        "suggestion": "These cards contain nearly identical information. Consider merging them to reduce redundancy."
                    })
                
                # Check for conflicts (same/similar title but different content)
                elif card_a["title"] and card_b["title"]:
                    title_similarity = _calculate_text_similarity(card_a["title"], card_b["title"])
                    
                    if title_similarity > 0.8 and similarity < conflict_threshold:
                        conflicts.append({
                            "type": "conflicting_info",
                            "card_ids": [card_a["id"], card_b["id"]],
                            "card_titles": [card_a["title"], card_b["title"]],
                            "severity": "high",
                            "similarity": round(similarity, 3),
                            "title_similarity": round(title_similarity, 3),
                            "suggestion": "These cards have similar titles but different content. Review for conflicting or complementary information."
                        })
        
        # 4. Calculate summary statistics
        summary = {
            "total_cards": len(cards),
            "total_conflicts": len(conflicts),
            "duplicates": len([c for c in conflicts if c["type"] == "duplicate"]),
            "conflicting_info": len([c for c in conflicts if c["type"] == "conflicting_info"]),
            "duplicate_threshold": duplicate_threshold,
            "conflict_threshold": conflict_threshold
        }
        
        result = {
            "success": True,
            "conflicts": conflicts,
            "duplicates": duplicates,
            "summary": summary
        }
        
        logger.info(f"Detected {len(conflicts)} conflicts: {summary['duplicates']} duplicates, {summary['conflicting_info']} conflicts")
        return result
        
    except Exception as e:
        logger.error(f"Error detecting conflicts: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "conflicts": [],
            "duplicates": [],
            "summary": {}
        }


def _calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using simple word overlap.
    
    This is a fallback method that doesn't require sklearn.
    For better results, use TF-IDF from find_similar_cards.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if len(words1) == 0 or len(words2) == 0:
        return 0.0
    
    # Calculate Jaccard similarity (intersection over union)
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    if union == 0:
        return 0.0
    
    return intersection / union



@tool
def merge_cards(
    card1_id: str,
    card2_id: str,
    canvas_id: str,
    merge_strategy: str = "combine"
) -> dict:
    """
    Merge two cards into one, combining their content and sources.
    
    This tool handles conflict resolution by merging duplicate or related cards.
    
    Args:
        card1_id: ID of first card (will be kept)
        card2_id: ID of second card (will be deleted after merge)
        canvas_id: Canvas ID
        merge_strategy: How to merge ("combine", "keep_first", "keep_second")
        
    Returns:
        {
            "success": bool,
            "merged_card_id": str,
            "deleted_card_id": str,
            "merge_summary": str
        }
    """
    logger.info(f"Merging cards {card1_id} and {card2_id} on canvas {canvas_id}")
    
    try:
        from graph.content_merger import ContentMerger
        from datetime import datetime
        
        # 1. Get both cards
        card1 = get_card(card1_id)
        card2 = get_card(card2_id)
        
        if not card1 or not card2:
            return {
                "success": False,
                "error": "One or both cards not found"
            }
        
        # 2. Prepare source info for card2
        source_info = {
            "url": card2.get("source_url", ""),
            "type": card2.get("source_type", "manual"),
            "extracted_at": card2.get("extracted_at", datetime.now().isoformat())
        }
        
        # 3. Merge content based on strategy
        merger = ContentMerger()
        
        if merge_strategy == "keep_first":
            # Keep card1 as is, just add card2's source
            merged_content = card1.get("content", "")
            merged_title = card1.get("title", "")
            sources = card1.get("sources", [])
            if source_info["url"]:
                sources.append(source_info)
        elif merge_strategy == "keep_second":
            # Use card2's content, but keep card1's ID
            merged_content = card2.get("content", "")
            merged_title = card2.get("title", "")
            sources = card2.get("sources", [])
            if card1.get("source_url"):
                sources.insert(0, {
                    "url": card1.get("source_url", ""),
                    "type": card1.get("source_type", "manual"),
                    "extracted_at": card1.get("extracted_at", datetime.now().isoformat())
                })
        else:  # combine
            # Intelligently merge content
            new_content = {
                "title": card2.get("title", ""),
                "description": card2.get("content", "")
            }
            
            merge_result = merger.merge_content(card1, new_content, source_info)
            merged_content = merge_result["merged_content"]
            merged_title = merge_result["merged_title"]
            sources = merge_result["sources"]
        
        # 4. Update card1 with merged content
        update_payload = {
            "title": merged_title,
            "content": merged_content,
            "sources": sources,
            "has_conflict": False  # Resolve conflict flag
        }
        
        # Update via API
        import requests
        response = requests.put(
            f"http://localhost:3000/api/nodes/{card1_id}",
            json=update_payload,
            timeout=10
        )
        response.raise_for_status()
        
        # 5. Transfer connections from card2 to card1
        # Get all connections involving card2
        connections_response = requests.get(
            f"http://localhost:3000/api/connections",
            params={"canvas_id": canvas_id},
            timeout=10
        )
        connections_response.raise_for_status()
        all_connections = connections_response.json()
        
        card2_connections = [
            conn for conn in all_connections
            if conn["source_id"] == card2_id or conn["target_id"] == card2_id
        ]
        
        # Create new connections pointing to card1
        for conn in card2_connections:
            new_source = card1_id if conn["source_id"] == card2_id else conn["source_id"]
            new_target = card1_id if conn["target_id"] == card2_id else conn["target_id"]
            
            # Skip self-connections
            if new_source == new_target:
                continue
            
            # Create new connection
            try:
                create_connection(
                    canvas_id=canvas_id,
                    source_id=new_source,
                    target_id=new_target,
                    connection_type=conn.get("type", "default")
                )
            except Exception as e:
                logger.warning(f"Could not transfer connection: {e}")
        
        # 6. Delete card2
        delete_response = requests.delete(
            f"http://localhost:3000/api/nodes/{card2_id}",
            timeout=10
        )
        delete_response.raise_for_status()
        
        merge_summary = f"Merged '{card2.get('title')}' into '{card1.get('title')}' using {merge_strategy} strategy"
        
        logger.info(f"Successfully merged cards: {merge_summary}")
        
        return {
            "success": True,
            "merged_card_id": card1_id,
            "deleted_card_id": card2_id,
            "merge_summary": merge_summary,
            "sources_count": len(sources)
        }
        
    except Exception as e:
        logger.error(f"Error merging cards: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "suggestion": "Check that both cards exist and try again"
        }


@tool
def get_merge_preview(card1_id: str, card2_id: str) -> dict:
    """
    Get a preview of what merged content would look like without actually merging.
    
    Args:
        card1_id: ID of first card
        card2_id: ID of second card
        
    Returns:
        {
            "success": bool,
            "preview": dict with merged content preview
        }
    """
    logger.info(f"Generating merge preview for cards {card1_id} and {card2_id}")
    
    try:
        from graph.content_merger import ContentMerger
        
        # Get both cards
        card1 = get_card(card1_id)
        card2 = get_card(card2_id)
        
        if not card1 or not card2:
            return {
                "success": False,
                "error": "One or both cards not found"
            }
        
        # Generate preview
        merger = ContentMerger()
        preview = merger.get_merge_preview(card1, card2)
        
        return {
            "success": True,
            "preview": preview
        }
        
    except Exception as e:
        logger.error(f"Error generating merge preview: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
