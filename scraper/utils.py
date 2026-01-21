import PyPDF2
from typing import Optional


def read_resume(resume_file_path: str) -> Optional[str]:
    """
    Read resume content from file (supports .txt and .pdf)
    
    Args:
        resume_file_path: Path to resume file
        
    Returns:
        Resume content as string, or None if error
    """
    try:
        # Check file extension
        if resume_file_path.lower().endswith('.pdf'):
            # Read PDF file
            with open(resume_file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                resume_content = ""
                for page in pdf_reader.pages:
                    resume_content += page.extract_text() + "\n"
            print(f"✅ Resume loaded from PDF '{resume_file_path}' ({len(pdf_reader.pages)} pages)")
        else:
            # Read text file
            with open(resume_file_path, 'r', encoding='utf-8') as f:
                resume_content = f.read()
            print(f"✅ Resume loaded from '{resume_file_path}'")
        
        return resume_content.strip()
        
    except FileNotFoundError:
        print(f"❌ Resume file not found: {resume_file_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading resume: {e}")
        return None