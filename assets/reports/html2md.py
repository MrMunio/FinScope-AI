import os
from pathlib import Path
try:
    import html2text
except ImportError:
    print("html2text not installed. Install with: pip install html2text")
    exit(1)

def html_to_markdown(html_file_path, markdown_file_path=None, **kwargs):
    """
    Convert HTML file to Markdown format and save it.
    
    Args:
        html_file_path (str): Path to the input HTML file
        markdown_file_path (str, optional): Path for output Markdown file.
                                          If None, uses same name with .md extension
        **kwargs: Additional options for html2text converter
                 - body_width: Maximum line width (default: 0 for no wrapping)
                 - ignore_links: Ignore link tags (default: False)
                 - ignore_images: Ignore image tags (default: False)
                 - single_line_break: Use single line breaks (default: False)
    
    Returns:
        str: Path to the created Markdown file
    
    Raises:
        FileNotFoundError: If HTML file doesn't exist
        Exception: For other conversion errors
    """
    
    # Check if HTML file exists
    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"HTML file not found: {html_file_path}")
    
    # Generate output path if not provided
    if markdown_file_path is None:
        html_path = Path(html_file_path)
        markdown_file_path = html_path.with_suffix('.md')
    
    try:
        # Read HTML file
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Configure html2text converter
        h = html2text.HTML2Text()
        
        # Set default options
        h.body_width = kwargs.get('body_width', 0)  # No line wrapping by default
        h.ignore_links = kwargs.get('ignore_links', False)
        h.ignore_images = kwargs.get('ignore_images', False)
        h.single_line_break = kwargs.get('single_line_break', False)
        h.unicode_snob = True  # Better Unicode handling
        h.decode_errors = 'ignore'
        
        # Convert HTML to Markdown
        markdown_content = h.handle(html_content)
        
        # Write Markdown file
        with open(markdown_file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Successfully converted '{html_file_path}' to '{markdown_file_path}'")
        return str(markdown_file_path)
        
    except Exception as e:
        raise Exception(f"Error converting HTML to Markdown: {str(e)}")

def batch_html_to_markdown(input_directory, output_directory=None, **kwargs):
    """
    Convert multiple HTML files in a directory to Markdown.
    
    Args:
        input_directory (str): Directory containing HTML files
        output_directory (str, optional): Directory for output files.
                                        If None, uses same directory
        **kwargs: Additional options passed to html_to_markdown
    
    Returns:
        list: Paths to created Markdown files
    """
    
    if not os.path.exists(input_directory):
        raise FileNotFoundError(f"Input directory not found: {input_directory}")
    
    if output_directory and not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    html_files = []
    for ext in ['*.html', '*.htm']:
        html_files.extend(Path(input_directory).glob(ext))
    
    if not html_files:
        print(f"No HTML files found in {input_directory}")
        return []
    
    converted_files = []
    for html_file in html_files:
        try:
            if output_directory:
                output_path = Path(output_directory) / f"{html_file.stem}.md"
            else:
                output_path = None
            
            result = html_to_markdown(str(html_file), str(output_path) if output_path else None, **kwargs)
            converted_files.append(result)
            
        except Exception as e:
            print(f"Failed to convert {html_file}: {e}")
    
    return converted_files

# Example usage
if __name__ == "__main__":
    # Single file conversion
    try:
        # html_to_markdown("example.html")
        
        # # With custom options
        # html_to_markdown(
        #     "example.html", 
        #     "output.md",
        #     body_width=80,
        #     ignore_images=True
        # )
        
        # Batch conversion
        batch_html_to_markdown(r"assets\reports\html_files", r"assets\reports\markdown_files")
        
    except Exception as e:
        print(f"Error: {e}")