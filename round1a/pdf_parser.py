#!/usr/bin/env python3
"""
PDF Parser for Adobe Hackathon Round 1A
Extracts text with formatting information from PDFs using PyMuPDF.
"""

import fitz  # PyMuPDF
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFParser:
    """Parser for extracting structured text from PDF documents."""
    
    def __init__(self):
        self.doc = None
        self.page_count = 0
        
    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse PDF and extract text with formatting information.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing parsed text data with formatting info
        """
        try:
            # Open PDF document
            self.doc = fitz.open(pdf_path)
            self.page_count = len(self.doc)
            
            logger.info(f"PDF opened successfully: {self.page_count} pages")
            
            # Extract text from all pages
            pages_data = []
            title = self._extract_title()
            
            for page_num in range(self.page_count):
                page_data = self._extract_page_text(page_num)
                pages_data.append(page_data)
            
            # Close document
            self.doc.close()
            
            return {
                "title": title,
                "page_count": self.page_count,
                "pages": pages_data
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            if self.doc:
                self.doc.close()
            raise
    
    def _extract_title(self) -> str:
        """
        Extract document title from PDF metadata or first page.
        
        Returns:
            Document title string
        """
        try:
            # Try to get title from metadata first
            metadata = self.doc.metadata
            if metadata.get("title"):
                title = metadata["title"].strip()
                if title and len(title) > 3:  # Basic validation
                    return title
            
            # If no metadata title, extract from first page
            if self.page_count > 0:
                page = self.doc[0]
                blocks = page.get_text("dict")["blocks"]
                
                # Look for title in the first few blocks
                for block in blocks[:5]:  # Check first 5 blocks
                    if block.get("type") == 0:  # Text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text = span.get("text", "").strip()
                                font_size = span.get("size", 0)
                                
                                # Title is usually large font size and at the top
                                if (font_size > 14 and 
                                    len(text) > 5 and 
                                    len(text) < 100 and
                                    not text.lower().startswith(("page", "chapter", "section"))):
                                    return text
                
                # Fallback: use first meaningful text
                first_text = self._get_first_meaningful_text(page)
                if first_text:
                    return first_text
            
            return "Untitled Document"
            
        except Exception as e:
            logger.warning(f"Error extracting title: {str(e)}")
            return "Untitled Document"
    
    def _get_first_meaningful_text(self, page) -> Optional[str]:
        """Get first meaningful text from a page."""
        try:
            text = page.get_text()
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if len(line) > 5 and not line.isdigit():
                    return line
            
            return None
            
        except Exception:
            return None
    
    def _extract_page_text(self, page_num: int) -> Dict[str, Any]:
        """
        Extract text with formatting from a specific page.
        
        Args:
            page_num: Page number (0-based)
            
        Returns:
            Dictionary containing page text with formatting info
        """
        try:
            page = self.doc[page_num]
            page_dict = page.get_text("dict")
            
            text_blocks = []
            
            for block in page_dict["blocks"]:
                if block.get("type") == 0:  # Text block
                    block_data = self._process_text_block(block, page_num + 1)
                    if block_data:
                        text_blocks.extend(block_data)
            
            return {
                "page_number": page_num + 1,
                "text_blocks": text_blocks
            }
            
        except Exception as e:
            logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
            return {
                "page_number": page_num + 1,
                "text_blocks": []
            }
    
    def _process_text_block(self, block: Dict, page_num: int) -> List[Dict[str, Any]]:
        """
        Process a text block and extract formatting information.
        
        Args:
            block: Text block dictionary from PyMuPDF
            page_num: Page number (1-based)
            
        Returns:
            List of text elements with formatting info
        """
        text_elements = []
        
        try:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    
                    if not text:
                        continue
                    
                    # Extract formatting information
                    font_info = {
                        "font": span.get("font", ""),
                        "size": span.get("size", 0),
                        "flags": span.get("flags", 0),  # Bold, italic, etc.
                        "color": span.get("color", 0),
                        "bbox": span.get("bbox", [])
                    }
                    
                    # Determine if text is bold, italic, etc.
                    formatting = self._analyze_formatting(font_info)
                    
                    text_element = {
                        "text": text,
                        "page": page_num,
                        "font_size": font_info["size"],
                        "font_name": font_info["font"],
                        "is_bold": formatting["is_bold"],
                        "is_italic": formatting["is_italic"],
                        "bbox": font_info["bbox"],
                        "likely_heading": self._is_likely_heading(text, font_info)
                    }
                    
                    text_elements.append(text_element)
            
            return text_elements
            
        except Exception as e:
            logger.warning(f"Error processing text block: {str(e)}")
            return []
    
    def _analyze_formatting(self, font_info: Dict) -> Dict[str, bool]:
        """
        Analyze font formatting flags.
        
        Args:
            font_info: Font information dictionary
            
        Returns:
            Dictionary with formatting flags
        """
        flags = font_info.get("flags", 0)
        
        return {
            "is_bold": bool(flags & 16),  # Bold flag
            "is_italic": bool(flags & 2),  # Italic flag
            "is_superscript": bool(flags & 1),
            "is_subscript": bool(flags & 4)
        }
    
    def _is_likely_heading(self, text: str, font_info: Dict) -> bool:
        """
        Determine if text is likely a heading based on formatting and content.
        
        Args:
            text: Text content
            font_info: Font information
            
        Returns:
            True if likely a heading
        """
        # Check font size (headings are usually larger)
        font_size = font_info.get("size", 0)
        if font_size >= 14:
            return True
        
        # Check for heading patterns
        heading_patterns = [
            r'^\d+\.\s',  # "1. Introduction"
            r'^\d+\.\d+\s',  # "1.1 Overview"
            r'^[A-Z][A-Z\s]+$',  # "INTRODUCTION"
            r'^Chapter\s\d+',  # "Chapter 1"
            r'^Section\s\d+',  # "Section 1"
            r'^[IVX]+\.\s',  # Roman numerals
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True
        
        # Check if text is short and title-case
        if (len(text) < 100 and 
            text.istitle() and 
            not text.endswith('.') and
            len(text.split()) <= 8):
            return True
        
        return False