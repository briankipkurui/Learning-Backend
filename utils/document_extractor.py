import io
try:
    import PyPDF2
    import docx2txt
    DOCUMENT_PARSING_AVAILABLE = True
except ImportError:
    DOCUMENT_PARSING_AVAILABLE = False

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file content"""
    if not DOCUMENT_PARSING_AVAILABLE:
        raise ValueError("PDF parsing not available. Install PyPDF2: pip install PyPDF2")
    
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file content"""
    if not DOCUMENT_PARSING_AVAILABLE:
        raise ValueError("DOCX parsing not available. Install docx2txt: pip install docx2txt")
    
    try:
        docx_file = io.BytesIO(file_content)
        text = docx2txt.process(docx_file)
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")

def extract_text_from_file(file_content: bytes, content_type: str) -> str:
    """Extract text from file based on content type"""
    content_type = content_type.lower()
    
    if content_type in ['application/pdf', 'pdf']:
        return extract_text_from_pdf(file_content)
    elif content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'docx']:
        return extract_text_from_docx(file_content)
    elif content_type in ['text/plain', 'txt']:
        return file_content.decode('utf-8')
    else:
        raise ValueError(f"Unsupported file type: {content_type}")

def process_document_input(text_input: str = None, 
                         file_content: bytes = None, 
                         file_type: str = None) -> str:
    """
    Process document input and return text content.
    
    Args:
        text_input: Direct text content (takes priority if provided)
        file_content: File content as bytes
        file_type: Content type of the file
    
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If no valid input provided or file processing fails
    """
    if text_input:
        return text_input.strip()
    elif file_content and file_type:
        return extract_text_from_file(file_content, file_type)
    else:
        raise ValueError("Either text_input or both file_content and file_type must be provided")