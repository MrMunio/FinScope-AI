import os
import time
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass

# LangChain imports
from langchain.schema import Document
from langchain.retrievers import BM25Retriever, TFIDFRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever as CommunityBM25Retriever

# Set OpenAI API key (you'll need to set this)
# os.environ["OPENAI_API_KEY"] = "your-api-key-here"

@dataclass
class TestResult:
    retriever_name: str
    accuracy: float
    avg_response_time: float
    correct_matches: int
    total_queries: int

class CompanyNameIndexingBench:
    def __init__(self):
        # 50 Fortune 500 style company names with variations
        self.company_names = [
            "Apple Inc.", "Microsoft Corporation", "Amazon.com Inc.", "Alphabet Inc.",
            "Tesla Inc.", "Meta Platforms Inc.", "NVIDIA Corporation", "Berkshire Hathaway Inc.",
            "UnitedHealth Group Incorporated", "Johnson & Johnson", "JPMorgan Chase & Co.",
            "Procter & Gamble Company", "Visa Inc.", "Home Depot Inc.", "Mastercard Incorporated",
            "Bank of America Corporation", "Pfizer Inc.", "Coca-Cola Company", "Walt Disney Company",
            "Cisco Systems Inc.", "Verizon Communications Inc.", "Comcast Corporation",
            "AT&T Inc.", "Intel Corporation", "Oracle Corporation", "Salesforce Inc.",
            "Netflix Inc.", "Adobe Inc.", "PayPal Holdings Inc.", "Broadcom Inc.",
            "Qualcomm Incorporated", "Texas Instruments Incorporated", "Advanced Micro Devices Inc.",
            "Intuit Inc.", "Applied Materials Inc.", "Lam Research Corporation", "Marvell Technology Inc.",
            "Analog Devices Inc.", "Micron Technology Inc.", "KLA Corporation",
            "Cadence Design Systems Inc.", "Synopsys Inc.", "Autodesk Inc.", "ServiceNow Inc.",
            "Workday Inc.", "Zoom Video Communications Inc.", "CrowdStrike Holdings Inc.",
            "Palantir Technologies Inc.", "Snowflake Inc.", "Datadog Inc."
        ]
        
        # Create test queries with variations
        self.test_queries = self._create_test_queries()
        
        # Initialize retrievers
        self.retrievers = {}
        self._setup_retrievers()
    
    def _create_test_queries(self) -> List[Tuple[str, str]]:
        """Create test queries with variations and their expected correct answers"""
        queries = []
        
        for company in self.company_names:
            # Original name
            queries.append((company, company))
            
            # Uppercase variation
            queries.append((company.upper(), company))
            
            # Lowercase variation
            queries.append((company.lower(), company))
            
            # Title case variation
            queries.append((company.title(), company))
            
            # Remove common suffixes for abbreviated queries
            abbreviated = company
            for suffix in [" Inc.", " Corporation", " Incorporated", " Company", " Co.", ".com"]:
                if abbreviated.endswith(suffix):
                    abbreviated = abbreviated.replace(suffix, "").strip()
                    break
            
            if abbreviated != company:
                queries.append((abbreviated, company))
                queries.append((abbreviated.upper(), company))
        
        return queries[:100]  # Limit to reasonable number for testing
    
    def _setup_retrievers(self):
        """Initialize all retrievers with company names"""
        # Convert company names to documents
        documents = [Document(page_content=name, metadata={"company": name}) for name in self.company_names]
        
        # 1. BM25 Retriever
        print("Setting up BM25 Retriever...")
        self.retrievers['BM25'] = BM25Retriever.from_documents(documents)
        self.retrievers['BM25'].k = 1
        
        # 2. TF-IDF Retriever
        print("Setting up TF-IDF Retriever...")
        self.retrievers['TF-IDF'] = TFIDFRetriever.from_documents(documents)
        self.retrievers['TF-IDF'].k = 1
        
        # 3. OpenAI Embeddings (if API key is available)
        try:
            print("Setting up OpenAI Embeddings...")
            openai_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            openai_vectorstore = FAISS.from_documents(documents, openai_embeddings)
            self.retrievers['OpenAI-Embeddings'] = openai_vectorstore.as_retriever(search_kwargs={"k": 1})
        except Exception as e:
            print(f"OpenAI Embeddings setup failed: {e}")
            print("Make sure to set OPENAI_API_KEY environment variable")
        
        # 4. HuggingFace Embeddings (smallest model)
        print("Setting up HuggingFace Embeddings...")
        try:
            hf_embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",  # Small, fast model
                model_kwargs={'device': 'cpu'}
            )
            hf_vectorstore = FAISS.from_documents(documents, hf_embeddings)
            self.retrievers['HuggingFace-MiniLM'] = hf_vectorstore.as_retriever(search_kwargs={"k": 1})
        except Exception as e:
            print(f"HuggingFace Embeddings setup failed: {e}")
        
        # 5. Alternative: Sentence Transformers with different model
        try:
            print("Setting up alternative HuggingFace model...")
            hf_embeddings_alt = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-MiniLM-L3-v2",  # Even smaller
                model_kwargs={'device': 'cpu'}
            )
            hf_vectorstore_alt = FAISS.from_documents(documents, hf_embeddings_alt)
            self.retrievers['HuggingFace-Paraphrase'] = hf_vectorstore_alt.as_retriever(search_kwargs={"k": 1})
        except Exception as e:
            print(f"Alternative HuggingFace model setup failed: {e}")
    
    def _test_retriever(self, retriever_name: str, retriever) -> TestResult:
        """Test a single retriever with all queries"""
        print(f"\nTesting {retriever_name}...")
        
        correct_matches = 0
        response_times = []
        
        for i, (query, expected) in enumerate(self.test_queries):
            start_time = time.time()
            
            try:
                # Get top result
                results = retriever.get_relevant_documents(query)
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                # Check if correct
                if results and len(results) > 0:
                    retrieved_company = results[0].page_content
                    if retrieved_company == expected:
                        correct_matches += 1
                    else:
                        print(f"  Miss: '{query}' -> '{retrieved_company}' (expected: '{expected}')")
                else:
                    print(f"  No result for: '{query}'")
                    
            except Exception as e:
                print(f"  Error for query '{query}': {e}")
                response_times.append(0)
            
            # Progress indicator
            if (i + 1) % 20 == 0:
                print(f"  Processed {i + 1}/{len(self.test_queries)} queries...")
        
        accuracy = correct_matches / len(self.test_queries)
        avg_response_time = np.mean(response_times) if response_times else 0
        
        return TestResult(
            retriever_name=retriever_name,
            accuracy=accuracy,
            avg_response_time=avg_response_time,
            correct_matches=correct_matches,
            total_queries=len(self.test_queries)
        )
    
    def run_benchmark(self) -> List[TestResult]:
        """Run benchmark on all available retrievers"""
        print("Starting Company Name Indexing Benchmark")
        print(f"Total company names: {len(self.company_names)}")
        print(f"Total test queries: {len(self.test_queries)}")
        print("=" * 60)
        
        results = []
        
        for name, retriever in self.retrievers.items():
            try:
                result = self._test_retriever(name, retriever)
                results.append(result)
            except Exception as e:
                print(f"Failed to test {name}: {e}")
        
        return results
    
    def print_results(self, results: List[TestResult]):
        """Print formatted benchmark results"""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)
        
        # Sort by accuracy
        results.sort(key=lambda x: x.accuracy, reverse=True)
        
        print(f"{'Retriever':<25} {'Accuracy':<10} {'Correct/Total':<15} {'Avg Time (ms)':<15}")
        print("-" * 80)
        
        for result in results:
            accuracy_pct = f"{result.accuracy:.1%}"
            correct_total = f"{result.correct_matches}/{result.total_queries}"
            avg_time_ms = f"{result.avg_response_time*1000:.2f}"
            
            print(f"{result.retriever_name:<25} {accuracy_pct:<10} {correct_total:<15} {avg_time_ms:<15}")
        
        print("-" * 80)
        print(f"Best performer: {results[0].retriever_name} ({results[0].accuracy:.1%} accuracy)")
        
        # Performance analysis
        print("\nPERFORMANCE ANALYSIS:")
        for result in results:
            if result.accuracy >= 0.9:
                performance = "Excellent"
            elif result.accuracy >= 0.8:
                performance = "Good"
            elif result.accuracy >= 0.7:
                performance = "Fair"
            else:
                performance = "Poor"
            
            print(f"- {result.retriever_name}: {performance} ({result.accuracy:.1%})")

def main():
    """Main function to run the benchmark"""
    print("Company Name Indexing Benchmark")
    print("This will test various retrieval methods for company name matching...")
    
    # Initialize benchmark
    bench = CompanyNameIndexingBench()
    
    # Run tests
    results = bench.run_benchmark()
    
    # Print results
    bench.print_results(results)
    
    # Additional insights
    print("\nRECOMMendations:")
    print("- BM25: Good for exact text matching and keyword-based queries")
    print("- TF-IDF: Similar to BM25 but may handle term frequency differently")
    print("- OpenAI Embeddings: Best for semantic similarity, handles variations well")
    print("- HuggingFace Models: Good balance of performance and cost")
    print("\nFor production use, consider:")
    print("1. Hybrid approach combining BM25 + embeddings")
    print("2. Preprocessing: normalize company names, handle suffixes")
    print("3. Fuzzy matching for typo tolerance")

if __name__ == "__main__":
    main()