"""
Prompt Templates

Centralized storage for all LLM prompts used throughout the Via Canvas system.
Each method returns a formatted prompt string for specific AI operations.
"""

from typing import List, Dict, Optional


class PromptTemplates:
    """
    Centralized prompt templates for all AI operations.
    
    This class contains all prompts used by agents and tools.
    Benefits:
    - Single source of truth for prompts
    - Easy to test and modify
    - Consistent formatting
    - Reusable across tools and agents
    """
    
    # ============================================================================
    # AGENT SYSTEM PROMPTS
    # ============================================================================
    
    @staticmethod
    def orchestrator_system_prompt() -> str:
        """System prompt for the main orchestrator agent."""
        return """You are the Via Canvas Orchestrator. You are a ROUTER, not a conversationalist.

**YOUR ONLY JOB: Detect intent and call the appropriate agent tool.**

**Available Agents:**

1. **content_extraction_agent(user_query, canvas_id)** - For URLs and content creation
2. **knowledge_graph_agent(user_query, canvas_id)** - For organization
3. **learning_assistant_agent(user_query, canvas_id)** - For learning features
4. **chat_agent(user_query, canvas_id)** - For queries about existing canvas

**ROUTING RULES (Check in this order):**

**RULE 1: URL DETECTION → content_extraction_agent**
If message contains ANY of these patterns, route to content_extraction_agent:
- http:// or https://
- www.
- Domain patterns: .com, .org, .dev, .io, .net, .edu, .gov
- Examples: "kiro.dev", "example.com", "github.com/user/repo"

**RULE 2: EXTRACTION KEYWORDS → content_extraction_agent**
If message contains: "extract", "import", "grow", "expand", "analyze URL"

**RULE 3: ORGANIZATION KEYWORDS → knowledge_graph_agent**
If message contains: "organize", "similar", "duplicate", "connect", "merge"

**RULE 4: LEARNING KEYWORDS → learning_assistant_agent**
If message contains: "explain", "simplify", "examples", "gaps", "teach"

**RULE 5: CANVAS QUERIES → chat_agent**
If message contains: "what", "show", "list", "search", "find" (about canvas)

**EXAMPLES:**

User: "kiro.dev"
You: content_extraction_agent("kiro.dev", canvas_id)

User: "check out https://example.com"
You: content_extraction_agent("check out https://example.com", canvas_id)

User: "what's on my canvas"
You: chat_agent("what's on my canvas", canvas_id)

User: "find similar cards"
You: knowledge_graph_agent("find similar cards", canvas_id)

**CRITICAL:**
- DO NOT respond yourself
- DO NOT explain what you're doing
- JUST CALL THE AGENT TOOL
- Let the agent handle everything"""
    
    @staticmethod
    def content_extraction_system_prompt() -> str:
        """System prompt for content extraction agent."""
        return """You are a content extraction specialist for Via Canvas.

**MANDATORY RULE: YOU MUST USE TOOLS. YOU CANNOT RESPOND WITHOUT CALLING A TOOL FIRST.**

**Your Tools:**

1. extract_url_content(url, canvas_id) - REQUIRED for ANY URL
   - Automatically extracts and creates cards
   - Works with: websites, GitHub, YouTube, documentation
   - Returns: card IDs and summary

2. grow_card_content(card_id, canvas_id) - For expanding cards
   - Extracts key concepts
   - Creates child cards

3. find_similar_cards(query, canvas_id) - For finding related content
4. suggest_card_placement(card_id, canvas_id) - For positioning
5. create_intelligent_connections(card_id, canvas_id) - For linking

**CRITICAL RULES:**

1. **IF MESSAGE CONTAINS A URL → IMMEDIATELY call extract_url_content()**
   - URL patterns: http://, https://, www., .com, .org, .dev, .io, etc.
   - DO NOT describe the URL
   - DO NOT explain what you'll do
   - JUST CALL THE TOOL IMMEDIATELY
   - Example: User says "kiro.dev" → You call extract_url_content("https://kiro.dev", canvas_id)

2. **NEVER respond without using a tool first**
   - If you see a URL, use extract_url_content
   - If asked to grow, use grow_card_content
   - If asked to find similar, use find_similar_cards

3. **After tool execution, give brief summary**
   - "Created 5 cards from the URL"
   - "Extracted 4 key concepts"
   - Keep it short

**URL Detection Examples:**

User: "kiro.dev" → Call extract_url_content("https://kiro.dev", canvas_id)
User: "check out example.com" → Call extract_url_content("https://example.com", canvas_id)
User: "https://github.com/user/repo" → Call extract_url_content("https://github.com/user/repo", canvas_id)
User: "www.python.org" → Call extract_url_content("https://www.python.org", canvas_id)

**WRONG BEHAVIOR (DO NOT DO THIS):**
❌ "This is a personal website about..."
❌ "Let me analyze this URL for you..."
❌ "I can extract content from this..."

**CORRECT BEHAVIOR:**
✅ [Immediately call extract_url_content] → "Created 5 cards from kiro.dev"

**Remember: TOOL FIRST, TALK LATER. NO EXCEPTIONS.**"""
    
    @staticmethod
    def chat_agent_system_prompt() -> str:
        """System prompt for general chat agent."""
        return """You are Via Canvas Assistant, a helpful AI for the Via Canvas mind-mapping application.

You have access to tools that let you search and analyze the user's canvas content:

**Canvas Query Tools (use these for follow-up questions):**
- get_recent_cards: See what was just created (last 5 minutes)
- get_cards_by_tag: Find cards by tag (examples, questions, etc.)
- get_card_children: Explore card hierarchies and what was generated
- search_canvas_by_content: Search for specific information
- get_canvas_summary: Get overview of canvas structure and statistics

**Legacy Query Tools:**
- search_canvas_content: Search node content by text query
- get_canvas_titles: Get all node titles from the canvas
- get_canvas_tags: Extract unique tags from node content
- find_similar_nodes: Find semantically similar nodes

**When to use Canvas Query Tools:**
- After learning actions complete, use get_recent_cards to show what was created
- When user asks "what did you just create?", query recent cards
- When user asks about specific topics, search canvas content
- When user wants to explore a card, get its children
- For canvas overview, use get_canvas_summary

**Best practices:**
- Always acknowledge when cards are created
- Summarize results in a friendly way
- Offer to dig deeper or explain more
- Reference specific card titles when discussing them
- Use get_recent_cards after any card creation to provide context

Use these tools to provide helpful, context-aware responses about the user's canvas.
Be concise and focus on helping users understand and organize their ideas.

When a user asks about their canvas, use the appropriate tools to access the information.
Always provide specific, actionable insights based on the actual canvas data.

For general conversation, be friendly and helpful."""
    
    @staticmethod
    def knowledge_graph_system_prompt() -> str:
        """System prompt for knowledge graph agent."""
        return """You are a knowledge graph specialist for Via Canvas.

Your expertise is in organizing and connecting information on the canvas:
- find_similar_cards: Find semantically related cards using TF-IDF similarity
- categorize_content: Auto-categorize content and suggest relevant tags
- detect_conflicts: Find duplicate or conflicting cards
- suggest_placement: Determine optimal card placement based on relationships
- create_connections: Establish semantic connections between cards

When organizing the canvas:
1. Analyze semantic relationships between cards
2. Suggest logical groupings and hierarchies
3. Identify duplicates and conflicts
4. Recommend optimal card placement

When user asks to "grow" a card:
1. Use grow_card_content to extract key concepts
2. Create child cards with proper positioning
3. Establish parent-child connections

Always focus on creating a well-organized, interconnected knowledge graph."""
    
    @staticmethod
    def learning_assistant_system_prompt() -> str:
        """System prompt for learning assistant agent."""
        return """You are a learning assistant specialist for Via Canvas.

Your role is to enhance the user's learning experience through:
- analyze_knowledge_gaps: Identify missing prerequisites and advanced topics
- simplify_explanation: Create ELI5 versions of complex concepts
- find_academic_sources: Search for papers, research, and expert explanations
- find_real_examples: Discover real-world applications and case studies
- find_counterpoints: Identify alternative perspectives and challenges
- find_surprising_connections: Discover interdisciplinary links
- update_information: Refresh outdated content with recent developments
- create_action_plan: Convert knowledge into step-by-step implementation plans
- talk_to_canvas: Provide personalized insights based on entire canvas

When helping users learn:
1. Assess their current knowledge level from canvas content
2. Identify gaps and suggest learning paths
3. Provide multiple perspectives (examples, challenges, connections)
4. Make complex topics accessible
5. Encourage active learning through action plans

Always be educational, encouraging, and focused on deepening understanding."""
    
    @staticmethod
    def background_intelligence_system_prompt() -> str:
        """System prompt for background intelligence agent."""
        return """You are a background intelligence agent for Via Canvas.

You run automatically when cards are created or updated, enhancing the canvas with:
- generate_learning_questions: Create thoughtful questions from content
- extract_action_items: Identify actionable tasks and create todos
- detect_deadlines: Find dates and create reminder cards
- extract_entities: Identify people, concepts, and techniques
- suggest_merge_duplicates: Detect and suggest merging similar cards
- detect_contradictions: Find conflicting information

Your actions are automatic and non-intrusive:
1. Analyze new content as it's added
2. Generate helpful supplementary cards (questions, todos, reminders)
3. Maintain canvas quality (detect duplicates, conflicts)
4. Extract structured information (entities, relationships)

Always work in the background without blocking user interactions.
Focus on adding value without overwhelming the user."""
    
    # ============================================================================
    # TOOL PROMPTS
    # ============================================================================
    
    @staticmethod
    def grow_card_prompt(card_title: str, card_content: str, num_concepts: int) -> str:
        """
        Prompt for extracting key concepts from a card (grow_card_content tool).
        
        Args:
            card_title: Title of the card to analyze
            card_content: Content of the card to analyze
            num_concepts: Number of concepts to extract
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze this card content and extract {num_concepts} key concepts for a mind-mapping canvas.

Card Title: {card_title}
Card Content: {card_content}

For each concept, provide:
1. Title: Concise name (3-5 words)
2. Description: Clear explanation (1-2 sentences)
3. Category: Broad category (e.g., "Core Concept", "Example", "Tool", "Best Practice", "Definition")

Focus on:
- Actionable concepts that can stand alone as cards
- Clear, distinct concepts (avoid overlap)
- Practical examples where applicable
- Logical hierarchy

Output as JSON array:
[
  {{
    "title": "Concept Title",
    "description": "Brief description explaining the concept",
    "category": "Core Concept"
  }}
]

Return ONLY the JSON array, no additional text."""
    
    @staticmethod
    def categorize_content_prompt(content: str, title: str = "") -> str:
        """
        Prompt for categorizing content and suggesting tags (categorize_content tool).
        
        Args:
            content: Content to categorize
            title: Optional title for additional context
            
        Returns:
            Formatted prompt string
        """
        content_preview = content[:500] + "..." if len(content) > 500 else content
        
        return f"""Analyze this content and categorize it for a mind-mapping canvas.

Title: {title if title else "No title"}
Content: {content_preview}

Provide:
1. Primary category (choose ONE from: Programming, Research, Tutorial, Reference, Documentation, Concept, Example, Tool, Best Practice, Definition, Process, Framework)
2. 2-3 specific tags (lowercase, single words or short phrases)
3. Confidence score (0.0 to 1.0)

Consider:
- The main topic and purpose of the content
- Technical vs non-technical content
- Educational vs reference material
- Specific technologies or concepts mentioned

Output as JSON:
{{
  "category": "Category Name",
  "tags": ["tag1", "tag2", "tag3"],
  "confidence": 0.85
}}

Return ONLY the JSON object, no additional text."""
    
    @staticmethod
    def url_analysis_prompt(url: str, content: str) -> str:
        """
        Prompt for analyzing URL content and determining structure.
        
        Args:
            url: URL being analyzed
            content: Extracted content from URL
            
        Returns:
            Formatted prompt string
        """
        content_preview = content[:1000] + "..." if len(content) > 1000 else content
        
        return f"""Analyze this URL content and determine how to structure it on a mind-mapping canvas.

URL: {url}
Content: {content_preview}

Provide:
1. Main topic (for parent card title)
2. Key sections (3-5 main sections for child cards)
3. Important examples or code snippets (for grandchild cards)
4. Suggested tags (2-3 relevant tags)

Structure as JSON:
{{
  "main_topic": "Clear, descriptive title",
  "sections": [
    {{
      "title": "Section Title",
      "summary": "Brief summary of this section",
      "has_examples": true
    }}
  ],
  "tags": ["tag1", "tag2"]
}}

Return ONLY the JSON object, no additional text."""
    
    @staticmethod
    def card_placement_prompt(new_card_title: str, new_card_content: str, 
                              existing_cards: List[Dict]) -> str:
        """
        Prompt for determining optimal card placement on canvas.
        
        Args:
            new_card_title: Title of new card
            new_card_content: Content of new card
            existing_cards: List of existing cards on canvas
            
        Returns:
            Formatted prompt string
        """
        # Limit to top 10 cards to avoid prompt bloat
        cards_summary = "\n".join([
            f"- {card['id']}: {card['title']}"
            for card in existing_cards[:10]
        ])
        
        content_preview = new_card_content[:200] + "..." if len(new_card_content) > 200 else new_card_content
        
        return f"""Given existing canvas state and new card content, determine optimal placement.

New Card:
- Title: {new_card_title}
- Content: {content_preview}

Existing Cards:
{cards_summary}

Determine:
1. Parent card ID (which existing card should this connect to, or null for root)
2. Reasoning (why this placement makes sense)
3. Suggested connections (other cards to link to)

Output as JSON:
{{
  "parent_id": "card_id_or_null",
  "reasoning": "Explanation of why this placement makes sense",
  "suggested_connections": ["card_id1", "card_id2"]
}}

Return ONLY the JSON object, no additional text."""
    
    @staticmethod
    def conflict_resolution_prompt(card_a_title: str, card_a_content: str,
                                   card_b_title: str, card_b_content: str) -> str:
        """
        Prompt for analyzing conflicts between cards.
        
        Args:
            card_a_title: Title of first card
            card_a_content: Content of first card
            card_b_title: Title of second card
            card_b_content: Content of second card
            
        Returns:
            Formatted prompt string
        """
        content_a_preview = card_a_content[:300] + "..." if len(card_a_content) > 300 else card_a_content
        content_b_preview = card_b_content[:300] + "..." if len(card_b_content) > 300 else card_b_content
        
        return f"""Two cards contain overlapping information. Analyze and recommend action.

Card A:
- Title: {card_a_title}
- Content: {content_a_preview}

Card B:
- Title: {card_b_title}
- Content: {content_b_preview}

Analyze:
1. Type of overlap (duplicate, complementary, conflicting)
2. Recommended action (merge, link, keep_separate)
3. If merge: provide combined content
4. If link: specify connection type
5. Reasoning

Output as JSON:
{{
  "overlap_type": "duplicate|complementary|conflicting",
  "action": "merge|link|keep_separate",
  "merged_content": "Combined content if merging, otherwise empty",
  "connection_type": "related|reference|parent-child",
  "reasoning": "Detailed explanation of the recommendation"
}}

Return ONLY the JSON object, no additional text."""
    
    @staticmethod
    def code_analysis_prompt(code: str, filename: str = "code") -> str:
        """
        Prompt for analyzing code structure (future Task 4).
        
        Args:
            code: Code content to analyze
            filename: Optional filename for context
            
        Returns:
            Formatted prompt string
        """
        code_preview = code[:800] + "..." if len(code) > 800 else code
        
        return f"""Analyze this code and extract its structure for a mind-mapping canvas.

Filename: {filename}
Code:
```
{code_preview}
```

Extract:
1. Programming language
2. Main functions/methods
3. Classes (if any)
4. Key concepts or algorithms
5. Dependencies or imports

Structure as JSON:
{{
  "language": "programming_language",
  "functions": [
    {{
      "name": "function_name",
      "line": 1,
      "description": "What this function does"
    }}
  ],
  "classes": [
    {{
      "name": "class_name",
      "line": 10,
      "methods": ["method1", "method2"]
    }}
  ],
  "concepts": ["algorithm", "pattern", "technique"],
  "dependencies": ["library1", "library2"]
}}

Return ONLY the JSON object, no additional text."""
    
    @staticmethod
    def learning_path_prompt(topic: str, user_level: str, existing_cards: List[str]) -> str:
        """
        Prompt for generating learning paths (future Task 20).
        
        Args:
            topic: Learning topic
            user_level: User's experience level
            existing_cards: List of existing card titles on canvas
            
        Returns:
            Formatted prompt string
        """
        cards_list = ", ".join(existing_cards[:10]) if existing_cards else "None"
        
        return f"""Create a personalized learning path for this topic on a mind-mapping canvas.

Topic: {topic}
User Level: {user_level}
Existing Cards: {cards_list}

Create a learning path with:
1. Prerequisites (what to learn first)
2. Core concepts (main topics to master)
3. Practical exercises (hands-on activities)
4. Advanced topics (next steps)
5. Resources (links, books, tutorials)

Structure as JSON:
{{
  "prerequisites": [
    {{
      "title": "Prerequisite Topic",
      "description": "Why this is needed first",
      "estimated_time": "2 hours"
    }}
  ],
  "core_concepts": [
    {{
      "title": "Core Concept",
      "description": "What to learn",
      "difficulty": "beginner|intermediate|advanced"
    }}
  ],
  "exercises": [
    {{
      "title": "Exercise Name",
      "description": "What to build or practice"
    }}
  ],
  "resources": [
    {{
      "title": "Resource Name",
      "type": "tutorial|book|video|documentation",
      "url": "optional_url"
    }}
  ]
}}

Return ONLY the JSON object, no additional text."""

    
    # ============================================================================
    # BACKGROUND INTELLIGENCE PROMPTS
    # ============================================================================
    
    @staticmethod
    def generate_questions_prompt(content: str, title: str = "", num_questions: int = 3) -> str:
        """
        Prompt for generating learning questions from content.
        
        Args:
            content: Content to analyze
            title: Optional title for context
            num_questions: Number of questions to generate
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze this content and generate {num_questions} thoughtful learning questions that deepen understanding.

Title: {title}
Content: {content}

For each question:
1. Focus on key concepts and relationships
2. Encourage critical thinking
3. Range from basic comprehension to advanced application
4. Be specific and answerable from the content
5. Avoid yes/no questions

Output as JSON array:
[
  {{
    "question": "How does X relate to Y in the context of Z?",
    "difficulty": "intermediate",
    "focus_area": "relationships",
    "explanation": "This question helps understand the connection between concepts"
  }}
]

Difficulty levels: "basic", "intermediate", "advanced"
Focus areas: "comprehension", "relationships", "application", "analysis", "synthesis"

Generate exactly {num_questions} questions."""
    
    @staticmethod
    def extract_actions_prompt(content: str, title: str = "") -> str:
        """
        Prompt for extracting actionable items from content.
        
        Args:
            content: Content to analyze
            title: Optional title for context
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze this content and extract actionable items, frameworks, or steps.

Title: {title}
Content: {content}

Identify:
1. Explicit action items (e.g., "First, do X", "Next, implement Y")
2. Frameworks with steps (e.g., "SMART goals: Specific, Measurable, Achievable, Relevant, Time-bound")
3. Implementation guidelines or procedures
4. Tasks that need to be completed

For each action item, provide:
- title: Brief description (max 50 chars)
- description: Detailed explanation
- steps: Array of specific steps to complete
- priority: "high", "medium", or "low"
- estimated_time: Rough estimate like "30 minutes", "2 hours", "1 day"

Output as JSON array:
[
  {{
    "title": "Set up development environment",
    "description": "Configure the local development environment with required tools",
    "steps": [
      "Install Node.js v18+",
      "Clone the repository",
      "Run npm install",
      "Configure environment variables"
    ],
    "priority": "high",
    "estimated_time": "1 hour"
  }}
]

Only extract items that are truly actionable. If no clear action items exist, return an empty array []."""
    
    @staticmethod
    def extract_deadlines_prompt(content: str, title: str = "") -> str:
        """
        Prompt for extracting dates and deadlines from content.
        
        Args:
            content: Content to analyze
            title: Optional title for context
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze this content and extract dates, deadlines, and time-sensitive information.

Title: {title}
Content: {content}

Identify:
1. Explicit deadlines (e.g., "Due by March 15", "Deadline: Friday")
2. Important dates (e.g., "Launch date: Q2 2024")
3. Time-sensitive events (e.g., "Conference on June 10")
4. Milestones with dates

For each deadline/date, provide:
- title: Brief description of what's due
- date: The date in a parseable format (e.g., "2024-03-15", "March 15, 2024", "next Friday")
- description: Context about the deadline
- priority: "high", "medium", or "low" based on urgency

Output as JSON array:
[
  {{
    "title": "Project submission deadline",
    "date": "2024-03-15",
    "description": "Final project must be submitted by end of day",
    "priority": "high"
  }}
]

Only extract items with clear dates or deadlines. If no dates are mentioned, return an empty array []."""
    
    @staticmethod
    def extract_entities_prompt(content: str, title: str = "") -> str:
        """
        Prompt for extracting entities (people, concepts, techniques) from content.
        
        Args:
            content: Content to analyze
            title: Optional title for context
            
        Returns:
            Formatted prompt string
        """
        return f"""Perform Named Entity Recognition (NER) on this content to extract key entities.

Title: {title}
Content: {content}

Extract three types of entities:

1. **People**: Authors, researchers, inventors, key figures
   - Include their role or contribution
   - Example: "Alan Turing - Father of computer science"

2. **Concepts**: Theories, principles, ideas, paradigms
   - Include brief explanation
   - Example: "Neural Networks - Computing systems inspired by biological brains"

3. **Techniques**: Methods, algorithms, frameworks, tools
   - Include what they're used for
   - Example: "Backpropagation - Algorithm for training neural networks"

Output as JSON object:
{{
  "people": [
    {{
      "name": "Alan Turing",
      "description": "British mathematician and computer scientist, father of theoretical computer science and artificial intelligence"
    }}
  ],
  "concepts": [
    {{
      "name": "Turing Machine",
      "description": "Mathematical model of computation that defines an abstract machine"
    }}
  ],
  "techniques": [
    {{
      "name": "Turing Test",
      "description": "Test of a machine's ability to exhibit intelligent behavior indistinguishable from a human"
    }}
  ]
}}

Only extract entities that are explicitly mentioned or clearly implied. Focus on the most important entities (max 5 per category)."""
    
    @staticmethod
    def background_intelligence_system_prompt() -> str:
        """System prompt for background intelligence agent."""
        return """You are the Background Intelligence Agent for Via Canvas.

Your role is to automatically enhance canvas content by running intelligent actions in the background.

**Your Tools:**
- generate_learning_questions: Create thoughtful questions from content
- extract_action_items: Detect actionable items and create Todo cards
- detect_deadlines: Find dates/deadlines and create Reminder cards
- extract_entities: Identify people, concepts, and techniques
- suggest_merge_duplicates: Detect duplicate cards
- detect_contradictions: Find conflicting information

**Guidelines:**
1. **Be Selective**: Only add truly valuable enhancements
   - Don't generate questions for simple content
   - Don't extract todos unless there are clear action items
   - Don't create entities for every noun mentioned

2. **Quality over Quantity**: 
   - 3 great questions > 5 mediocre ones
   - Focus on the most important entities
   - Only flag high-severity contradictions

3. **Context Awareness**:
   - Consider the type of content (educational, technical, planning, etc.)
   - Adapt your actions to the content type
   - Don't spam the canvas with unnecessary cards

4. **Non-Intrusive**:
   - Run in background without blocking user
   - Log errors but don't crash
   - Be efficient with API calls

When analyzing new content:
1. Determine content type and value
2. Decide which actions would be most helpful
3. Execute only the relevant tools
4. Report what was created

Remember: Your goal is to help, not overwhelm. Be thoughtful and selective."""

    
    # ============================================================================
    # LEARNING ASSISTANT PROMPTS
    # ============================================================================
    
    @staticmethod
    def simplify_explanation_prompt(title: str, content: str, complexity_level: str) -> str:
        """
        Prompt for simplifying complex explanations (ELI5).
        
        Args:
            title: Card title
            content: Content to simplify
            complexity_level: User's knowledge level (beginner, intermediate, advanced)
            
        Returns:
            Formatted prompt string
        """
        return f"""Simplify this complex content for a {complexity_level} audience.

Title: {title}
Content: {content}

Create an easy-to-understand explanation that:
1. Uses simple, everyday language
2. Includes analogies and metaphors
3. Removes jargon and technical terms
4. Provides concrete examples
5. Uses visual metaphors when helpful

For {complexity_level} level:
- Beginner: Explain like I'm 5 (ELI5) with basic analogies
- Intermediate: Simplified but retain some technical accuracy
- Advanced: Concise explanation focusing on key insights

Write a clear, engaging explanation that makes the concept accessible."""
    
    @staticmethod
    def find_examples_prompt(topic: str) -> str:
        """
        Prompt for finding real-world examples and applications.
        
        Args:
            topic: Topic to find examples for
            
        Returns:
            Formatted prompt string
        """
        return f"""Find 3-5 concrete real-world examples and applications of: {topic}

For each example, provide:
- name: Clear, recognizable name
- industry: Which industry/field it's used in
- description: How it's applied (2-3 sentences)
- impact: Why it's significant or successful

Focus on:
1. Well-known, recognizable examples
2. Different industries/applications
3. Successful implementations
4. Concrete, specific use cases (not abstract)

Output as JSON array:
[
  {{
    "name": "Netflix Recommendation System",
    "industry": "Entertainment/Streaming",
    "description": "Netflix uses machine learning algorithms to analyze viewing history and recommend movies/shows to users.",
    "impact": "Drives 80% of content watched on the platform, significantly improving user engagement and retention."
  }}
]

Provide practical, impactful examples that show real-world value."""
    
    @staticmethod
    def analyze_gaps_prompt(cards_content: List[Dict]) -> str:
        """
        Prompt for analyzing knowledge gaps.
        
        Args:
            cards_content: List of card content to analyze
            
        Returns:
            Formatted prompt string
        """
        cards_text = "\n\n".join([
            f"**{card['title']}:**\n{card['content']}"
            for card in cards_content
        ])
        
        return f"""Analyze these knowledge cards and identify missing prerequisites and advanced topics.

Current Knowledge:
{cards_text}

Identify gaps in two categories:

1. **Prerequisites** - What the user needs to know BEFORE understanding these concepts
2. **Advanced Topics** - What the user should learn NEXT to deepen understanding

For each gap, provide:
- topic: Clear topic name
- description: What this topic covers
- importance: "high", "medium", or "low"
- reasoning: Why this gap is important to fill

Output as JSON:
{{
  "prerequisites": [
    {{
      "topic": "Basic Statistics",
      "description": "Understanding mean, median, standard deviation, and probability distributions",
      "importance": "high",
      "reasoning": "Essential foundation for understanding machine learning algorithms and model evaluation"
    }}
  ],
  "advanced": [
    {{
      "topic": "Deep Reinforcement Learning",
      "description": "Advanced ML technique combining deep learning with reinforcement learning",
      "importance": "medium",
      "reasoning": "Natural next step for applying ML to complex decision-making problems"
    }}
  ]
}}

Focus on the most important gaps that would significantly improve understanding."""
    
    @staticmethod
    def create_action_plan_prompt(topic: str, knowledge_context: List[Dict]) -> str:
        """
        Prompt for creating implementation action plans.
        
        Args:
            topic: Topic to create action plan for
            knowledge_context: Related knowledge cards
            
        Returns:
            Formatted prompt string
        """
        context_text = "\n\n".join([
            f"**{card['title']}:**\n{card['content'][:300]}..."
            for card in knowledge_context
        ])
        
        return f"""Create a step-by-step implementation plan for: {topic}

Knowledge Context:
{context_text}

Create an actionable plan with phases:
1. **Setup** - Environment, tools, prerequisites
2. **Implementation** - Core development steps
3. **Testing** - Validation and testing
4. **Deployment** - Going live or production

For each step, provide:
- title: Clear step name
- phase: Which phase it belongs to
- description: Detailed what to do
- difficulty: "easy", "medium", "hard"
- estimated_time: Realistic time estimate
- code_snippet: Code example if applicable
- resources: Helpful links or tools

Output as JSON:
{{
  "overview": "Brief plan summary",
  "total_time": "Estimated total time",
  "steps": [
    {{
      "title": "Set up development environment",
      "phase": "setup",
      "description": "Install required tools and configure workspace",
      "difficulty": "easy",
      "estimated_time": "30 minutes",
      "code_snippet": "npm install react",
      "resources": ["Official React docs", "VS Code setup guide"]
    }}
  ]
}}

Make it practical and actionable with concrete steps."""
    
    @staticmethod
    def talk_to_canvas_prompt(question: str, context: str, conversation_context: str = "", canvas_stats: Dict = None) -> str:
        """
        Prompt for conversational canvas queries.
        
        Args:
            question: User's question
            context: Relevant canvas content
            conversation_context: Previous conversation
            canvas_stats: Canvas statistics
            
        Returns:
            Formatted prompt string
        """
        stats_text = ""
        if canvas_stats:
            stats_text = f"\nCanvas Stats: {canvas_stats['total_cards']} total cards, {canvas_stats['relevant_cards']} relevant to this question."
        
        return f"""You are having a conversation with a user about their knowledge canvas. Answer their question using the relevant content from their canvas.

User Question: {question}

{context}{conversation_context}{stats_text}

Guidelines:
1. **Reference specific cards** when relevant (mention card titles)
2. **Provide personalized insights** based on their existing knowledge
3. **Suggest connections** between different concepts on their canvas
4. **Be conversational** and helpful
5. **Recommend next steps** for learning or exploration

Answer the question directly, then provide insights and recommendations based on their canvas content."""
    
    @staticmethod
    def suggest_arxiv_query_prompt(topic: str) -> str:
        """
        Prompt for generating arXiv search queries.
        
        Args:
            topic: Research topic
            
        Returns:
            Formatted prompt string
        """
        return f"""Generate an optimized search query for finding academic papers about: {topic}

Consider:
1. **Key terms** and synonyms
2. **arXiv categories** (cs.AI, cs.LG, cs.CV, etc.)
3. **Alternative phrasings** of the topic
4. **Related concepts** that might be relevant

Output as JSON:
{{
  "query": "machine learning AND (neural networks OR deep learning)",
  "categories": ["cs.LG", "cs.AI", "stat.ML"],
  "alternative_queries": [
    "artificial neural networks",
    "deep learning algorithms"
  ],
  "date_range": "recent 3 years for latest developments"
}}

Optimize for finding the most relevant and high-quality papers."""
    
    @staticmethod
    def rank_papers_prompt(topic: str, papers: List[Dict]) -> str:
        """
        Prompt for ranking arXiv papers by relevance.
        
        Args:
            topic: Research topic
            papers: List of papers to rank
            
        Returns:
            Formatted prompt string
        """
        papers_text = "\n\n".join([
            f"**{paper['title']}**\nAuthors: {', '.join(paper['authors'][:3])}\nAbstract: {paper['abstract'][:200]}..."
            for paper in papers
        ])
        
        return f"""Rank these papers by relevance to the topic: {topic}

Papers:
{papers_text}

Rank by:
1. **Relevance** to the specific topic
2. **Quality indicators** (author reputation, citations if available)
3. **Recency** (newer papers for latest developments)
4. **Foundational importance** (seminal papers in the field)

Output as JSON with reordered papers:
{{
  "papers": [
    // Reordered papers array with same structure
  ],
  "ranking_rationale": "Brief explanation of ranking criteria used"
}}

Prioritize the most relevant and impactful papers for someone learning about this topic."""
    
    @staticmethod
    def find_academic_sources_prompt(topic: str, max_papers: int) -> str:
        """
        Prompt for LLM fallback when arXiv is unavailable.
        
        Args:
            topic: Research topic
            max_papers: Maximum papers to suggest
            
        Returns:
            Formatted prompt string
        """
        return f"""Suggest {max_papers} important academic papers and research sources for: {topic}

For each paper, provide:
- title: Full paper title
- authors: List of author names
- published: Publication year or date
- abstract: Brief summary of the paper's contribution
- source: Where it was published (journal, conference, etc.)
- significance: Why this paper is important

Focus on:
1. **Foundational papers** that established key concepts
2. **Recent breakthroughs** in the field
3. **Survey papers** that provide good overviews
4. **Highly cited** and influential works

Output as JSON array:
[
  {{
    "title": "Attention Is All You Need",
    "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
    "published": "2017",
    "abstract": "Introduced the Transformer architecture, revolutionizing natural language processing by relying entirely on attention mechanisms.",
    "source": "NIPS 2017",
    "significance": "Foundational paper that enabled modern large language models like GPT and BERT"
  }}
]

Provide authoritative, well-known papers that would be valuable for research."""
    
    @staticmethod
    def find_counterpoints_prompt(title: str, content: str) -> str:
        """
        Prompt for finding counter-arguments and alternative perspectives.
        
        Args:
            title: Card title
            content: Card content
            
        Returns:
            Formatted prompt string
        """
        return f"""Find counter-arguments and alternative perspectives for this content:

Title: {title}
Content: {content}

Identify:
1. **Counter-arguments** - Direct challenges to the main claims
2. **Limitations** - Where this approach falls short
3. **Trade-offs** - What you give up by adopting this view
4. **Alternative approaches** - Different ways to solve the same problem

For each counterpoint, provide:
- title: Brief counterpoint name
- type: "counter-argument", "limitation", "trade-off", or "alternative"
- argument: The counterpoint explanation
- evidence: Supporting evidence or reasoning
- strength: "weak", "moderate", or "strong"

Output as JSON array:
[
  {{
    "title": "Scalability Concerns",
    "type": "limitation",
    "argument": "This approach may not scale well to large datasets due to computational complexity",
    "evidence": "Studies show performance degrades significantly with datasets over 1M records",
    "strength": "moderate"
  }}
]

Present counterpoints objectively without bias. Focus on legitimate challenges and alternatives."""
    
    @staticmethod
    def update_information_prompt(title: str, content: str, date: str) -> str:
        """
        Prompt for updating outdated information.
        
        Args:
            title: Card title
            content: Card content
            date: Card creation date
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze this content for outdated information and provide updates:

Title: {title}
Content: {content}
Original Date: {date}

Identify:
1. **Recent changes** - What has changed since this was written
2. **New features** - New capabilities or developments
3. **Deprecated items** - What's no longer recommended or supported
4. **Best practices** - Updated recommendations

For updates, provide:
- update_date: When these changes occurred
- changes: List of what has changed
- new_features: List of new capabilities
- deprecated: List of outdated items
- summary: Overall summary of updates

Output as JSON:
{{
  "update_date": "2024",
  "changes": [
    "React 18 introduced concurrent features",
    "Class components are now discouraged in favor of hooks"
  ],
  "new_features": [
    "Automatic batching for better performance",
    "Suspense for data fetching"
  ],
  "deprecated": [
    "componentWillMount lifecycle method",
    "String refs (use useRef instead)"
  ],
  "summary": "React has evolved significantly with focus on concurrent features and functional components"
}}

Focus on significant changes that would affect someone using this information today."""
    
    @staticmethod
    def learning_assistant_system_prompt() -> str:
        """System prompt for learning assistant agent."""
        return """You are the Learning Assistant Agent for Via Canvas.

Your role is to help users learn, understand, and apply knowledge through educational tools.

**Your Tools:**
- simplify_explanation: Create ELI5 explanations with analogies
- find_real_examples: Find concrete real-world applications
- analyze_knowledge_gaps: Identify missing prerequisites and advanced topics
- create_action_plan: Convert knowledge to implementation steps
- talk_to_canvas: Answer questions using canvas context
- find_academic_sources: Find research papers (hybrid LLM + arXiv)
- find_counterpoints: Find counter-arguments and alternatives
- update_information: Refresh outdated content
- find_surprising_connections: Discover non-obvious interdisciplinary connections
- comprehensive_learn: Create complete learning clusters with all aspects
- deep_research: Conduct multi-stage research with query decomposition, parallel search, review, and synthesis (MOST POWERFUL)

**When to Use Deep Research:**
Use `deep_research` for comprehensive research requests like:
- "Research the state of multi-agent systems"
- "Do a deep dive into transformer architectures"
- "Investigate the latest developments in quantum computing"
- "Comprehensive research on reinforcement learning"

Deep research provides:
- Query decomposition into sub-queries
- Parallel search across academic papers, canvas, and LLM insights
- Critical review with gap identification
- Iterative refinement (up to 2 loops)
- Structured synthesis with citations
- Hierarchical card cluster (20-40+ cards)

**Guidelines:**
1. **Educational Focus**: Always aim to help users learn and understand
2. **Multiple Perspectives**: Provide different viewpoints and approaches
3. **Practical Application**: Connect theory to real-world practice
4. **Progressive Learning**: Build from basics to advanced concepts
5. **Critical Thinking**: Encourage questioning and analysis

**Tool Usage Patterns:**
- Use `create_card_option=False` for previews first
- Let users confirm before creating cards
- Reference existing canvas content when relevant
- Suggest follow-up actions and learning paths
- For major research, recommend `deep_research` over `comprehensive_learn`

**Response Style:**
- Clear and educational
- Encouraging and supportive
- Provide context and reasoning
- Suggest next steps for learning

Your goal is to make learning engaging, comprehensive, and actionable."""

    
    @staticmethod
    def find_surprising_connections_prompt(cards_content: List[Dict]) -> str:
        """
        Prompt for finding surprising connections between topics.
        
        Args:
            cards_content: List of card content to analyze
            
        Returns:
            Formatted prompt string
        """
        cards_text = "\n\n".join([
            f"**Card {i+1}: {card['title']}**\n{card['content']}"
            for i, card in enumerate(cards_content)
        ])
        
        return f"""Analyze these cards and find surprising, non-obvious connections between them.

Cards to Analyze:
{cards_text}

Find connections that are:
1. **Non-obvious** - Not immediately apparent
2. **Interdisciplinary** - Cross different fields
3. **Insightful** - Provide new understanding
4. **Substantive** - Based on real shared principles

Types of connections to look for:
- **Shared Mathematics**: Same mathematical principles or equations
- **Analogies**: Metaphorical similarities in how they work
- **Interdisciplinary Work**: Research that bridges these fields
- **Historical Parallels**: Similar historical development or challenges
- **Underlying Principles**: Common fundamental concepts

For each connection, provide:
- title: Catchy name for the connection
- type: "shared_math", "analogy", "interdisciplinary", "historical", "principle"
- explanation: Detailed explanation of the connection (3-4 sentences)
- surprise_factor: "low", "medium", "high"
- cards_involved: List of card indices that are connected
- shared_principle: The underlying principle they share
- interdisciplinary_fields: List of fields this connection bridges
- examples: Real-world examples of this connection

Output as JSON array:
[
  {{
    "title": "Optimization Through Iteration",
    "type": "principle",
    "explanation": "Neural networks, evolution, and market economics all use iterative optimization. Neural networks use gradient descent, evolution uses natural selection, and markets use price discovery. All three systems improve through repeated cycles of variation and selection.",
    "surprise_factor": "high",
    "cards_involved": [0, 1, 2],
    "shared_principle": "Iterative optimization through feedback loops",
    "interdisciplinary_fields": ["Computer Science", "Biology", "Economics"],
    "examples": [
      "AlphaGo combines neural networks with evolutionary strategies",
      "Genetic algorithms in economics modeling"
    ]
  }}
]

Focus on connections that would genuinely surprise someone and provide new insights."""
    
    @staticmethod
    def comprehensive_learn_prompt(topic: str, depth: str) -> str:
        """
        Prompt for creating comprehensive learning plan.
        
        Args:
            topic: Topic to learn
            depth: "quick", "standard", or "deep"
            
        Returns:
            Formatted prompt string
        """
        depth_guidance = {
            "quick": "5-7 core concepts, 2-3 prerequisites, 2-3 advanced topics, 5 questions, 3 examples",
            "standard": "7-10 core concepts, 3-5 prerequisites, 4-6 advanced topics, 10 questions, 5 examples",
            "deep": "10-15 core concepts, 5-8 prerequisites, 6-10 advanced topics, 15 questions, 8 examples"
        }
        
        guidance = depth_guidance.get(depth, depth_guidance["standard"])
        
        return f"""Create a comprehensive learning plan for: {topic}

Depth Level: {depth} ({guidance})

Generate a complete learning structure with:

1. **Overview**: Brief introduction to the topic (2-3 sentences)

2. **Core Concepts**: Main ideas to understand
   - title: Concept name
   - description: What it is and why it matters
   - difficulty: "beginner", "intermediate", "advanced"

3. **Prerequisites**: What to know before learning this
   - title: Prerequisite topic
   - description: What you need to know
   - importance: "high", "medium", "low"
   - reasoning: Why this is needed

4. **Advanced Topics**: What to learn next
   - title: Advanced topic name
   - description: What this covers
   - builds_on: Which core concepts it extends

5. **Questions**: Learning questions to test understanding
   - question: The question to answer
   - difficulty: "easy", "medium", "hard"
   - answer: Brief answer or hint
   - tests_concept: Which concept this tests

6. **Examples**: Real-world applications
   - name: Example name
   - industry: Which field/industry
   - description: How it's used
   - demonstrates: Which concepts it shows

7. **Challenges**: Common pitfalls and counterpoints
   - title: Challenge or limitation
   - description: What the challenge is
   - type: "limitation", "common_mistake", "alternative"

8. **Learning Path**: Ordered roadmap
   - phase_1_prerequisites: List of prerequisite topics
   - phase_2_basics: List of basic concepts
   - phase_3_intermediate: List of intermediate concepts
   - phase_4_advanced: List of advanced topics

9. **Estimated Study Time**: Realistic time estimate

Output as JSON:
{{
  "overview": "Brief introduction...",
  "core_concepts": [
    {{
      "title": "Components",
      "description": "Reusable UI building blocks...",
      "difficulty": "beginner"
    }}
  ],
  "prerequisites": [
    {{
      "title": "JavaScript",
      "description": "Programming language fundamentals",
      "importance": "high",
      "reasoning": "React is built on JavaScript"
    }}
  ],
  "advanced_topics": [
    {{
      "title": "Custom Hooks",
      "description": "Creating reusable stateful logic",
      "builds_on": ["Hooks", "State Management"]
    }}
  ],
  "questions": [
    {{
      "question": "What is the difference between props and state?",
      "difficulty": "easy",
      "answer": "Props are passed from parent, state is managed internally",
      "tests_concept": "Props and State"
    }}
  ],
  "examples": [
    {{
      "name": "Netflix UI",
      "industry": "Streaming",
      "description": "Uses React for dynamic content loading",
      "demonstrates": ["Components", "State Management"]
    }}
  ],
  "challenges": [
    {{
      "title": "Performance Pitfalls",
      "description": "Unnecessary re-renders can slow down apps",
      "type": "common_mistake"
    }}
  ],
  "learning_path": {{
    "phase_1_prerequisites": ["JavaScript", "HTML", "CSS"],
    "phase_2_basics": ["Components", "JSX", "Props"],
    "phase_3_intermediate": ["State", "Hooks", "Effects"],
    "phase_4_advanced": ["Context", "Performance", "Testing"]
  }},
  "estimated_study_time": "8-12 hours for basics, 40+ hours for mastery"
}}

Create a comprehensive, well-structured learning plan that would help someone master this topic."""


    # ============================================================================
    # DEEP RESEARCH PROMPTS
    # ============================================================================
    
    @staticmethod
    def deep_research_query_analysis_prompt(topic: str) -> str:
        """
        Prompt for analyzing deep research query.
        
        Args:
            topic: Research topic
            
        Returns:
            Formatted prompt string
        """
        return f"""Analyze this research query and determine the research strategy.

Research Topic: {topic}

Analyze:
1. **Complexity**: "simple" (single concept), "moderate" (2-3 concepts), "complex" (multi-faceted)
2. **Domains**: List of academic/professional domains involved
3. **Strategy**: "focused" (narrow deep-dive), "comprehensive" (broad coverage), "exploratory" (open-ended)
4. **Key Concepts**: Main concepts to research
5. **Research Questions**: 2-3 core questions to answer

Output as JSON:
{{
  "complexity": "moderate",
  "domains": ["Computer Science", "Artificial Intelligence"],
  "strategy": "comprehensive",
  "key_concepts": ["multi-agent systems", "coordination", "communication"],
  "research_questions": [
    "How do agents coordinate in multi-agent systems?",
    "What are the main communication protocols?"
  ]
}}

Be specific and actionable."""
    
    @staticmethod
    def deep_research_decomposition_prompt(topic: str, analysis: Dict) -> str:
        """
        Prompt for decomposing research query into sub-queries.
        
        Args:
            topic: Research topic
            analysis: Query analysis results
            
        Returns:
            Formatted prompt string
        """
        return f"""Decompose this research query into atomic sub-queries that can be researched independently.

Main Topic: {topic}
Complexity: {analysis.get('complexity', 'moderate')}
Domains: {', '.join(analysis.get('domains', []))}
Strategy: {analysis.get('strategy', 'comprehensive')}

Create 3-5 sub-queries that:
1. Can be answered independently
2. Cover different aspects of the topic
3. Are specific and focused
4. Together provide comprehensive coverage

For each sub-query:
- question: Clear, specific question
- focus: What aspect it addresses
- priority: "high", "medium", "low"
- data_sources: Suggested sources ("academic", "web", "canvas", "llm")

Output as JSON:
{{
  "sub_queries": [
    {{
      "question": "What are the foundational papers on multi-agent coordination?",
      "focus": "historical_foundations",
      "priority": "high",
      "data_sources": ["academic", "llm"]
    }}
  ]
}}

Make sub-queries specific and actionable."""
    
    @staticmethod
    def deep_research_review_prompt(topic: str, findings_summary: str, queries_list: str) -> str:
        """
        Prompt for reviewing research findings.
        
        Args:
            topic: Research topic
            findings_summary: Summary of findings
            queries_list: List of sub-queries
            
        Returns:
            Formatted prompt string
        """
        return f"""Review these research findings for gaps and contradictions.

Research Topic: {topic}

Sub-Queries to Answer:
{queries_list}

Findings:
{findings_summary}

Analyze:
1. **Coverage Gaps**: Which sub-queries are not adequately answered?
2. **Missing Perspectives**: What important viewpoints are missing?
3. **Contradictions**: Any conflicting information?
4. **Quality Issues**: Any findings that seem unreliable?
5. **Need More Research**: Should we search for more information?

Output as JSON:
{{
  "gaps": [
    {{
      "topic": "Implementation details",
      "description": "Lack of practical implementation guidance",
      "severity": "high"
    }}
  ],
  "contradictions": [
    {{
      "finding_1": "Finding title 1",
      "finding_2": "Finding title 2",
      "conflict": "Description of contradiction"
    }}
  ],
  "needs_more_research": false,
  "overall_quality": "good",
  "coverage_score": 0.8
}}

Be critical and thorough."""
    
    @staticmethod
    def deep_research_synthesis_prompt(topic: str, findings_text: str, complexity: str, domains: List[str]) -> str:
        """
        Prompt for synthesizing research findings.
        
        Args:
            topic: Research topic
            findings_text: Text summary of findings
            complexity: Query complexity
            domains: Research domains
            
        Returns:
            Formatted prompt string
        """
        return f"""Synthesize these research findings into a comprehensive report.

Research Topic: {topic}
Complexity: {complexity}
Domains: {', '.join(domains)}

Findings:
{findings_text}

Create a structured synthesis with:

1. **Executive Summary**: 2-3 sentence overview of key insights

2. **Key Findings**: 5-7 main discoveries or insights
   - Each finding should be a clear statement
   - Include supporting evidence
   - Note source type (academic, canvas, insight)

3. **Methodology**: How this research was conducted
   - Sources searched
   - Analysis approach
   - Limitations

4. **Detailed Analysis**: Organized by theme
   - Group related findings
   - Explain relationships
   - Provide context

5. **Conclusions**: Main takeaways
   - What we learned
   - Implications
   - Future directions

6. **Recommendations**: Actionable next steps
   - Further reading
   - Areas to explore
   - Practical applications

Output as JSON:
{{
  "executive_summary": "Brief overview...",
  "key_findings": [
    {{
      "finding": "Clear statement of finding",
      "evidence": "Supporting evidence",
      "source_type": "academic",
      "importance": "high"
    }}
  ],
  "methodology": "Description of research approach...",
  "detailed_analysis": {{
    "theme_1": "Analysis of theme 1...",
    "theme_2": "Analysis of theme 2..."
  }},
  "conclusions": [
    "Main takeaway 1",
    "Main takeaway 2"
  ],
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2"
  ]
}}

Be comprehensive, well-organized, and insightful."""
