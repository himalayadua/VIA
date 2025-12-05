"""
GitHub Extractor

Extracts repository information and README content from GitHub URLs.
"""

import logging
from typing import Dict
from .url_extractor import URLExtractor

logger = logging.getLogger(__name__)


class GitHubExtractor(URLExtractor):
    """
    Extract content from GitHub repositories.
    
    Extracts:
    - Repository metadata (name, description, stars, language)
    - README content parsed into sections
    - Topics/tags
    """
    
    def extract(self) -> Dict:
        """
        Extract structured content from GitHub repository.
        
        Returns:
            Dictionary with extracted repository structure
        """
        logger.info(f"Extracting GitHub repository from: {self.url}")
        
        # Parse repo owner and name from URL
        # https://github.com/owner/repo
        parts = self.parsed_url.path.strip('/').split('/')
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL format: {self.url}")
        
        owner = parts[0]
        repo_name = parts[1]
        
        # TODO: Implement GitHub API integration
        # For now, return placeholder structure
        result = {
            "card_type": "link",
            "title": f"{owner}/{repo_name}",
            "description": f"GitHub repository: {owner}/{repo_name}",
            "sections": [
                {
                    "title": "Repository",
                    "content": f"This is a placeholder for {owner}/{repo_name}. Full implementation coming in Task 2.4."
                }
            ],
            "metadata": {
                **self.get_metadata(),
                "owner": owner,
                "repo": repo_name
            }
        }
        
        logger.info(f"Extracted GitHub repo: {owner}/{repo_name}")
        return result
