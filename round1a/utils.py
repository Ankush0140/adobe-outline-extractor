#!/usr/bin/env python3
"""
Utility functions for Adobe Hackathon Round 1A
Common helper functions for PDF processing and validation.
"""

import json
import logging
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
import jsonschema

# Configure logging
def setup_logging(level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )

# JSON Schema for validation
OUTLINE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "outline": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "level": {"type": "string", "enum": ["H1", "H2", "H3"]},
                    "text": {"type": "string"},
                    "page": {"type": "integer", "minimum": 1}
                },
                "required": ["level", "text", "page"]
            }
        }
    },
    "required": ["title", "outline"]
}

def validate_json_output(data: Dict[str, Any]) -> bool:
    """
    Validate JSON output against the required schema.
    
    Args:
        data: JSON data to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        jsonschema.validate(data, OUTLINE_SCHEMA)
        return True
    except jsonschema.ValidationError as e:
        logging.error(f"JSON validation error: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected validation error: {e}")
        return False

def save_json_output(data: Dict[str, Any], output_path: str) -> bool:
    """
    Save JSON data to file with proper formatting.
    
    Args:
        data: JSON data to save
        output_path: Path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error saving JSON to {output_path}: {e}")
        return False

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON data from file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        JSON data or None if failed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading JSON from {file_path}: {e}")
        return None

def normalize_text(text: str) -> str:
    """
    Normalize text by removing extra whitespace and special characters.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    import re
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\-\.\,\:\;\!\?\(\)]', '', text)
    
    return text

def extract_page_number_from_text(text: str) -> Optional[int]:
    """
    Extract page number from text patterns.
    
    Args:
        text: Text that might contain page numbers
        
    Returns:
        Page number if found, None otherwise
    """
    import re
    
    # Common page number patterns
    patterns = [
        r'page\s+(\d+)',
        r'p\.?\s*(\d+)',
        r'^(\d+)$',  # Just a number
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    
    return None

def clean_heading_text(text: str) -> str:
    """
    Clean heading text by removing common artifacts.
    
    Args:
        text: Raw heading text
        
    Returns:
        Cleaned text
    """
    import re
    
    # Remove common heading artifacts
    cleaning_patterns = [
        r'^\d+\.\s*',  # "1. "
        r'^\d+\.\d+\s*',  # "1.1 "
        r'^\d+\.\d+\.\d+\s*',  # "1.1.1 "
        r'^chapter\s+\d+:?\s*',  # "Chapter 1: "
        r'^section\s+\d+:?\s*',  # "Section 1: "
        r'^[ivx]+\.\s*',  # Roman numerals
        r'^[a-z]\.\s*',  # "a. "
        r'^[A-Z]\.\s*',  # "A. "
    ]
    
    cleaned = text
    for pattern in cleaning_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Clean up whitespace and normalize
    cleaned = normalize_text(cleaned)
    
    return cleaned if cleaned else text

def is_valid_heading(text: str, min_length: int = 2, max_length: int = 200) -> bool:
    """
    Check if text is a valid heading.
    
    Args:
        text: Text to check
        min_length: Minimum length
        max_length: Maximum length
        
    Returns:
        True if valid heading
    """
    if not text or not text.strip():
        return False
    
    text = text.strip()
    
    # Check length
    if len(text) < min_length or len(text) > max_length:
        return False
    
    # Skip if mostly numbers
    if text.replace('.', '').replace(' ', '').isdigit():
        return False
    
    # Skip if all special characters
    import re
    if re.match(r'^[^\w\s]+$', text):
        return False
    
    return True

def deduplicate_headings(headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate headings based on text similarity.
    
    Args:
        headings: List of heading dictionaries
        
    Returns:
        List of unique headings
    """
    unique_headings = []
    seen_texts = set()
    
    for heading in headings:
        text = heading.get("text", "").lower().strip()
        
        # Skip if empty
        if not text:
            continue
        
        # Skip if already seen
        if text in seen_texts:
            continue
        
        # Check for similarity with existing headings
        is_similar = False
        for seen_text in seen_texts:
            if texts_are_similar(text, seen_text):
                is_similar = True
                break
        
        if not is_similar:
            unique_headings.append(heading)
            seen_texts.add(text)
    
    return unique_headings

def texts_are_similar(text1: str, text2: str, threshold: float = 0.8) -> bool:
    """
    Check if two texts are similar.
    
    Args:
        text1: First text
        text2: Second text
        threshold: Similarity threshold
        
    Returns:
        True if similar
    """
    if not text1 or not text2:
        return False
    
    # Check if one is substring of another
    if text1 in text2 or text2 in text1:
        return True
    
    # Check word overlap
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return False
    
    overlap = len(words1.intersection(words2))
    similarity = overlap / max(len(words1), len(words2))
    
    return similarity >= threshold

def format_outline_for_display(outline_data: Dict[str, Any]) -> str:
    """
    Format outline data for human-readable display.
    
    Args:
        outline_data: Outline data dictionary
        
    Returns:
        Formatted string representation
    """
    result = []
    result.append(f"Title: {outline_data.get('title', 'N/A')}")
    result.append("\nOutline:")
    
    for item in outline_data.get('outline', []):
        level = item.get('level', 'H1')
        text = item.get('text', '')
        page = item.get('page', 1)
        
        # Create indentation based on level
        indent = '  ' * (int(level[1]) - 1)
        result.append(f"{indent}{level}: {text} (page {page})")
    
    return '\n'.join(result)

def benchmark_processing_time(func):
    """
    Decorator to benchmark processing time.
    
    Args:
        func: Function to benchmark
        
    Returns:
        Decorated function
    """
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        processing_time = end_time - start_time
        logging.info(f"{func.__name__} completed in {processing_time:.2f} seconds")
        
        return result
    
    return wrapper

def create_sample_output(title: str = "Sample Document") -> Dict[str, Any]:
    """
    Create sample output for testing.
    
    Args:
        title: Document title
        
    Returns:
        Sample outline data
    """
    return {
        "title": title,
        "outline": [
            {"level": "H1", "text": "Introduction", "page": 1},
            {"level": "H2", "text": "Background", "page": 1},
            {"level": "H2", "text": "Methodology", "page": 2},
            {"level": "H3", "text": "Data Collection", "page": 2},
            {"level": "H3", "text": "Analysis", "page": 3},
            {"level": "H1", "text": "Results", "page": 4},
            {"level": "H1", "text": "Conclusion", "page": 5}
        ]
    }

# Error handling utilities
class PDFProcessingError(Exception):
    """Custom exception for PDF processing errors."""
    pass

class OutlineExtractionError(Exception):
    """Custom exception for outline extraction errors."""
    pass

def handle_processing_error(error: Exception, pdf_path: str) -> Dict[str, Any]:
    """
    Handle processing errors gracefully.
    
    Args:
        error: Exception that occurred
        pdf_path: Path to PDF that caused error
        
    Returns:
        Error response in expected format
    """
    logging.error(f"Processing error for {pdf_path}: {str(error)}")
    
    # Return minimal valid response
    return {
        "title": f"Error processing {Path(pdf_path).name}",
        "outline": [
            {"level": "H1", "text": "Processing Error", "page": 1}
        ]
    }