#!/usr/bin/env python3
"""
Adobe Hackathon Round 1A - PDF Outline Extraction
Main entry point for processing PDFs and extracting structured outlines.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from pdf_parser import PDFParser
from outline_extractor import OutlineExtractor
from utils import setup_logging, validate_json_output

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFOutlineProcessor:
    """Main processor for PDF outline extraction."""
    
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.outline_extractor = OutlineExtractor()
        
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process a single PDF and extract its outline.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing title and outline structure
        """
        try:
            start_time = time.time()
            
            # Parse PDF and extract text with formatting
            logger.info(f"Parsing PDF: {pdf_path}")
            parsed_data = self.pdf_parser.parse_pdf(pdf_path)
            
            # Extract outline structure
            logger.info("Extracting outline structure...")
            outline_data = self.outline_extractor.extract_outline(parsed_data)
            
            processing_time = time.time() - start_time
            logger.info(f"Processing completed in {processing_time:.2f} seconds")
            
            return outline_data
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            raise
    
    def process_directory(self, input_dir: str, output_dir: str) -> None:
        """
        Process all PDFs in input directory and save results to output directory.
        
        Args:
            input_dir: Directory containing input PDFs
            output_dir: Directory to save JSON outputs
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all PDF files
        pdf_files = list(input_path.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {input_dir}")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF
        for pdf_file in pdf_files:
            try:
                logger.info(f"Processing: {pdf_file.name}")
                
                # Process the PDF
                result = self.process_pdf(str(pdf_file))
                
                # Generate output filename
                output_filename = pdf_file.stem + ".json"
                output_file = output_path / output_filename
                
                # Save results
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Results saved to: {output_file}")
                
                # Validate output format
                if validate_json_output(result):
                    logger.info("✅ JSON output validation passed")
                else:
                    logger.warning("⚠️  JSON output validation failed")
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file.name}: {str(e)}")
                continue

def main():
    """Main function - entry point for Docker container."""
    
    # Setup logging
    setup_logging()
    
    # Default paths for Docker container
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    # Check if running locally (for development)
    if not os.path.exists(input_dir):
        input_dir = "data/input"
        output_dir = "data/output"
        
        # Create directories if they don't exist
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info("🚀 Starting Adobe Hackathon Round 1A - PDF Outline Extraction")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    # Check if input directory exists and has PDFs
    if not os.path.exists(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    # Initialize processor
    processor = PDFOutlineProcessor()
    
    try:
        # Process all PDFs
        processor.process_directory(input_dir, output_dir)
        logger.info("✅ Processing completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Processing failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()