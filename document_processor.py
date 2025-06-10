"""
Document processor for StudyBuddy.
This module handles uploading, parsing, and extracting information from documents.
"""

import os
import tempfile
from typing import Dict, List, Optional
import re
import string

class DocumentProcessor:
    """
    Processes documents for the StudyBuddy application.
    Supports text extraction and simple question generation.
    """
    
    def __init__(self):
        """Initialize the document processor"""
        self.supported_extensions = ['.txt', '.md']
        self.documents = {}  # Store loaded documents
        self.current_document = None
        
    def load_document(self, file_path: str) -> bool:
        """
        Load a document from a file path
        
        Args:
            file_path: Path to the document file
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return False
            
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.supported_extensions:
            print(f"Unsupported file extension: {ext}")
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            doc_name = os.path.basename(file_path)
            self.documents[doc_name] = {
                'content': content,
                'path': file_path,
                'sections': self._split_into_sections(content)
            }
            self.current_document = doc_name
            return True
        except Exception as e:
            print(f"Error loading document: {e}")
            return False
    
    def get_current_document_content(self) -> str:
        """
        Get the content of the current document
        
        Returns:
            str: Document content or empty string if no document is loaded
        """
        if not self.current_document or self.current_document not in self.documents:
            return ""
        return self.documents[self.current_document]['content']
    
    def get_document_summary(self) -> str:
        """
        Generate a simple summary of the current document
        
        Returns:
            str: Summary text
        """
        if not self.current_document or self.current_document not in self.documents:
            return "No document loaded"
            
        content = self.documents[self.current_document]['content']
        # Simple summary - first paragraph and length info
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        if not non_empty_lines:
            return "Document is empty"
            
        first_para = ""
        for line in non_empty_lines:
            if line.strip():
                first_para += line + " "
            else:
                break
                
        word_count = len(content.split())
        
        return (f"Document: {self.current_document}\n"
                f"Word count: {word_count}\n\n"
                f"Preview: {first_para[:150]}...")
    
    def generate_questions(self, num_questions: int = 3) -> List[Dict[str, str]]:
        """
        Generate simple questions based on the document content
        
        Args:
            num_questions: Number of questions to generate
            
        Returns:
            List of dictionaries with 'question' and 'answer' keys
        """
        if not self.current_document or self.current_document not in self.documents:
            return []
            
        sections = self.documents[self.current_document]['sections']
        if not sections:
            return []
            
        # Simple question generation based on sections
        questions = []
        for section in sections[:num_questions]:
            title = section.get('title', '')
            content = section.get('content', '')
            
            if not title or not content:
                continue
                
            # Generate a simple question from the title
            question = self._title_to_question(title)
            
            # Take the first sentence as the answer
            sentences = content.split('.')
            answer = sentences[0] if sentences else content[:100]
            
            questions.append({
                'question': question,
                'answer': answer.strip()
            })
            
        return questions
    
    def _split_into_sections(self, content: str) -> List[Dict[str, str]]:
        """
        Split document content into sections based on headings
        
        Args:
            content: Document content
            
        Returns:
            List of dictionaries with 'title' and 'content' keys
        """
        # Simple section splitting using markdown-style headings
        lines = content.split('\n')
        sections = []
        
        current_title = None
        current_content = []
        
        for line in lines:
            # Check if the line is a heading (markdown style)
            if line.startswith('#'):
                # Save previous section if it exists
                if current_title is not None:
                    sections.append({
                        'title': current_title,
                        'content': '\n'.join(current_content).strip()
                    })
                
                # Start a new section
                current_title = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add the last section
        if current_title is not None:
            sections.append({
                'title': current_title,
                'content': '\n'.join(current_content).strip()
            })
        elif current_content:
            # If no headings were found, create a default section
            sections.append({
                'title': 'Main Content',
                'content': '\n'.join(current_content).strip()
            })
            
        return sections
    
    def _title_to_question(self, title: str) -> str:
        """
        Convert a section title to a question
        
        Args:
            title: Section title
            
        Returns:
            str: A question based on the title
        """
        # Remove punctuation
        title = title.translate(str.maketrans('', '', string.punctuation))
        title = title.strip()
        
        # Simple title to question conversion
        if title.lower().startswith(('what', 'when', 'where', 'who', 'why', 'how')):
            # It's already question-like, just add a question mark
            return f"{title}?"
        
        # Try to form a question
        words = title.split()
        if len(words) == 0:
            return "What is this section about?"
            
        if title.lower().startswith(('the', 'a', 'an')):
            # For titles starting with articles
            return f"What is {title}?"
        
        return f"Can you explain what {title} means?"

    def clear_documents(self):
        """Clear all loaded documents"""
        self.documents = {}
        self.current_document = None
