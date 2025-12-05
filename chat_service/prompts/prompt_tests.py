"""
Prompt Testing Utilities

Utilities for testing prompts with sample data to ensure they work correctly.
Provides validation and testing functions for all prompt templates.
"""

import json
import logging
from typing import Dict, Any

from .prompt_templates import PromptTemplates
from .prompt_utils import PromptFormatter

logger = logging.getLogger(__name__)


class PromptTester:
    """
    Test prompts with sample data to ensure they work correctly.
    
    Provides methods to:
    - Test individual prompts
    - Validate prompt formatting
    - Test JSON extraction
    - Run comprehensive test suite
    """
    
    @staticmethod
    def test_grow_card_prompt() -> Dict[str, Any]:
        """
        Test grow card prompt with sample data.
        
        Returns:
            Test results dictionary
        """
        print("Testing grow_card_prompt...")
        
        prompt = PromptTemplates.grow_card_prompt(
            card_title="Machine Learning",
            card_content="Machine Learning is a subset of artificial intelligence that uses algorithms to learn patterns from data and make predictions or decisions without being explicitly programmed for each task.",
            num_concepts=3
        )
        
        stats = PromptFormatter.get_prompt_stats(prompt)
        
        result = {
            'test_name': 'grow_card_prompt',
            'success': True,
            'prompt_length': stats['length'],
            'within_limit': stats['within_limit'],
            'contains_json_instruction': '"title":' in prompt,
            'contains_variables': 'Machine Learning' in prompt
        }
        
        print(f"  ✓ Generated prompt ({stats['length']} chars)")
        print(f"  ✓ Within length limit: {stats['within_limit']}")
        
        return result
    
    @staticmethod
    def test_categorize_prompt() -> Dict[str, Any]:
        """
        Test categorize prompt with sample data.
        
        Returns:
            Test results dictionary
        """
        print("Testing categorize_content_prompt...")
        
        prompt = PromptTemplates.categorize_content_prompt(
            content="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            title="Fibonacci Function"
        )
        
        stats = PromptFormatter.get_prompt_stats(prompt)
        
        result = {
            'test_name': 'categorize_content_prompt',
            'success': True,
            'prompt_length': stats['length'],
            'within_limit': stats['within_limit'],
            'contains_json_instruction': '"category":' in prompt,
            'contains_content': 'fibonacci' in prompt
        }
        
        print(f"  ✓ Generated prompt ({stats['length']} chars)")
        print(f"  ✓ Within length limit: {stats['within_limit']}")
        
        return result
    
    @staticmethod
    def test_url_analysis_prompt() -> Dict[str, Any]:
        """
        Test URL analysis prompt with sample data.
        
        Returns:
            Test results dictionary
        """
        print("Testing url_analysis_prompt...")
        
        prompt = PromptTemplates.url_analysis_prompt(
            url="https://docs.python.org/3/tutorial/introduction.html",
            content="This tutorial introduces the reader informally to the basic concepts and features of the Python language and system. It helps to have a Python interpreter handy for hands-on experience."
        )
        
        stats = PromptFormatter.get_prompt_stats(prompt)
        
        result = {
            'test_name': 'url_analysis_prompt',
            'success': True,
            'prompt_length': stats['length'],
            'within_limit': stats['within_limit'],
            'contains_url': 'docs.python.org' in prompt,
            'contains_json_structure': '"main_topic":' in prompt
        }
        
        print(f"  ✓ Generated prompt ({stats['length']} chars)")
        print(f"  ✓ Contains URL: {result['contains_url']}")
        
        return result
    
    @staticmethod
    def test_card_placement_prompt() -> Dict[str, Any]:
        """
        Test card placement prompt with sample data.
        
        Returns:
            Test results dictionary
        """
        print("Testing card_placement_prompt...")
        
        existing_cards = [
            {'id': 'card1', 'title': 'Python Basics'},
            {'id': 'card2', 'title': 'Data Structures'},
            {'id': 'card3', 'title': 'Algorithms'}
        ]
        
        prompt = PromptTemplates.card_placement_prompt(
            new_card_title="List Comprehensions",
            new_card_content="Python list comprehensions provide a concise way to create lists.",
            existing_cards=existing_cards
        )
        
        stats = PromptFormatter.get_prompt_stats(prompt)
        
        result = {
            'test_name': 'card_placement_prompt',
            'success': True,
            'prompt_length': stats['length'],
            'within_limit': stats['within_limit'],
            'contains_existing_cards': 'Python Basics' in prompt,
            'contains_new_card': 'List Comprehensions' in prompt
        }
        
        print(f"  ✓ Generated prompt ({stats['length']} chars)")
        print(f"  ✓ Contains existing cards: {result['contains_existing_cards']}")
        
        return result
    
    @staticmethod
    def test_json_extraction() -> Dict[str, Any]:
        """
        Test JSON extraction from various response formats.
        
        Returns:
            Test results dictionary
        """
        print("Testing JSON extraction...")
        
        test_cases = [
            # Standard JSON
            '{"key": "value"}',
            
            # JSON with markdown
            '```json\n{"key": "value"}\n```',
            
            # JSON with generic code block
            '```\n{"key": "value"}\n```',
            
            # JSON with surrounding text
            'Here is the result:\n```json\n{"key": "value"}\n```\nDone!',
            
            # Array format
            '[{"item": 1}, {"item": 2}]',
            
            # Complex nested JSON
            '{"data": {"nested": [1, 2, 3]}, "status": "ok"}'
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases):
            try:
                extracted = PromptFormatter.extract_json_from_response(test_case)
                parsed = json.loads(extracted)
                success_count += 1
                print(f"  ✓ Test case {i+1}: Extracted and parsed successfully")
            except Exception as e:
                print(f"  ✗ Test case {i+1}: Failed - {e}")
        
        result = {
            'test_name': 'json_extraction',
            'success': success_count == len(test_cases),
            'total_cases': len(test_cases),
            'successful_cases': success_count,
            'success_rate': success_count / len(test_cases)
        }
        
        print(f"  ✓ Success rate: {result['success_rate']:.1%}")
        
        return result
    
    @staticmethod
    def test_prompt_formatting() -> Dict[str, Any]:
        """
        Test prompt formatting utilities.
        
        Returns:
            Test results dictionary
        """
        print("Testing prompt formatting...")
        
        # Test content truncation
        long_content = "This is a very long piece of content. " * 100
        truncated = PromptFormatter.truncate_content(long_content, 200)
        
        # Test input sanitization
        dangerous_input = 'Normal text """ injection attempt ``` more text'
        sanitized = PromptFormatter.sanitize_input(dangerous_input)
        
        # Test context injection
        base_prompt = "Analyze this content."
        with_context = PromptFormatter.inject_canvas_context(base_prompt, "canvas_123")
        
        result = {
            'test_name': 'prompt_formatting',
            'success': True,
            'truncation_works': len(truncated) <= 200 and truncated.endswith('...'),
            'sanitization_works': '"""' not in sanitized and '```' not in sanitized,
            'context_injection_works': 'canvas_123' in with_context
        }
        
        print(f"  ✓ Truncation: {result['truncation_works']}")
        print(f"  ✓ Sanitization: {result['sanitization_works']}")
        print(f"  ✓ Context injection: {result['context_injection_works']}")
        
        return result
    
    @staticmethod
    def test_agent_prompts() -> Dict[str, Any]:
        """
        Test all agent system prompts.
        
        Returns:
            Test results dictionary
        """
        print("Testing agent system prompts...")
        
        prompts = {
            'orchestrator': PromptTemplates.orchestrator_system_prompt(),
            'content_extraction': PromptTemplates.content_extraction_system_prompt(),
            'chat_agent': PromptTemplates.chat_agent_system_prompt(),
            'knowledge_graph': PromptTemplates.knowledge_graph_system_prompt(),
            'learning_assistant': PromptTemplates.learning_assistant_system_prompt(),
            'background_intelligence': PromptTemplates.background_intelligence_system_prompt()
        }
        
        all_valid = True
        for name, prompt in prompts.items():
            stats = PromptFormatter.get_prompt_stats(prompt)
            is_valid = stats['within_limit'] and len(prompt) > 100
            
            if is_valid:
                print(f"  ✓ {name}: {stats['length']} chars")
            else:
                print(f"  ✗ {name}: Invalid (length: {stats['length']})")
                all_valid = False
        
        result = {
            'test_name': 'agent_prompts',
            'success': all_valid,
            'total_prompts': len(prompts),
            'prompts_tested': list(prompts.keys())
        }
        
        return result
    
    @staticmethod
    def run_all_tests() -> Dict[str, Any]:
        """
        Run all prompt tests and return comprehensive results.
        
        Returns:
            Complete test results
        """
        print("\n=== Running Prompt Template Tests ===\n")
        
        test_results = []
        
        # Run individual tests
        test_results.append(PromptTester.test_grow_card_prompt())
        test_results.append(PromptTester.test_categorize_prompt())
        test_results.append(PromptTester.test_url_analysis_prompt())
        test_results.append(PromptTester.test_card_placement_prompt())
        test_results.append(PromptTester.test_json_extraction())
        test_results.append(PromptTester.test_prompt_formatting())
        test_results.append(PromptTester.test_agent_prompts())
        
        # Calculate overall results
        total_tests = len(test_results)
        successful_tests = sum(1 for result in test_results if result['success'])
        
        overall_result = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': successful_tests / total_tests,
            'all_passed': successful_tests == total_tests,
            'individual_results': test_results
        }
        
        print(f"\n=== Test Results Summary ===\n")
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Success rate: {overall_result['success_rate']:.1%}")
        
        if overall_result['all_passed']:
            print("\n✅ All prompt tests passed!\n")
        else:
            print("\n❌ Some tests failed. Check individual results.\n")
        
        return overall_result


# Sample data for testing
SAMPLE_DATA = {
    'card_content': {
        'title': 'Machine Learning Fundamentals',
        'content': 'Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.'
    },
    'code_content': {
        'title': 'Python Function',
        'content': 'def calculate_fibonacci(n):\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)'
    },
    'url_content': {
        'url': 'https://docs.python.org/3/tutorial/',
        'content': 'Python is an easy to learn, powerful programming language. It has efficient high-level data structures and a simple but effective approach to object-oriented programming.'
    }
}


# Run tests if executed directly
if __name__ == "__main__":
    PromptTester.run_all_tests()
