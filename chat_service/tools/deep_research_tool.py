"""
Deep Research Tool

Comprehensive multi-stage research system that:
1. Analyzes and decomposes research queries
2. Executes parallel searches across multiple sources
3. Reviews findings for gaps and contradictions
4. Synthesizes results into structured reports
5. Creates hierarchical card clusters on canvas

Based on proven patterns from GPT Researcher and Stanford STORM.
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional
from strands import tool

# Import canvas API helpers
from tools.canvas_api import (
    create_card,
    get_canvas_cards,
    create_connection,
    calculate_child_position
)

# Import existing learning tools to reuse
from tools.learning_tools import find_academic_sources

# Import prompts
from prompts import PromptTemplates

logger = logging.getLogger(__name__)


@tool
def deep_research(
    topic: str,
    canvas_id: str,
    create_card_option: bool = False,
    depth: str = "standard",
    include_academic: bool = True,
    max_iterations: int = 2
) -> dict:
    """
    Conduct comprehensive deep research on a topic using multi-stage pipeline.
    
    This is the most powerful research tool, combining:
    - Query decomposition into sub-queries
    - Parallel search across multiple sources (arXiv, web, canvas)
    - Critical review and gap identification
    - Iterative refinement (up to 2 loops)
    - Synthesis into structured research report
    - Hierarchical card cluster creation
    
    Workflow:
    1. Query Analysis - Classify complexity and identify domains
    2. Query Processing - Decompose into atomic sub-queries
    3. Parallel Search - Execute searches simultaneously
    4. Document Analysis - Extract and score relevance
    5. Review & Iteration - Identify gaps, iterate if needed
    6. Synthesis - Integrate findings with citations
    7. Output Generation - Create structured report and cards
    
    Args:
        topic: Research topic or question
        canvas_id: Canvas ID for card creation
        create_card_option: If True, creates research cluster; if False, returns preview
        depth: "quick" (10-15 cards), "standard" (20-30 cards), "deep" (40+ cards)
        include_academic: If True, searches academic sources (arXiv)
        max_iterations: Maximum review/refinement loops (default 2)
        
    Returns:
        {
            "success": bool,
            "research_summary": dict,
            "findings": dict,
            "sources": list,
            "card_ids": dict,
            "preview": bool
        }
    """
    logger.info(f"Starting deep research for topic: {topic} (depth: {depth})")
    
    try:
        from agents.model_provider import get_nvidia_nim_model
        model = get_nvidia_nim_model()
        
        # ====================================================================
        # STAGE 1: QUERY ANALYSIS
        # ====================================================================
        logger.info("Stage 1: Query Analysis")
        
        analysis_prompt = _build_query_analysis_prompt(topic)
        analysis_response = model(analysis_prompt)
        
        try:
            from prompts import PromptFormatter
            query_analysis = PromptFormatter.parse_json_response(str(analysis_response))
        except Exception as e:
            logger.error(f"Failed to parse query analysis: {e}")
            return {
                "success": False,
                "error": "Failed to analyze research query"
            }
        
        complexity = query_analysis.get("complexity", "moderate")
        domains = query_analysis.get("domains", [])
        research_strategy = query_analysis.get("strategy", "comprehensive")
        
        logger.info(f"Query analysis: complexity={complexity}, domains={domains}, strategy={research_strategy}")
        
        # ====================================================================
        # STAGE 2: QUERY PROCESSING (Decomposition)
        # ====================================================================
        logger.info("Stage 2: Query Decomposition")
        
        decomposition_prompt = _build_query_decomposition_prompt(topic, query_analysis)
        decomposition_response = model(decomposition_prompt)
        
        try:
            decomposition = PromptFormatter.parse_json_response(str(decomposition_response))
        except Exception as e:
            logger.error(f"Failed to parse query decomposition: {e}")
            return {
                "success": False,
                "error": "Failed to decompose research query"
            }
        
        sub_queries = decomposition.get("sub_queries", [])
        logger.info(f"Decomposed into {len(sub_queries)} sub-queries")
        
        # ====================================================================
        # STAGE 3: PARALLEL SEARCH
        # ====================================================================
        logger.info("Stage 3: Parallel Search Execution")
        
        all_findings = []
        all_sources = []
        
        # Search academic sources if requested
        if include_academic and len(sub_queries) > 0:
            logger.info("Searching academic sources (arXiv)...")
            
            # Use first sub-query for academic search (most relevant)
            primary_query = sub_queries[0].get("question", topic)
            
            # Call existing find_academic_sources tool
            academic_results = find_academic_sources(
                topic=primary_query,
                card_id=None,  # No source card yet
                canvas_id=canvas_id,
                create_card_option=False,  # Don't create cards yet
                max_papers=5
            )
            
            if academic_results.get("success"):
                papers = academic_results.get("papers", [])
                all_sources.extend(papers)
                
                # Extract findings from papers
                for paper in papers:
                    all_findings.append({
                        "source": "academic",
                        "title": paper.get("title", ""),
                        "content": paper.get("abstract", ""),
                        "authors": paper.get("authors", []),
                        "url": paper.get("pdf_url", ""),
                        "relevance": "high"
                    })
                
                logger.info(f"Found {len(papers)} academic papers")
        
        # Search canvas knowledge base
        logger.info("Searching canvas knowledge base...")
        canvas_cards = get_canvas_cards(canvas_id)
        
        if canvas_cards:
            relevant_canvas_cards = _find_relevant_canvas_cards(topic, canvas_cards, max_cards=10)
            
            for card in relevant_canvas_cards:
                all_findings.append({
                    "source": "canvas",
                    "title": card.get("title", ""),
                    "content": card.get("content", ""),
                    "card_id": card.get("id"),
                    "relevance": "medium"
                })
            
            logger.info(f"Found {len(relevant_canvas_cards)} relevant canvas cards")
        
        # Generate LLM-based insights for sub-queries
        logger.info("Generating LLM insights for sub-queries...")
        for sub_query in sub_queries[:3]:  # Limit to top 3 sub-queries
            insight_prompt = _build_insight_generation_prompt(sub_query.get("question", ""), topic)
            insight_response = model(insight_prompt)
            
            all_findings.append({
                "source": "llm_insight",
                "title": sub_query.get("question", ""),
                "content": str(insight_response),
                "relevance": "high"
            })
        
        logger.info(f"Total findings collected: {len(all_findings)}")
        
        # ====================================================================
        # STAGE 4: DOCUMENT ANALYSIS
        # ====================================================================
        logger.info("Stage 4: Document Analysis and Relevance Scoring")
        
        # Score and rank findings
        scored_findings = _score_findings(all_findings, topic, model)
        
        # ====================================================================
        # STAGE 5: REVIEW & ITERATION
        # ====================================================================
        logger.info("Stage 5: Critical Review")
        
        review_prompt = _build_review_prompt(topic, scored_findings, sub_queries)
        review_response = model(review_prompt)
        
        try:
            review_results = PromptFormatter.parse_json_response(str(review_response))
        except Exception as e:
            logger.warning(f"Failed to parse review results: {e}")
            review_results = {
                "gaps": [],
                "contradictions": [],
                "needs_more_research": False
            }
        
        gaps = review_results.get("gaps", [])
        contradictions = review_results.get("contradictions", [])
        needs_more = review_results.get("needs_more_research", False)
        
        logger.info(f"Review: {len(gaps)} gaps, {len(contradictions)} contradictions, needs_more={needs_more}")
        
        # Iteration loop (if needed and within limit)
        iteration_count = 0
        while needs_more and iteration_count < max_iterations:
            iteration_count += 1
            logger.info(f"Iteration {iteration_count}: Addressing research gaps")
            
            # Generate additional insights for gaps
            for gap in gaps[:2]:  # Address top 2 gaps
                gap_prompt = _build_gap_filling_prompt(gap, topic)
                gap_response = model(gap_prompt)
                
                all_findings.append({
                    "source": "gap_filling",
                    "title": gap.get("topic", "Additional Research"),
                    "content": str(gap_response),
                    "relevance": "high"
                })
            
            # Re-review
            review_prompt = _build_review_prompt(topic, all_findings, sub_queries)
            review_response = model(review_prompt)
            
            try:
                review_results = PromptFormatter.parse_json_response(str(review_response))
                needs_more = review_results.get("needs_more_research", False)
            except:
                needs_more = False
        
        # ====================================================================
        # STAGE 6: SYNTHESIS
        # ====================================================================
        logger.info("Stage 6: Synthesis and Integration")
        
        synthesis_prompt = _build_synthesis_prompt(topic, scored_findings, query_analysis, review_results)
        synthesis_response = model(synthesis_prompt)
        
        try:
            synthesis = PromptFormatter.parse_json_response(str(synthesis_response))
        except Exception as e:
            logger.error(f"Failed to parse synthesis: {e}")
            return {
                "success": False,
                "error": "Failed to synthesize research findings"
            }
        
        # ====================================================================
        # STAGE 7: OUTPUT GENERATION
        # ====================================================================
        logger.info("Stage 7: Output Generation")
        
        research_summary = {
            "topic": topic,
            "complexity": complexity,
            "domains": domains,
            "total_findings": len(all_findings),
            "sources_breakdown": {
                "academic": len([f for f in all_findings if f["source"] == "academic"]),
                "canvas": len([f for f in all_findings if f["source"] == "canvas"]),
                "llm_insights": len([f for f in all_findings if f["source"] == "llm_insight"]),
                "gap_filling": len([f for f in all_findings if f["source"] == "gap_filling"])
            },
            "iterations": iteration_count,
            "gaps_identified": len(gaps),
            "contradictions_found": len(contradictions)
        }
        
        # If create_card_option is False, return preview
        if not create_card_option:
            estimated_cards = _estimate_card_count(synthesis, depth)
            
            return {
                "success": True,
                "research_summary": research_summary,
                "synthesis_preview": {
                    "executive_summary": synthesis.get("executive_summary", ""),
                    "key_findings": synthesis.get("key_findings", [])[:3],
                    "estimated_cards": estimated_cards
                },
                "sources": all_sources,
                "preview": True,
                "message": f"Research complete. Will create ~{estimated_cards} cards. Set create_card_option=True to create cluster."
            }
        
        # Create research cluster on canvas
        card_ids = _create_research_cluster(
            canvas_id=canvas_id,
            topic=topic,
            synthesis=synthesis,
            findings=scored_findings,
            sources=all_sources,
            gaps=gaps,
            depth=depth
        )
        
        logger.info(f"Created research cluster with {sum(len(v) if isinstance(v, list) else 1 for v in card_ids.values())} total cards")
        
        return {
            "success": True,
            "research_summary": research_summary,
            "findings": {
                "executive_summary": synthesis.get("executive_summary", ""),
                "key_findings": synthesis.get("key_findings", []),
                "methodology": synthesis.get("methodology", ""),
                "conclusions": synthesis.get("conclusions", [])
            },
            "sources": all_sources,
            "gaps": gaps,
            "contradictions": contradictions,
            "card_ids": card_ids,
            "preview": False,
            # Chat integration fields
            "cards": _build_cards_for_chat(card_ids, topic),
            "summary": f"Completed deep research on '{topic}' with {len(all_findings)} findings from {len(all_sources)} sources",
            "operation_type": "deep_research"
        }
        
    except Exception as e:
        logger.error(f"Error in deep research: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# HELPER FUNCTIONS - Query Analysis & Decomposition
# ============================================================================

def _build_query_analysis_prompt(topic: str) -> str:
    """Build prompt for analyzing research query."""
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


def _build_query_decomposition_prompt(topic: str, analysis: Dict) -> str:
    """Build prompt for decomposing query into sub-queries."""
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


def _build_insight_generation_prompt(sub_query: str, main_topic: str) -> str:
    """Build prompt for generating insights for a sub-query."""
    return f"""Provide comprehensive insights for this research sub-query.

Main Topic: {main_topic}
Sub-Query: {sub_query}

Provide:
1. **Core Explanation**: Clear explanation of the concept (2-3 paragraphs)
2. **Key Points**: 3-5 bullet points of essential information
3. **Examples**: 1-2 concrete examples
4. **Current State**: Latest developments or current understanding

Be comprehensive but concise. Focus on accuracy and clarity."""


# ============================================================================
# HELPER FUNCTIONS - Search & Analysis
# ============================================================================

def _find_relevant_canvas_cards(topic: str, cards: List[Dict], max_cards: int = 10) -> List[Dict]:
    """Find canvas cards relevant to research topic using keyword matching."""
    try:
        topic_words = set(topic.lower().split())
        
        scored_cards = []
        for card in cards:
            title = card.get("title", "").lower()
            content = card.get("content", "").lower()
            
            # Calculate relevance score
            title_matches = len(topic_words.intersection(set(title.split())))
            content_matches = len(topic_words.intersection(set(content.split())))
            
            relevance_score = title_matches * 3 + content_matches  # Title weighted higher
            
            if relevance_score > 0:
                card_copy = card.copy()
                card_copy["_relevance_score"] = relevance_score
                scored_cards.append(card_copy)
        
        # Sort by relevance and return top cards
        scored_cards.sort(key=lambda x: x["_relevance_score"], reverse=True)
        return scored_cards[:max_cards]
        
    except Exception as e:
        logger.error(f"Error finding relevant canvas cards: {e}")
        return cards[:max_cards]


def _score_findings(findings: List[Dict], topic: str, model) -> List[Dict]:
    """Score and rank findings by relevance and quality."""
    # For now, use simple heuristics
    # In production, could use LLM to score each finding
    
    scored = []
    for finding in findings:
        score = 0.5  # Base score
        
        # Source-based scoring
        if finding["source"] == "academic":
            score += 0.3
        elif finding["source"] == "llm_insight":
            score += 0.2
        elif finding["source"] == "canvas":
            score += 0.1
        
        # Relevance-based scoring
        if finding.get("relevance") == "high":
            score += 0.2
        elif finding.get("relevance") == "medium":
            score += 0.1
        
        finding["_score"] = min(score, 1.0)
        scored.append(finding)
    
    # Sort by score
    scored.sort(key=lambda x: x.get("_score", 0), reverse=True)
    return scored


# ============================================================================
# HELPER FUNCTIONS - Review & Synthesis
# ============================================================================

def _build_review_prompt(topic: str, findings: List[Dict], sub_queries: List[Dict]) -> str:
    """Build prompt for reviewing research findings."""
    findings_summary = "\n\n".join([
        f"**{f.get('title', 'Finding')}** (Source: {f.get('source', 'unknown')})\n{f.get('content', '')[:300]}..."
        for f in findings[:10]  # Top 10 findings
    ])
    
    queries_list = "\n".join([f"- {q.get('question', '')}" for q in sub_queries])
    
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


def _build_gap_filling_prompt(gap: Dict, topic: str) -> str:
    """Build prompt for filling identified research gaps."""
    return f"""Address this research gap for the topic: {topic}

Gap: {gap.get('topic', '')}
Description: {gap.get('description', '')}
Severity: {gap.get('severity', 'medium')}

Provide comprehensive information to fill this gap:
1. **Core Information**: Essential facts and concepts
2. **Context**: How this relates to the main topic
3. **Examples**: Concrete examples if applicable
4. **Sources**: Where this information comes from (if known)

Be thorough and accurate."""


def _build_synthesis_prompt(topic: str, findings: List[Dict], analysis: Dict, review: Dict) -> str:
    """Build prompt for synthesizing research findings."""
    findings_text = "\n\n".join([
        f"**{f.get('title', 'Finding')}**\nSource: {f.get('source', 'unknown')}\n{f.get('content', '')[:400]}..."
        for f in findings[:15]  # Top 15 findings
    ])
    
    return f"""Synthesize these research findings into a comprehensive report.

Research Topic: {topic}
Complexity: {analysis.get('complexity', 'moderate')}
Domains: {', '.join(analysis.get('domains', []))}

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


# ============================================================================
# HELPER FUNCTIONS - Card Creation
# ============================================================================

def _estimate_card_count(synthesis: Dict, depth: str) -> int:
    """Estimate number of cards that will be created."""
    base_counts = {
        "quick": 12,
        "standard": 25,
        "deep": 45
    }
    
    base = base_counts.get(depth, 25)
    
    # Adjust based on synthesis content
    key_findings = len(synthesis.get("key_findings", []))
    conclusions = len(synthesis.get("conclusions", []))
    recommendations = len(synthesis.get("recommendations", []))
    
    return base + key_findings + conclusions + recommendations


def _create_research_cluster(
    canvas_id: str,
    topic: str,
    synthesis: Dict,
    findings: List[Dict],
    sources: List[Dict],
    gaps: List[Dict],
    depth: str
) -> Dict:
    """Create hierarchical research cluster on canvas."""
    card_ids = {}
    
    # Main research card (center)
    main_card = create_card(
        canvas_id=canvas_id,
        title=f"🔬 Deep Research: {topic}",
        content=synthesis.get("executive_summary", ""),
        card_type="rich_text",
        position_x=0,
        position_y=0,
        tags=["research", "deep-research", "synthesis"]
    )
    card_ids["main"] = main_card["id"]
    
    # Key findings cards (top)
    findings_ids = []
    key_findings = synthesis.get("key_findings", [])[:7]  # Max 7
    for i, finding in enumerate(key_findings):
        child_x, child_y = calculate_child_position(
            parent_x=0, parent_y=0,
            child_index=i,
            total_children=len(key_findings),
            radius=350
        )
        
        finding_card = create_card(
            canvas_id=canvas_id,
            title=f"💡 {finding.get('finding', 'Key Finding')[:50]}",
            content=f"**Finding:** {finding.get('finding', '')}\n\n**Evidence:** {finding.get('evidence', '')}\n\n**Source:** {finding.get('source_type', 'unknown')}\n\n**Importance:** {finding.get('importance', 'medium')}",
            card_type="rich_text",
            position_x=child_x,
            position_y=child_y,
            parent_id=main_card["id"],
            tags=["finding", "research", finding.get("importance", "medium")]
        )
        findings_ids.append(finding_card["id"])
        create_connection(canvas_id, main_card["id"], finding_card["id"], "finding")
    
    card_ids["findings"] = findings_ids
    
    # Methodology card (left)
    methodology_card = create_card(
        canvas_id=canvas_id,
        title="📋 Research Methodology",
        content=synthesis.get("methodology", "Research methodology and approach"),
        card_type="rich_text",
        position_x=-400,
        position_y=0,
        tags=["methodology", "research"]
    )
    card_ids["methodology"] = methodology_card["id"]
    create_connection(canvas_id, main_card["id"], methodology_card["id"], "methodology")
    
    # Conclusions cards (right)
    conclusions_ids = []
    conclusions = synthesis.get("conclusions", [])[:5]
    for i, conclusion in enumerate(conclusions):
        child_x, child_y = calculate_child_position(
            parent_x=400, parent_y=0,
            child_index=i,
            total_children=len(conclusions),
            radius=200
        )
        
        conclusion_card = create_card(
            canvas_id=canvas_id,
            title=f"✓ Conclusion {i+1}",
            content=conclusion,
            card_type="rich_text",
            position_x=child_x,
            position_y=child_y,
            tags=["conclusion", "research"]
        )
        conclusions_ids.append(conclusion_card["id"])
        create_connection(canvas_id, main_card["id"], conclusion_card["id"], "conclusion")
    
    card_ids["conclusions"] = conclusions_ids
    
    # Recommendations cards (bottom)
    recommendations_ids = []
    recommendations = synthesis.get("recommendations", [])[:5]
    for i, recommendation in enumerate(recommendations):
        child_x, child_y = calculate_child_position(
            parent_x=0, parent_y=400,
            child_index=i,
            total_children=len(recommendations),
            radius=250
        )
        
        rec_card = create_card(
            canvas_id=canvas_id,
            title=f"→ {recommendation[:50]}",
            content=recommendation,
            card_type="rich_text",
            position_x=child_x,
            position_y=child_y,
            tags=["recommendation", "next-steps"]
        )
        recommendations_ids.append(rec_card["id"])
        create_connection(canvas_id, main_card["id"], rec_card["id"], "recommendation")
    
    card_ids["recommendations"] = recommendations_ids
    
    # Sources card (top-left)
    if sources:
        sources_content = "**Academic Sources:**\n\n"
        for source in sources[:5]:
            sources_content += f"• {source.get('title', 'Unknown')}\n"
            if source.get('authors'):
                sources_content += f"  Authors: {', '.join(source['authors'][:3])}\n"
            if source.get('pdf_url'):
                sources_content += f"  URL: {source['pdf_url']}\n"
            sources_content += "\n"
        
        sources_card = create_card(
            canvas_id=canvas_id,
            title="📚 Academic Sources",
            content=sources_content,
            card_type="rich_text",
            position_x=-300,
            position_y=-300,
            tags=["sources", "academic", "references"]
        )
        card_ids["sources"] = sources_card["id"]
        create_connection(canvas_id, main_card["id"], sources_card["id"], "references")
    
    # Gaps card (bottom-left) if gaps exist
    if gaps:
        gaps_content = "**Research Gaps Identified:**\n\n"
        for gap in gaps[:5]:
            gaps_content += f"• **{gap.get('topic', 'Gap')}**\n"
            gaps_content += f"  {gap.get('description', '')}\n"
            gaps_content += f"  Severity: {gap.get('severity', 'medium')}\n\n"
        
        gaps_card = create_card(
            canvas_id=canvas_id,
            title="🔍 Research Gaps",
            content=gaps_content,
            card_type="rich_text",
            position_x=-300,
            position_y=300,
            tags=["gaps", "future-research"]
        )
        card_ids["gaps"] = gaps_card["id"]
        create_connection(canvas_id, main_card["id"], gaps_card["id"], "identifies_gaps")
    
    return card_ids


def _build_cards_for_chat(card_ids: Dict, topic: str) -> List[Dict]:
    """Build cards array for chat display."""
    cards = []
    
    if "main" in card_ids:
        cards.append({
            "id": card_ids["main"],
            "title": f"🔬 Deep Research: {topic}",
            "type": "rich_text",
            "parent_id": None
        })
    
    if "findings" in card_ids:
        for i, finding_id in enumerate(card_ids["findings"]):
            cards.append({
                "id": finding_id,
                "title": f"💡 Key Finding {i+1}",
                "type": "rich_text",
                "parent_id": card_ids.get("main")
            })
    
    return cards
