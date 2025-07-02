import os
import glob
from typing import List
from langchain.schema import Document
from langchain_community.retrievers import BM25Retriever,TFIDFRetriever
from langchain_core.tools import tool

import nltk
nltk.download("punkt_tab")
from nltk.tokenize import word_tokenize

# Setup the system
REPORTS_FOLDER = r"assets\reports\markdown_files"

class CompanyFinancialRetriever:
    """
    A lexical-based retrieval system for company financial reports using TF-IDF Vectorizer.
    Indexes only company names and returns full documents.
    """
    
    def __init__(self, reports_folder_path: str,):
        self.reports_folder_path = reports_folder_path
        self.documents = []
        self.company_names = []
        self.retriever = None
        self.build_index()

        
    def preprocess_company_name(self, company_name: str) -> str:
        """
        Preprocess company name for better matching.
        Removes common corporate suffixes and normalizes text.
        """
        # Convert to lowercase for processing
        processed = company_name.lower()
        
        # Remove common corporate suffixes that might interfere with matching
        suffixes_to_remove = [
            'corporation', 'corp', 'inc', 'incorporated', 'ltd', 'limited', 
            'llc', 'llp', 'lp', 'company', 'co', 'group', 'holdings'
        ]
        
        words = processed.split()
        filtered_words = []
        
        for word in words:
            # Remove punctuation and check if it's a suffix
            clean_word = word.strip('.,()[]{}')
            if clean_word not in suffixes_to_remove:
                filtered_words.append(clean_word)
        
        return ' '.join(filtered_words)
    
    def load_documents(self) -> List[Document]:
        """Load all markdown files and extract company names from first line."""
        documents = []
        company_names = []
        
        # Get all .md files in the folder
        md_files = glob.glob(os.path.join(self.reports_folder_path, "*.md"))
        
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                    # Extract company name from first line
                    lines = content.strip().split('\n')
                    if lines:
                        company_name = lines[0].strip()
                        
                        # Create both original and preprocessed versions for better matching
                        preprocessed_name = self.preprocess_company_name(company_name)
                        
                        # Create document with both original and preprocessed names for indexing
                        # This helps with partial matching
                        combined_content = f"{company_name} {preprocessed_name}"
                        
                        # Create document with company name as page_content for indexing
                        # but store full content in metadata
                        doc = Document(
                            page_content=combined_content,  # Index both original and processed
                            metadata={
                                'company_name': company_name,
                                'preprocessed_name': preprocessed_name,
                                'file_path': file_path,
                                'full_content': content  # Store full document here
                            }
                        )
                        
                        documents.append(doc)
                        company_names.append(company_name)
                        
            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")
                
        self.documents = documents
        self.company_names = company_names
        # print(f"Loaded {len(documents)} company reports")
        return documents
    
    def build_index(self):
        """Build BM25 index on company names."""
        if not self.documents:
            self.load_documents()
            
        # Create  retriever - this will index the page_content (company names)
        self.retriever = TFIDFRetriever.from_documents(self.documents,preprocess_func=word_tokenize)

        print("index built successfully")
    

# create retriever tool
retriever_system=CompanyFinancialRetriever(REPORTS_FOLDER)
document_retriever = retriever_system.retriever

# build document retriver wrapper function for sub agent 2 to use as a tool
@tool
def retrieve_docs(company_name:str):
    """A retriever tool to fetch financial records of any company from DB. This tool uses company name as query and finds the top matching company name and its financial records from system DB."""
    document_retriever.k=1 # default chunks to return
    result_docs = document_retriever.invoke(company_name)
    formated_results = []
    for doc in result_docs:
        metadata=doc.metadata
        company_name = metadata.get("company_name", "Unknown Company")
        full_content = metadata.get("full_content", "No content available")
        formated_results.append(
            f"Company: {company_name}\nContent:\n{full_content}\n"+"--"*50
        )
    return "\n\n".join(formated_results) if formated_results else "No documents found"

if __name__ == "__main__":
    # agent tool test
    query="tcs"
    result = retrieve_docs(query)
    print(result[:500] + "..." if len(result) > 500 else result)
