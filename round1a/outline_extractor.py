#!/usr/bin/env python3
"""
Outline Extractor for Adobe Hackathon Round 1A
Extracts hierarchical outline structure from parsed PDF data.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class OutlineExtractor:
    """Extracts hierarchical outline structure from PDF text."""
    
    def __init__(self):
        self.font_size_threshold = 12
        self.heading_patterns = [
            # Numbered headings
            r'^(\d+)\.\s+(.+)$',  # "1. Introduction"
            r'^(\d+\.\d+)\s+(.+)$',  # "1.1 Overview"
            r'^(\d+\.\d+\.\d+)\s+(.+)$',  # "1.1.1 Details"
            
            # Roman numerals
            r'^([IVX]+)\.\s+(.+)$',  # "I. Introduction"
            r'^([ivx]+)\.\s+(.+)$',  # "i. Introduction"
            
            # Letter headings
            r'^([A-Z])\.\s+(.+)$',  # "A. Introduction"
            r'^([a-z])\.\s+(.+)$',  # "a. Introduction"
            
            # Chapter/Section patterns
            r'^(Chapter\s+\d+):?\s*(.*)$',
            r'^(Section\s+\d+):?\s*(.*)$',
            r'^(Part\s+\d+):?\s*(.*)$',
            
            # All caps headings
            r'^([A-Z\s]+)$',  # "INTRODUCTION"
        ]
    
    def extract_outline(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract outline structure from parsed PDF data.
        
        Args:
            parsed_data: Parsed PDF data from PDFParser
            
        Returns:
            Dictionary with title and outline structure
        """
        try:
            title = parsed_data.get("title", "Untitled Document")
            pages = parsed_data.get("pages", [])
            
            # Extract potential headings from all pages
            potential_headings = self._extract_potential_headings(pages)
            
            # Analyze and classify headings
            classified_headings = self._classify_headings(potential_headings)
            
            # Build hierarchical structure
            outline = self._build_outline_hierarchy(classified_headings)
            
            return {
                "title": title,
                "outline": outline
            }
            
        except Exception as e:
            logger.error(f"Error extracting outline: {str(e)}")
            raise
    
    def _extract_potential_headings(self, pages: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extract potential headings from all pages.
        
        Args:
            pages: List of page data
            
        Returns:
            List of potential heading elements
        """
        potential_headings = []
        font_sizes = []
        
        # First pass: collect all font sizes
        for page in pages:
            for block in page.get("text_blocks", []):
                font_sizes.append(block.get("font_size", 0))
        
        # Calculate font size statistics
        if font_sizes:
            avg_font_size = sum(font_sizes) / len(font_sizes)
            max_font_size = max(font_sizes)
            self.font_size_threshold = max(avg_font_size + 2, 12)
        
        # Second pass: extract potential headings
        for page in pages:
            for block in page.get("text_blocks", []):
                text = block.get("text", "").strip()
                
                if self._is_potential_heading(block, text):
                    potential_headings.append({
                        "text": text,
                        "page": block.get("page", 1),
                        "font_size": block.get("font_size", 0),
                        "is_bold": block.get("is_bold", False),
                        "likely_heading": block.get("likely_heading", False)
                    })
        
        return potential_headings
    
    def _is_potential_heading(self, block: Dict, text: str) -> bool:
        """
        Determine if a text block is a potential heading.
        
        Args:
            block: Text block data
            text: Text content
            
        Returns:
            True if potentially a heading
        """
        if not text or len(text) < 2:
            return False
        
        # Skip very long text (likely paragraphs)
        if len(text) > 200:
            return False
        
        # Check if already marked as likely heading
        if block.get("likely_heading", False):
            return True
        
        # Check font size
        font_size = block.get("font_size", 0)
        if font_size >= self.font_size_threshold:
            return True
        
        # Check if bold
        if block.get("is_bold", False):
            return True
        
        # Check against heading patterns
        for pattern in self.heading_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # Check for title case headings
        if (text.istitle() and 
            len(text.split()) <= 8 and 
            not text.endswith('.')):
            return True
        
        return False
    
    def _classify_headings(self, headings: List[Dict]) -> List[Dict[str, Any]]:
        """
        Classify headings into hierarchy levels (H1, H2, H3).
        
        Args:
            headings: List of potential headings
            
        Returns:
            List of classified headings with levels
        """
        classified = []
        
        # Group by font size for level determination
        font_size_groups = defaultdict(list)
        for heading in headings:
            font_size = heading["font_size"]
            font_size_groups[font_size].append(heading)
        
        # Sort font sizes in descending order
        sorted_sizes = sorted(font_size_groups.keys(), reverse=True)
        
        # Assign levels based on font size (largest = H1, etc.)
        level_map = {}
        for i, size in enumerate(sorted_sizes[:3]):  # Only H1, H2, H3
            level_map[size] = f"H{i+1}"
        
        # Process each heading
        for heading in headings:
            font_size = heading["font_size"]
            text = heading["text"]
            
            # Determine level
            level = self._determine_heading_level(text, font_size, level_map)
            
            if level:
                classified.append({
                    "level": level,
                    "text": self._clean_heading_text(text),
                    "page": heading["page"],
                    "font_size": font_size,
                    "original_text": text
                })
        
        return classified
    
    def _determine_heading_level(self, text: str, font_size: float, level_map: Dict) -> Optional[str]:
        """
        Determine the heading level based on text content and formatting.
        
        Args:
            text: Heading text
            font_size: Font size
            level_map: Font size to level mapping
            
        Returns:
            Heading level (H1, H2, H3) or None
        """
        # Check numbered patterns for level hints
        numbered_patterns = [
            (r'^\d+\.\s', "H1"),  # "1. Introduction"
            (r'^\d+\.\d+\s', "H2"),  # "1.1 Overview"
            (r'^\d+\.\d+\.\d+\s', "H3"),  # "1.1.1 Details"
        ]
        
        for pattern, level in numbered_patterns:
            if re.match(pattern, text):
                return level
        
        # Check chapter/section patterns
        chapter_patterns = [
            (r'^Chapter\s+\d+', "H1"),
            (r'^Section\s+\d+', "H2"),
            (r'^Part\s+\d+', "H1"),
        ]
        
        for pattern, level in chapter_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return level
        
        # Use font size mapping
        if font_size in level_map:
            return level_map[font_size]
        
        # Default fallback based on font size
        if font_size >= 18:
            return "H1"
        elif font_size >= 14:
            return "H2"
        elif font_size >= 12:
            return "H3"
        
        return None
    
    def _clean_heading_text(self, text: str) -> str:
        """
        Clean heading text by removing numbering and extra whitespace.
        
        Args:
            text: Raw heading text
            
        Returns:
            Cleaned heading text
        """
        # Remove common heading prefixes
        patterns_to_remove = [
            r'^\d+\.\s*',  # "1. "
            r'^\d+\.\d+\s*',  # "1.1 "
            r'^\d+\.\d+\.\d+\s*',  # "1.1.1 "
            r'^Chapter\s+\d+:?\s*',  # "Chapter 1: "
            r'^Section\s+\d+:?\s*',  # "Section 1: "
            r'^Part\s+\d+:?\s*',  # "Part 1: "
            r'^[IVX]+\.\s*',  # "I. "
            r'^[A-Z]\.\s*',  # "A. "
        ]
        
        cleaned = text
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned if cleaned else text
    
    def _build_outline_hierarchy(self, classified_headings: List[Dict]) -> List[Dict[str, Any]]:
        """
        Build final outline hierarchy from classified headings.
        
        Args:
            classified_headings: List of classified headings
            
        Returns:
            List of outline items in proper hierarchy
        """
        outline = []
        
        # Sort by page number to maintain document order
        sorted_headings = sorted(classified_headings, key=lambda x: x["page"])
        
        # Remove duplicates and very similar headings
        unique_headings = self._remove_duplicate_headings(sorted_headings)
        
        # Build final outline
        for heading in unique_headings:
            outline_item = {
                "level": heading["level"],
                "text": heading["text"],
                "page": heading["page"]
            }
            outline.append(outline_item)
        
        return outline
    
    def _remove_duplicate_headings(self, headings: List[Dict]) -> List[Dict]:
        """
        Remove duplicate and very similar headings.
        
        Args:
            headings: List of headings
            
        Returns:
            List of unique headings
        """
        unique_headings = []
        seen_texts = set()
        
        for heading in headings:
            text = heading["text"].lower().strip()
            
            # Skip if we've seen this exact text
            if text in seen_texts:
                continue
            
            # Skip if very similar to existing heading
            is_similar = False
            for seen_text in seen_texts:
                if self._texts_are_similar(text, seen_text):
                    is_similar = True
                    break
            
            if not is_similar:
                unique_headings.append(heading)
                seen_texts.add(text)
        
        return unique_headings
    
    def _texts_are_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """
        Check if two texts are similar using simple string matching.
        
        Args:
            text1: First text
            text2: Second text
            threshold: Similarity threshold
            
        Returns:
            True if texts are similar
        """
        # Simple similarity check
        if abs(len(text1) - len(text2)) > 10:
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