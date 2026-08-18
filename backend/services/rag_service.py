"""
Simple RAG (Retrieval-Augmented Generation) service for health Q&A.

Pipeline Logic:
1. Query Classification:
   - Document query (guideline, how-to, evidence, research) → Use document RAG
   - Personal query (my health, my condition, advice for me) → Use personal data
   - Both → Combine both sources

2. Response Generation:
   - Retrieve relevant documents (if applicable)
   - Include personal health context (if available)
   - Add SDOH reasoning for health equity context
   - Generate LLM response

3. SDOH Integration:
   - Analyze SDOH scores for health barriers
   - Provide context-aware recommendations
   - Address social determinants in guidance
"""

import os
import logging
import importlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

logger = logging.getLogger(__name__)

DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "documents" / "uploads"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


class RAGService:
    """Simple RAG service with document + personal data + SDOH reasoning."""
    
    def __init__(self, groq_api_key: str, model_name: str = "openai/gpt-oss-120b"):
        """Initialize RAG service."""
        self.model_name = model_name
        self.documents = []
        self.vector_store = None
        self.retriever = None
        self.llm = None
        self.embeddings = None
        
        try:
            self.llm = self._build_llm(groq_api_key, model_name)
            if self.llm is None:
                logger.info("✓ Demo mode: Using mock LLM")
            else:
                logger.info(f"✓ LLM initialized: {model_name}")
            
            # Initialize embeddings (works offline)
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            logger.info("✓ Embeddings initialized")
            
            # Load documents
            self._load_documents()
            
        except Exception as e:
            logger.error(f"RAG initialization error: {str(e)}")
            self.llm = None
            self.embeddings = None
    
    def _detect_provider(self, model_name: str) -> str:
        """Determine which LLM backend should be used."""
        if model_name and model_name.startswith("openai/"):
            return "openai"
        return "groq"

    def _build_llm(self, api_key: str, model_name: str):
        """Build an LLM client compatible with either Groq or OpenAI-style models."""
        provider = self._detect_provider(model_name)
        key = (api_key or "").strip()

        if not key or key == "demo_mode":
            return None

        try:
            if provider == "openai":
                try:
                    from langchain_openai import ChatOpenAI
                except Exception as exc:  # pragma: no cover
                    logger.warning(f"OpenAI backend unavailable: {exc}")
                    return None

                openai_key = os.getenv("OPENAI_API_KEY", key)
                if not openai_key or openai_key == "demo_mode":
                    return None

                base_url = os.getenv("OPENAI_BASE_URL")
                return ChatOpenAI(
                    model=model_name.replace("openai/", ""),
                    api_key=openai_key,
                    base_url=base_url,
                    temperature=0.7,
                    max_tokens=1024,
                )

            try:
                from langchain_groq import ChatGroq
            except Exception as exc:  # pragma: no cover
                logger.warning(f"Groq backend unavailable: {exc}")
                return None

            return ChatGroq(
                groq_api_key=key,
                model_name=model_name,
                temperature=0.7,
                max_tokens=1024,
            )
        except Exception as exc:
            logger.warning(f"LLM initialization fallback disabled: {exc}")
            return None

    def _demo_response(self, question: str, context: Optional[str] = None) -> str:
        """Provide a lightweight rule-based response when the LLM is unavailable."""
        question_low = (question or "").lower()
        if "diabetes" in question_low:
            answer = "Diabetes risk should be assessed using HbA1c, glucose, BMI, weight, and history indicators. Monitor glucose, prioritize nutrition, activity, and routine follow-up."
        elif "blood pressure" in question_low or "hypertension" in question_low or "highbp" in question_low:
            answer = "Hypertension risk is often driven by age, BMI, cholesterol, smoking, and access-to-care factors. Encourage blood pressure tracking, sodium reduction, activity, and routine clinical review."
        elif "heart" in question_low:
            answer = "Heart disease risk is influenced by cholesterol, blood pressure, smoking, obesity, and glucose patterns. Aim for regular activity, heart-healthy nutrition, and preventive checkups."
        else:
            answer = "This health guidance should be interpreted with the patient’s medical record and local clinical protocols. Focus on evidence-based lifestyle changes, monitoring, and follow-up care."

        if context:
            return f"{answer}\n\nContext used: {context[:500]}"
        return answer

    def generate_response(self, question: str, context: Optional[str] = None) -> str:
        """Generate a direct answer for a question using the configured LLM or fallback demo logic."""
        if not question:
            return ""

        if self.llm is None:
            return self._demo_response(question, context)

        try:
            prompt_parts = []
            if context:
                prompt_parts.append(f"Context:\n{context}")
            prompt_parts.append(f"Question:\n{question}\n\nProvide concise, evidence-based guidance.")
            response = self.llm.invoke("\n\n".join(prompt_parts))
            return response.content if hasattr(response, "content") else str(response)
        except Exception as exc:
            logger.warning(f"LLM generation failed, using fallback response: {exc}")
            return self._demo_response(question, context)

    def _load_documents(self) -> None:
        """Load documents from documents/uploads directory."""
        try:
            if not DOCUMENTS_DIR.exists():
                logger.warning(f"Documents directory not found: {DOCUMENTS_DIR}")
                return
            
            # Load text files
            txt_loader = DirectoryLoader(
                str(DOCUMENTS_DIR),
                glob="*.txt",
                loader_cls=TextLoader,
                show_progress=False
            )
            txt_docs = txt_loader.load()
            logger.info(f"Loaded {len(txt_docs)} text documents")
            
            # Load PDF files
            pdf_docs = []
            try:
                pdf_loader = DirectoryLoader(
                    str(DOCUMENTS_DIR),
                    glob="*.pdf",
                    loader_cls=PyPDFLoader,
                    show_progress=False
                )
                pdf_docs = pdf_loader.load()
                logger.info(f"Loaded {len(pdf_docs)} PDF documents")
            except Exception as e:
                logger.debug(f"No PDFs or PDF loading error: {str(e)}")
            
            all_docs = txt_docs + pdf_docs
            
            if not all_docs:
                logger.warning("No documents found in documents/uploads/")
                return
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", " ", ""]
            )
            self.documents = text_splitter.split_documents(all_docs)
            logger.info(f"Split into {len(self.documents)} chunks")
            
            # Create vector store
            self.vector_store = FAISS.from_documents(
                self.documents,
                self.embeddings
            )
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            logger.info(f"✓ Vector store created with {len(self.documents)} chunks")
            
        except Exception as e:
            logger.error(f"Document loading error: {str(e)}")
    
    def _classify_query(self, question: str) -> str:
        """
        Classify query into: 'document', 'personal', or 'both'.
        
        Returns:
            Query type: 'document' | 'personal' | 'both'
        """
        question_lower = question.lower()
        
        # Document keywords
        doc_keywords = [
            "guideline", "recommendation", "should i", "how to", "when to",
            "what is", "explain", "tell me", "research", "evidence",
            "study", "treatment", "therapy", "medication", "causes",
            "symptoms", "management", "prevention", "best practice"
        ]
        
        # Personal keywords
        personal_keywords = [
            "my", "me", "mine", "i have", "i am", "diagnosed", "suffering",
            "risk", "concerned about", "advice for me", "what should i do",
            "my condition", "my health", "my results"
        ]
        
        has_doc_keyword = any(kw in question_lower for kw in doc_keywords)
        has_personal_keyword = any(kw in question_lower for kw in personal_keywords)
        
        if has_doc_keyword and has_personal_keyword:
            return "both"
        elif has_personal_keyword:
            return "personal"
        else:
            return "document"
    
    def _retrieve_documents(self, question: str) -> str:
        """Retrieve relevant documents for the question."""
        if not self.retriever:
            return ""
        
        try:
            docs = self.retriever.get_relevant_documents(question)
            if not docs:
                return ""
            
            # Combine document chunks
            context = "\n---\n".join([
                f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}"
                for doc in docs
            ])
            return context
        except Exception as e:
            logger.error(f"Document retrieval error: {str(e)}")
            return ""
    
    def _get_sdoh_context(self, context_data: Optional[Dict]) -> str:
        """Generate SDOH-based reasoning and recommendations."""
        if not context_data:
            return ""
        
        sdoh_factors = []
        recommendations = []
        
        # Analyze SDOH scores
        economic = context_data.get("economic_stability_score", 0.5)
        healthcare = context_data.get("healthcare_access_quality_score", 0.5)
        education = context_data.get("education_access_quality_score", 0.5)
        neighborhood = context_data.get("neighborhood_built_environment_score", 0.5)
        food = context_data.get("food_security_score", 0.5)
        social = context_data.get("social_community_context_score", 0.5)
        
        # Build factor and recommendation lists
        if economic < 0.4:
            sdoh_factors.append("Limited economic resources")
            recommendations.append("Explore low-cost healthcare options and community health programs")
        
        if healthcare < 0.4:
            sdoh_factors.append("Limited healthcare access")
            recommendations.append("Identify nearest health centers and telemedicine options")
        
        if education < 0.4:
            sdoh_factors.append("Health literacy challenges")
            recommendations.append("Use simple, clear health education materials")
        
        if neighborhood < 0.4:
            sdoh_factors.append("Limited neighborhood resources")
            recommendations.append("Adapt recommendations to available resources (home exercise, stairs)")
        
        if food < 0.4:
            sdoh_factors.append("Food insecurity")
            recommendations.append("Focus on affordable, nutrient-dense foods; explore food assistance programs")
        
        if social < 0.4:
            sdoh_factors.append("Limited social support")
            recommendations.append("Encourage online health communities and peer support groups")
        
        # Build context string
        sdoh_context = ""
        if sdoh_factors:
            sdoh_context = "\n\n📊 SDOH CONSIDERATIONS:\n"
            sdoh_context += "Health equity factors: " + ", ".join(sdoh_factors) + "\n"
            sdoh_context += "Adapted recommendations:\n"
            sdoh_context += "\n".join([f"  • {r}" for r in recommendations])
        
        return sdoh_context
    
    def query(
        self,
        question: str,
        context_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query RAG system with intelligent routing.
        
        Args:
            question: Health question
            context_data: Optional personal health context
        
        Returns:
            Response dict with: response, source_type, confidence, sdoh_factors
        """
        try:
            if not self.llm:
                demo_response = self.generate_response(question, context_data and str(context_data))
                return {
                    "response": demo_response,
                    "source_type": "demo_fallback",
                    "confidence": 0.55,
                    "has_sdoh_context": bool(context_data),
                    "timestamp": datetime.utcnow().isoformat()
                }
            # Step 1: Classify query
            query_type = self._classify_query(question)
            logger.info(f"Query type: {query_type} | {question[:60]}...")
            
            # Step 2: Build context based on query type
            doc_context = ""
            source_type = "llm_knowledge"
            
            if query_type in ["document", "both"] and self.vector_store:
                doc_context = self._retrieve_documents(question)
                if doc_context:
                    source_type = "rag_documents"
            
            # Step 3: Build personal context
            personal_context = ""
            if query_type in ["personal", "both"] and context_data:
                conditions = []
                for cond in ["diabetes", "hypertension", "heart_disease", "asthma"]:
                    if context_data.get(cond) is True or context_data.get(cond) == "Yes" or context_data.get(f"{cond}_diagnosed") is True:
                        conditions.append(cond.replace('_', ' ').title())
                
                cond_str = ", ".join(conditions) if conditions else "None reported"
                
                personal_context = f"""
Patient Information:
- Age: {context_data.get('age', 'N/A')} years
- Gender: {context_data.get('gender', 'N/A')}
- BMI: {context_data.get('bmi', 'N/A')}
- Glucose: {context_data.get('glucose') or context_data.get('glucose_mg_dl', 'N/A')} mg/dL
- Cholesterol: {context_data.get('cholesterol') or context_data.get('total_cholesterol_mg_dl', 'N/A')} mg/dL
- Smoking: {context_data.get('smoking_history') or context_data.get('smoking', 'N/A')}
- Medical Conditions: {cond_str}
"""
                if source_type == "rag_documents":
                    source_type = "combined"
                else:
                    source_type = "personal_health_data"
            
            # Step 4: Build prompt
            prompt_parts = []
            
            if doc_context:
                prompt_parts.append(f"Health Information:\n{doc_context}")
            
            if personal_context:
                prompt_parts.append(personal_context)
            
            prompt_parts.append(f"Question: {question}\n\nProvide helpful, evidence-based health guidance.")
            
            full_prompt = "\n".join(prompt_parts)
            
            # Step 5: Get LLM response
            response = self.llm.invoke(full_prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Step 6: Add SDOH context
            sdoh_context = self._get_sdoh_context(context_data)
            final_answer = answer + sdoh_context if sdoh_context else answer
            
            return {
                "response": final_answer,
                "source_type": source_type,
                "confidence": 0.85 if doc_context else 0.7,
                "has_sdoh_context": bool(sdoh_context),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            return {
                "response": f"Error processing query: {str(e)}",
                "source_type": "error",
                "confidence": 0.0
            }
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to vector store."""
        try:
            if not documents:
                return False
            
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            split_docs = text_splitter.split_documents(documents)
            
            # Add to vector store
            if self.vector_store:
                self.vector_store.add_documents(split_docs)
            else:
                self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
            
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            self.documents.extend(split_docs)
            
            logger.info(f"Added {len(split_docs)} document chunks")
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics."""
        return {
            "total_chunks": len(self.documents),
            "has_vector_store": self.vector_store is not None,
            "has_retriever": self.retriever is not None,
            "documents_dir": str(DOCUMENTS_DIR),
            "model": self.model_name,
            "status": "ready" if self.llm and self.vector_store else "partial",
            "timestamp": datetime.utcnow().isoformat()
        }
