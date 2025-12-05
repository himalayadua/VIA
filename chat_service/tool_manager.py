"""
Tool Manager for Via Canvas AI Service

Manages canvas data access tools that allow the AI agent to query
and analyze canvas content from PostgreSQL.
"""

import logging
import json
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
from strands.tools import tool
from config import settings

logger = logging.getLogger(__name__)


class ToolManager:
    """
    Manages canvas data access tools
    
    Provides tools for the Strands agent to search and analyze canvas content
    by querying the PostgreSQL database.
    """
    
    def __init__(self):
        """Initialize ToolManager with database configuration"""
        self.db_config = {
            'host': settings.db_host,
            'port': settings.db_port,
            'database': settings.db_name,
            'user': settings.db_user,
            'password': settings.db_password,
        }
        logger.info("ToolManager initialized with database config")
    
    def get_db_connection(self):
        """
        Get PostgreSQL database connection
        
        Returns:
            psycopg2 connection with RealDictCursor
        """
        try:
            conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def get_canvas_tools(self) -> List:
        """
        Return list of ALL canvas tools for the AI agent.
        
        Includes:
        - Basic canvas query tools (search, titles, tags)
        - Canvas query tools (recent cards, by tag, children, search, summary) - NEW Phase 2
        - Content extraction tools (URL extraction)
        - Graph intelligence tools (placement, connections, similarity)
        - Content manipulation tools (grow, categorize, merge)
        - Conflict detection tools (duplicates, conflicts)
        
        Returns:
            List of tool functions decorated with @tool
        """
        # Import canvas manipulation tools
        from tools.canvas_tools import (
            extract_url_content,
            grow_card_content,
            find_similar_cards,
            categorize_content,
            detect_conflicts,
            merge_cards,
            get_merge_preview
        )
        
        # Import graph intelligence tools
        from tools.graph_tools import (
            suggest_card_placement,
            create_intelligent_connections
        )
        
        # Import canvas query tools (Phase 2)
        from tools.canvas_query_tools import (
            get_recent_cards,
            get_cards_by_tag,
            get_card_children,
            search_canvas_by_content,
            get_canvas_summary
        )
        
        # Import knowledge base tools (Phase 2 - Week 6-7)
        from tools.knowledge_base_tools import (
            search_knowledge_base,
            get_knowledge_context,
            get_knowledge_base_stats
        )
        
        return [
            # Basic canvas query tools (legacy)
            self.search_canvas_content,
            self.get_canvas_titles,
            self.get_canvas_tags,
            self.find_similar_nodes,
            
            # Canvas query tools (Phase 2 - for follow-up conversations)
            get_recent_cards,
            get_cards_by_tag,
            get_card_children,
            search_canvas_by_content,
            get_canvas_summary,
            
            # Content extraction and manipulation
            extract_url_content,
            grow_card_content,
            categorize_content,
            
            # Graph intelligence
            find_similar_cards,
            suggest_card_placement,
            create_intelligent_connections,
            
            # Conflict detection and resolution
            detect_conflicts,
            get_merge_preview,
            merge_cards,
            
            # Knowledge base tools (RAG)
            search_knowledge_base,
            get_knowledge_context,
            get_knowledge_base_stats
        ]
    
    def get_extraction_tools(self) -> List:
        """
        Return tools for content extraction agent.
        
        Includes:
        - URL extraction and card creation
        - Card growth and expansion
        - Intelligent placement and connections
        
        Returns:
            List of tool functions for extraction operations
        """
        from tools.canvas_tools import (
            extract_url_content,
            grow_card_content,
            find_similar_cards
        )
        
        from tools.graph_tools import (
            suggest_card_placement,
            create_intelligent_connections
        )
        
        return [
            extract_url_content,
            grow_card_content,
            find_similar_cards,
            suggest_card_placement,
            create_intelligent_connections
        ]
    
    @tool(
        name="search_canvas_content",
        description="Search for nodes containing specific text in their content. Use this when the user asks about specific topics, keywords, or content on their canvas.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text to search for in node content"
                },
                "canvas_id": {
                    "type": "string",
                    "description": "Canvas ID to search in"
                }
            },
            "required": ["query", "canvas_id"]
        }
    )
    def search_canvas_content(self, query: str, canvas_id: str) -> str:
        """
        Search canvas nodes by content
        
        Args:
            query: Text to search for
            canvas_id: Canvas ID to search in
            
        Returns:
            JSON string with search results
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            logger.info(f"Searching canvas {canvas_id} for: {query}")
            
            cursor.execute(
                """SELECT id, content, position_x, position_y, type, 
                          created_at, updated_at
                   FROM nodes
                   WHERE canvas_id = %s AND content ILIKE %s
                   ORDER BY created_at DESC
                   LIMIT 10""",
                (canvas_id, f'%{query}%')
            )
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Convert to list of dicts
            nodes = [dict(row) for row in results]
            
            # Convert datetime objects to strings
            for node in nodes:
                if 'created_at' in node and node['created_at']:
                    node['created_at'] = node['created_at'].isoformat()
                if 'updated_at' in node and node['updated_at']:
                    node['updated_at'] = node['updated_at'].isoformat()
            
            result = {
                "found": len(nodes),
                "query": query,
                "nodes": nodes
            }
            
            logger.info(f"Found {len(nodes)} nodes matching '{query}'")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error searching canvas content: {e}", exc_info=True)
            return json.dumps({
                "error": str(e),
                "found": 0,
                "nodes": []
            })
    
    @tool(
        name="get_canvas_titles",
        description="Get all node titles from the canvas. Use this to get an overview of all nodes or when the user asks 'what's on my canvas' or 'show me all nodes'.",
        input_schema={
            "type": "object",
            "properties": {
                "canvas_id": {
                    "type": "string",
                    "description": "Canvas ID"
                }
            },
            "required": ["canvas_id"]
        }
    )
    def get_canvas_titles(self, canvas_id: str) -> str:
        """
        Get all node titles from canvas
        
        Args:
            canvas_id: Canvas ID
            
        Returns:
            JSON string with node titles
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            logger.info(f"Getting titles for canvas {canvas_id}")
            
            cursor.execute(
                """SELECT id, content, type, created_at
                   FROM nodes
                   WHERE canvas_id = %s
                   ORDER BY created_at ASC""",
                (canvas_id,)
            )
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Extract first line as title
            titles = []
            for row in results:
                content = row['content'] or ''
                # Get first non-empty line as title
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                title = lines[0][:100] if lines else '(Empty node)'
                
                titles.append({
                    "id": row['id'],
                    "title": title,
                    "type": row['type'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            result = {
                "count": len(titles),
                "titles": titles
            }
            
            logger.info(f"Found {len(titles)} nodes in canvas")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting canvas titles: {e}", exc_info=True)
            return json.dumps({
                "error": str(e),
                "count": 0,
                "titles": []
            })
    
    @tool(
        name="get_canvas_tags",
        description="Extract unique tags from node content (words starting with #). Use this when the user asks about tags, categories, or wants to see how their content is organized.",
        input_schema={
            "type": "object",
            "properties": {
                "canvas_id": {
                    "type": "string",
                    "description": "Canvas ID"
                }
            },
            "required": ["canvas_id"]
        }
    )
    def get_canvas_tags(self, canvas_id: str) -> str:
        """
        Extract unique tags from canvas nodes
        
        Args:
            canvas_id: Canvas ID
            
        Returns:
            JSON string with unique tags
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            logger.info(f"Extracting tags from canvas {canvas_id}")
            
            cursor.execute(
                """SELECT content FROM nodes WHERE canvas_id = %s""",
                (canvas_id,)
            )
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Extract hashtags using regex
            tag_set = set()
            tag_regex = re.compile(r'#(\w+)')
            
            for row in results:
                content = row['content'] or ''
                matches = tag_regex.findall(content)
                tag_set.update(matches)
            
            tags = sorted(list(tag_set))
            
            result = {
                "count": len(tags),
                "tags": tags
            }
            
            logger.info(f"Found {len(tags)} unique tags")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting canvas tags: {e}", exc_info=True)
            return json.dumps({
                "error": str(e),
                "count": 0,
                "tags": []
            })
    
    @tool(
        name="find_similar_nodes",
        description="Find nodes with similar content using keyword matching. Use this when the user wants to find related nodes or group similar content.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Reference text to find similar nodes"
                },
                "canvas_id": {
                    "type": "string",
                    "description": "Canvas ID"
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of results to return",
                    "default": 5
                }
            },
            "required": ["query", "canvas_id"]
        }
    )
    def find_similar_nodes(self, query: str, canvas_id: str, limit: int = 5) -> str:
        """
        Find similar nodes using keyword-based similarity
        
        Args:
            query: Reference text to find similar nodes
            canvas_id: Canvas ID
            limit: Maximum number of results
            
        Returns:
            JSON string with similar nodes
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            logger.info(f"Finding nodes similar to: {query}")
            
            cursor.execute(
                """SELECT id, content, position_x, position_y, type, created_at
                   FROM nodes
                   WHERE canvas_id = %s
                   ORDER BY created_at DESC""",
                (canvas_id,)
            )
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Simple keyword-based similarity (can be enhanced with embeddings)
            keywords = query.lower().split()
            
            scored_nodes = []
            for row in results:
                content = (row['content'] or '').lower()
                score = sum(1 for keyword in keywords if keyword in content)
                
                if score > 0:
                    node_dict = dict(row)
                    node_dict['score'] = score
                    node_dict['created_at'] = node_dict['created_at'].isoformat() if node_dict['created_at'] else None
                    scored_nodes.append(node_dict)
            
            # Sort by score and take top N
            scored_nodes.sort(key=lambda x: x['score'], reverse=True)
            similar = scored_nodes[:limit]
            
            # Remove score from output
            for node in similar:
                del node['score']
            
            result = {
                "found": len(similar),
                "query": query,
                "nodes": similar
            }
            
            logger.info(f"Found {len(similar)} similar nodes")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error finding similar nodes: {e}", exc_info=True)
            return json.dumps({
                "error": str(e),
                "found": 0,
                "nodes": []
            })
