import os
import base64
from typing import List, Optional
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io
from langchain_community.llms import Ollama
from langchain.schema import BaseMessage, HumanMessage
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFToMarkdownConverter:
    def __init__(self, model_name: str = "qwen2.5vl:3b", base_url: str = "http://localhost:11434"):
        """
        Initialize the PDF to Markdown converter.
        
        Args:
            model_name: Name of the Ollama vision model
            base_url: Base URL for Ollama API
        """
        self.model_name = model_name
        self.base_url = base_url
        self.llm = Ollama(
            model=model_name,
            base_url=base_url,
            temperature=0.1
        )
        
        # Prompt template for vision model
        self.vision_prompt = PromptTemplate(
            input_variables=["page_content"],
            template="""
You are an expert document analyzer. Please analyze this page image and convert it to clean, well-structured markdown format.

Instructions:
1. Extract all text content accurately
2. Preserve document structure (headings, paragraphs, lists, tables)
3. Use proper markdown syntax:
   - # for main headings
   - ## for subheadings
   - ### for sub-subheadings
   - **bold** for emphasis
   - *italic* for emphasis
   - - for bullet points
   - 1. for numbered lists
   - | table | format | for tables
4. Maintain logical flow and readability
5. If there are images, describe them briefly as [Image: description]
6. Ignore headers, footers, and page numbers unless they're part of the main content

Convert this page to markdown:

{page_content}
"""
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.vision_prompt)

    def pdf_to_images(self, pdf_path: str, dpi: int = 480) -> List[Image.Image]:
        """
        Convert PDF pages to images.
        
        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for image conversion
            
        Returns:
            List of PIL Image objects
        """
        logger.info(f"Converting PDF to images: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            images = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Convert page to image
                mat = fitz.Matrix(dpi/72, dpi/72)  # scaling factor
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
                
                logger.info(f"Converted page {page_num + 1}/{len(doc)}")
            
            doc.close()
            return images
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise

    def image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string.
        
        Args:
            image: PIL Image object
            
        Returns:
            Base64 encoded string
        """
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str

    def analyze_page_with_vision(self, image: Image.Image) -> str:
        """
        Analyze a single page image with the vision model.
        
        Args:
            image: PIL Image object
            
        Returns:
            Markdown content for the page
        """
        try:
            # Convert image to base64
            img_base64 = self.image_to_base64(image)
            
            # Create the prompt with image
            prompt_with_image = f"data:image/png;base64,{img_base64}"
            
            # Use the vision model to analyze the image
            response = self.llm.invoke(
                f"Analyze this document page and convert it to clean markdown format:\n\n{prompt_with_image}"
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error analyzing page with vision model: {str(e)}")
            return f"[Error processing page: {str(e)}]"

    def convert_pdf_to_markdown(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert entire PDF to markdown format.
        
        Args:
            pdf_path: Path to input PDF file
            output_path: Optional path for output markdown file
            
        Returns:
            Complete markdown content
        """
        logger.info(f"Starting PDF to Markdown conversion: {pdf_path}")
        
        # Convert PDF to images
        images = self.pdf_to_images(pdf_path)
        
        markdown_content = []
        
        # Process each page
        for i, image in enumerate(images):
            logger.info(f"Processing page {i + 1}/{len(images)}")
            
            # Analyze page with vision model
            page_markdown = self.analyze_page_with_vision(image)
            
            # Add page separator and content
            if i > 0:
                markdown_content.append("\n\n---\n\n")  # Page separator
            
            markdown_content.append(f"<!-- Page {i + 1} -->\n\n")
            markdown_content.append(page_markdown)
        
        # Combine all content
        final_markdown = "".join(markdown_content)
        
        # Save to file if output path provided
        if output_path:
            self.save_markdown(final_markdown, output_path)
        
        logger.info("PDF to Markdown conversion completed")
        return final_markdown

    def save_markdown(self, content: str, output_path: str):
        """
        Save markdown content to file.
        
        Args:
            content: Markdown content to save
            output_path: Path for output file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Markdown saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving markdown file: {str(e)}")
            raise

    def batch_convert(self, input_dir: str, output_dir: str):
        """
        Convert multiple PDF files in a directory.
        
        Args:
            input_dir: Directory containing PDF files
            output_dir: Directory for output markdown files
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
        
        logger.info(f"Found {len(pdf_files)} PDF files to convert")
        
        for pdf_file in pdf_files:
            try:
                output_file = output_path / f"{pdf_file.stem}.md"
                logger.info(f"Converting: {pdf_file.name}")
                
                self.convert_pdf_to_markdown(str(pdf_file), str(output_file))
                
            except Exception as e:
                logger.error(f"Error converting {pdf_file.name}: {str(e)}")
                continue

def main():
    parser = argparse.ArgumentParser(description="Convert PDF files to Markdown using Qwen2.5-VL vision model")
    parser.add_argument("--input", "-i", required=True, help="Input PDF file or directory")
    parser.add_argument("--output", "-o", help="Output markdown file or directory")
    parser.add_argument("--model", "-m", default="qwen2.5-vl:3b", help="Ollama model name")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--batch", action="store_true", help="Batch process directory")
    
    args = parser.parse_args()
    
    # Initialize converter
    converter = PDFToMarkdownConverter(
        model_name=args.model,
        base_url=args.base_url
    )
    
    try:
        if args.batch:
            # Batch conversion
            output_dir = args.output or "output_markdown"
            converter.batch_convert(args.input, output_dir)
        else:
            # Single file conversion
            input_path = Path(args.input)
            if args.output:
                output_path = args.output
            else:
                output_path = input_path.stem + ".md"
            
            markdown_content = converter.convert_pdf_to_markdown(args.input, output_path)
            print(f"Conversion completed. Output saved to: {output_path}")
            
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Initialize converter
    converter = PDFToMarkdownConverter(
        model_name="qwen2.5vl:3b",
        base_url="http://localhost:11434"
    )
    # Single file conversion
    input_path = Path(r"assets\reports\pdfs\cognizant_annual_report_micro.pdf")
    output_path = input_path.stem + ".md"
    markdown_content = converter.convert_pdf_to_markdown(input_path, output_path)
    print(f"Conversion completed. Output saved to: {output_path}")


# Example usage for main():
"""
# Single file conversion
python pdf_to_markdown.py --input "assets\reports\pdfs\cognizant_annual_report_small.pdf" --output "assets\reports\pdfs/document.md"

# Batch conversion
python pdf_to_markdown.py --input ./pdfs/ --output ./markdown/ --batch

# Using different model
python pdf_to_markdown.py --input document.pdf --model qwen2.5-vl:7b

# Using different Ollama server
python pdf_to_markdown.py --input document.pdf --base-url http://192.168.1.100:11434
"""