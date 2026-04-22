"""updated with pdf report generation"""
from langgraph.checkpoint.memory import InMemorySaver
from researcher.agents.supervisor import corporate_researcher_v2
import chainlit as cl
from langchain_core.messages import HumanMessage
import re
from pathlib import Path
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from bs4 import BeautifulSoup
import logging

# Global configuration
PDF_FONT_FAMILY = "Helvetica"  # Options: Helvetica, Times-Roman, Courier
PDF_MARGIN = 0.75 * inch
HEADING1_SIZE = 18
HEADING2_SIZE = 14
HEADING3_SIZE = 12
BODY_TEXT_SIZE = 10

thread_counter = 1
logger = logging.getLogger(__name__)

def markdown_to_pdf(txt_file_path: str) -> str:
    """Convert markdown txt file to styled PDF"""
    try:
        pdf_path = txt_file_path.replace('.txt', '.pdf')
        
        # Read markdown content
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(md_content)
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Create PDF
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=PDF_MARGIN,
            leftMargin=PDF_MARGIN,
            topMargin=PDF_MARGIN,
            bottomMargin=PDF_MARGIN
        )
        
        # Create custom styles
        styles = getSampleStyleSheet()
        
        # Custom styles for different elements
        h1_style = ParagraphStyle(
            'CustomH1',
            parent=styles['Heading1'],
            fontName=f"{PDF_FONT_FAMILY}-Bold",
            fontSize=HEADING1_SIZE,
            spaceAfter=12,
            textColor='black'
        )
        
        h2_style = ParagraphStyle(
            'CustomH2',
            parent=styles['Heading2'],
            fontName=f"{PDF_FONT_FAMILY}-Bold",
            fontSize=HEADING2_SIZE,
            spaceAfter=10,
            textColor='black'
        )
        
        h3_style = ParagraphStyle(
            'CustomH3',
            parent=styles['Heading3'],
            fontName=f"{PDF_FONT_FAMILY}-Bold",
            fontSize=HEADING3_SIZE,
            spaceAfter=8,
            textColor='black'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontName=PDF_FONT_FAMILY,
            fontSize=BODY_TEXT_SIZE,
            spaceAfter=6,
            textColor='black',
            alignment=TA_LEFT
        )
        
        bold_style = ParagraphStyle(
            'CustomBold',
            parent=body_style,
            fontName=f"{PDF_FONT_FAMILY}-Bold"
        )
        
        # Build PDF content
        story = []
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'strong', 'ul', 'ol']):
            if element.name == 'h1':
                story.append(Paragraph(element.get_text(), h1_style))
                story.append(Spacer(1, 0.2*inch))
            elif element.name == 'h2':
                story.append(Paragraph(element.get_text(), h2_style))
                story.append(Spacer(1, 0.15*inch))
            elif element.name == 'h3':
                story.append(Paragraph(element.get_text(), h3_style))
                story.append(Spacer(1, 0.1*inch))
            elif element.name == 'p':
                text = str(element)
                # Handle bold text
                text = text.replace('<strong>', f'<b>')
                text = text.replace('</strong>', '</b>')
                text = text.replace('<p>', '').replace('</p>', '')
                story.append(Paragraph(text, body_style))
                story.append(Spacer(1, 0.1*inch))
            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li'):
                    bullet = '•' if element.name == 'ul' else f"{list(element.find_all('li')).index(li) + 1}."
                    story.append(Paragraph(f"{bullet} {li.get_text()}", body_style))
                story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(story)
        logger.info(f"Successfully converted {txt_file_path} to {pdf_path}")
        return pdf_path
        
    except Exception as e:
        logger.error(f"Error converting markdown to PDF: {str(e)}")
        return None

@cl.on_chat_start
async def initialize_chat():
    global thread_counter
    corporate_researcher_v2.checkpointer = InMemorySaver()
    cl.user_session.set("thread_id", thread_counter)
    thread_counter += 1

@cl.on_message
async def on_message(msg: cl.Message):
    state_input = {"messages": [HumanMessage(content=msg.content)]}
    config = {"configurable": {"thread_id": cl.user_session.get("thread_id")}}
    response = await corporate_researcher_v2.ainvoke(state_input, config=config)
    last_msg = response["messages"][-1].content
    
    # Check for file path pattern
    match = re.search(r'\*\*(.*?)\.txt\*\*', last_msg)
    if match:
        file_path = match.group(1) + ".txt"
        file = Path(file_path)
        
        if file.exists():
            logger.info(f"Found report file at {file_path}, preparing to send.")
            # Remove the file path from the message
            filtered_msg = re.sub(r'\*\*.*?\.txt\*\*', '', last_msg).strip()
            
            # Send the filtered message
            await cl.Message(content=filtered_msg).send()
            
            # Try to convert to PDF
            logger.info(f"Starting process of converting report to PDF format")
            pdf_path = markdown_to_pdf(str(file))
            logger.info(f"PDF conversion process completed with path: {pdf_path}")
            
            if pdf_path and Path(pdf_path).exists():
                # Send PDF download link
                pdf_file = Path(pdf_path)
                sent_msg = await cl.Message(content=f"📄 [Download Report (PDF)]({pdf_file.name})").send()
                await cl.File(name=pdf_file.name, path=str(pdf_file)).send(for_id=sent_msg.id)
            else:
                # Fallback to TXT file
                logger.warning(f"PDF conversion failed, falling back to TXT file")
                sent_msg = await cl.Message(content=f"📎 [Download Report (TXT)]({file.name})").send()
                await cl.File(name=file.name, path=str(file)).send(for_id=sent_msg.id)
            return
    
    await cl.Message(content=last_msg).send()