""" 
Manages interactions with Gemini LLM and other language models.
Provides functionalities for generating text, analyzing data, and planning.
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Union
import google.generativeai as genai
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMManager:
    """Manages interactions with language models."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the LLM manager.
        
        Args:
            api_key (str, optional): API key for the Gemini API
            model_name (str): Name of the Gemini model to use
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("No Gemini API key provided. Some functionality may be limited.")
        
        self.model_name = model_name
        self._setup_gemini()
        self._setup_langchain()
        
    def _setup_gemini(self):
        """Set up the Gemini client."""
        try:
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.gemini_model = genai.GenerativeModel(self.model_name)
                logger.debug(f"Gemini model {self.model_name} initialized")
            else:
                self.gemini_model = None
                logger.warning("Gemini model not initialized due to missing API key")
        except Exception as e:
            logger.error(f"Error setting up Gemini: {str(e)}")
            self.gemini_model = None
            
    def _setup_langchain(self):
        """Set up LangChain components."""
        try:
            if self.api_key:
                self.langchain_llm = GoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                    temperature=0.7
                )
                logger.debug("LangChain integration initialized")
            else:
                self.langchain_llm = None
                logger.warning("LangChain integration not initialized due to missing API key")
        except Exception as e:
            logger.error(f"Error setting up LangChain: {str(e)}")
            self.langchain_llm = None
    
    async def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate text using the Gemini model.
        
        Args:
            prompt (str): Text prompt for generation
            temperature (float): Temperature for text generation
            
        Returns:
            str: Generated text
        """
        try:
            if not self.gemini_model:
                return "LLM functionality not available (API key not configured)"
                
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={"temperature": temperature}
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return f"Error generating text: {str(e)}"
    
    async def analyze_page_content(self, url: str, content: str) -> Dict[str, Any]:
        """
        Analyze page content to extract key information.
        
        Args:
            url (str): URL of the page
            content (str): Page content to analyze
            
        Returns:
            dict: Analysis results including key entities, summary, etc.
        """
        try:
            if not self.gemini_model:
                return {
                    "status": "error",
                    "message": "LLM functionality not available (API key not configured)"
                }
                
            # Truncate content if too long
            truncated_content = content[:8000] if len(content) > 8000 else content
                
            prompt = f"""
            Analyze the following content from {url}:
            
            {truncated_content}
            
            Extract and provide the following information in a structured format:
            1. Main topic or purpose of the page
            2. Key entities (people, companies, products, locations)
            3. Important facts or data points
            4. A brief summary (2-3 sentences)
            
            Format your response as a JSON object with the following keys:
            - main_topic
            - key_entities (as a list of objects with 'type' and 'name' properties)
            - important_facts (as a list)
            - summary
            """
                
            response = self.gemini_model.generate_content(prompt)
            
            try:
                # Try to parse as JSON
                text_response = response.text
                # Find JSON object if embedded in text
                if '{' in text_response and '}' in text_response:
                    start = text_response.find('{')
                    end = text_response.rfind('}') + 1
                    json_str = text_response[start:end]
                    analysis = json.loads(json_str)
                else:
                    # Create structured result if not JSON
                    analysis = {
                        "main_topic": "Unknown",
                        "key_entities": [],
                        "important_facts": [],
                        "summary": text_response[:300]  # Use first 300 chars as summary
                    }
            except json.JSONDecodeError:
                # Handle non-JSON response
                analysis = {
                    "main_topic": "Unknown",
                    "key_entities": [],
                    "important_facts": [],
                    "summary": response.text[:300]  # Use first 300 chars as summary
                }
                
            return {
                "status": "success",
                "analysis": analysis
            }
                
        except Exception as e:
            logger.error(f"Error analyzing page content: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def generate_summary(self, task: str, context: Dict[str, Any]) -> str:
        """
        Generate a summary of task execution.
        
        Args:
            task (str): Task description
            context (dict): Context data from task execution
            
        Returns:
            str: Generated summary
        """
        try:
            if not self.gemini_model:
                return "Summary not available (LLM API key not configured)"
                
            # Extract relevant data from context
            visited_urls = context.get("visited_urls", [])
            actions_performed = context.get("actions_performed", [])
            
            # Create a prompt for summary generation
            prompt = f"""
            Generate a concise summary of the following task:
            
            Task: {task}
            
            URLs visited: {', '.join(visited_urls[:5])}
            Number of actions performed: {len(actions_performed)}
            
            Please provide a brief summary of what was accomplished, focusing on the most important information 
            discovered or actions taken. Keep the summary under 3 sentences.
            """
                
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
                
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Task completed. Visited {len(visited_urls)} URLs."
    
    async def plan_search_strategy(self, query: str) -> Dict[str, Any]:
        """
        Plan a search strategy for a given query.
        
        Args:
            query (str): Search query
            
        Returns:
            dict: Search plan with recommended search engines, keywords, etc.
        """
        try:
            if not self.langchain_llm:
                return {
                    "search_engine": "google",
                    "url": f"https://www.google.com/search?q={query}"
                }
                
            template = """
            For the search query: "{query}"
            
            Determine the optimal search strategy:
            1. Which search engine would be most appropriate?
            2. Should the query be reformulated for better results?
            3. Are there specific filters or advanced search operators that should be used?
            
            Respond with a JSON object containing:
            {{
                "search_engine": "google" or "bing" or "duckduckgo",
                "reformulated_query": "the improved search query",
                "url": "the full search URL including the query string",
                "rationale": "brief explanation of your choices"
            }}
            """
            
            prompt = PromptTemplate(
                template=template,
                input_variables=["query"]
            )
            
            chain = LLMChain(llm=self.langchain_llm, prompt=prompt)
            result = await chain.arun(query=query)
            
            try:
                # Extract JSON from response
                if '{' in result and '}' in result:
                    start = result.find('{')
                    end = result.rfind('}') + 1
                    json_str = result[start:end]
                    plan = json.loads(json_str)
                else:
                    # Fallback plan
                    plan = {
                        "search_engine": "google",
                        "reformulated_query": query,
                        "url": f"https://www.google.com/search?q={query}",
                        "rationale": "Default search strategy"
                    }
            except json.JSONDecodeError:
                # Fallback plan
                plan = {
                    "search_engine": "google",
                    "reformulated_query": query,
                    "url": f"https://www.google.com/search?q={query}",
                    "rationale": "Default search strategy"
                }
                
            return plan
                
        except Exception as e:
            logger.error(f"Error planning search strategy: {str(e)}")
            return {
                "search_engine": "google",
                "url": f"https://www.google.com/search?q={query}"
            }
    
    async def analyze_search_results(self, query: str, results: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyze search results to extract key information.
        
        Args:
            query (str): Original search query
            results (list): Search results to analyze
            
        Returns:
            dict: Analysis including top results, recommended next steps, etc.
        """
        try:
            if not self.gemini_model or len(results) == 0:
                return {
                    "recommended_links": [],
                    "summary": "No analysis available"
                }
                
            # Prepare results for LLM analysis
            result_text = "\n".join([
                f"Result {i+1}: {r.get('text', '')}[:100] - Link: {r.get('link', '')}"
                for i, r in enumerate(results[:5])  # Limit to top 5 results
            ])
                
            prompt = f"""
            Analyze the following search results for the query: "{query}"
            
            {result_text}
            
            Please:
            1. Identify the most relevant results (up to 3)
            2. Summarize what we learned from these results
            3. Recommend next steps (e.g., refine search, visit specific pages)
            
            Format your response as a JSON object with the following keys:
            - top_results (indices of the most relevant results, starting from 1)
            - summary (a brief summary of what we learned)
            - next_steps (recommended actions)
            """
                
            response = self.gemini_model.generate_content(prompt)
            
            try:
                # Try to parse as JSON
                text_response = response.text
                if '{' in text_response and '}' in text_response:
                    start = text_response.find('{')
                    end = text_response.rfind('}') + 1
                    json_str = text_response[start:end]
                    analysis = json.loads(json_str)
                else:
                    # Create structured result
                    analysis = {
                        "top_results": [1],  # Default to first result
                        "summary": text_response[:300],
                        "next_steps": ["Visit the first search result"]
                    }
            except json.JSONDecodeError:
                # Handle non-JSON response
                analysis = {
                    "top_results": [1],  # Default to first result
                    "summary": response.text[:300],
                    "next_steps": ["Visit the first search result"]
                }
                
            # Convert top_results indices to recommended links
            recommended_links = []
            for idx in analysis.get("top_results", []):
                if isinstance(idx, int) and 1 <= idx <= len(results):
                    recommended_links.append(results[idx-1].get("link", ""))
                
            return {
                "recommended_links": recommended_links,
                "summary": analysis.get("summary", "No summary available"),
                "next_steps": analysis.get("next_steps", [])
            }
                
        except Exception as e:
            logger.error(f"Error analyzing search results: {str(e)}")
            return {
                "recommended_links": [],
                "summary": f"Error analyzing results: {str(e)}"
            }
            
    async def perform_analysis_task(self, task: str, collected_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform an in-depth analysis task based on collected data from multiple sources.
        
        Args:
            task (str): Description of the analysis task
            collected_data (list): List of dictionaries containing data collected from various sources
            
        Returns:
            dict: Analysis results including findings, insights, and summary
        """
        try:
            if not self.gemini_model:
                return {
                    "status": "error",
                    "message": "LLM functionality not available (API key not configured)"
                }
                
            # Prepare the collected data for analysis
            data_summary = []
            for i, item in enumerate(collected_data):
                source = item.get('url', f'Source {i+1}')
                content = item.get('data', '')[:4000]  # Truncate long content
                data_summary.append(f"Source: {source}\nContent: {content}\n")
            
            data_text = "\n".join(data_summary)
            
            prompt = f"""
            Task: {task}
            
            Analyze the following data collected from multiple sources:
            
            {data_text}
            
            Perform a thorough sentiment analysis addressing the task requirements. For each source:
            1. Identify positive, negative, and neutral sentiments related to AI safety
            2. Extract key concerns and risks mentioned
            3. Identify positive developments or solutions discussed
            4. Determine the overall stance toward AI safety (concerned, optimistic, balanced, etc.)
            
            Then provide a comprehensive analysis across all sources:
            1. Common themes and patterns in sentiment
            2. Major concerns that appear across multiple sources
            3. Positive developments or solutions emphasized
            4. Overall public sentiment toward AI safety based on these sources
            5. Significant differences in sentiment between sources
            
            Format your response as a JSON object with the following structure:
            {{
                "source_analyses": [
                    {{
                        "source": "source URL",
                        "sentiment_summary": "overall sentiment description",
                        "key_concerns": ["concern 1", "concern 2", ...],
                        "positive_aspects": ["positive 1", "positive 2", ...],
                        "stance": "overall stance description"
                    }},
                    ...
                ],
                "cross_source_analysis": {{
                    "common_themes": ["theme 1", "theme 2", ...],
                    "major_concerns": ["concern 1", "concern 2", ...],
                    "positive_developments": ["development 1", "development 2", ...],
                    "overall_public_sentiment": "description of overall sentiment",
                    "sentiment_differences": ["difference 1", "difference 2", ...]
                }},
                "executive_summary": "concise summary of findings"
            }}
            """
                
            response = self.gemini_model.generate_content(prompt)
            
            try:
                # Try to parse as JSON
                text_response = response.text
                if '{' in text_response and '}' in text_response:
                    start = text_response.find('{')
                    end = text_response.rfind('}') + 1
                    json_str = text_response[start:end]
                    analysis = json.loads(json_str)
                else:
                    # Create structured result if not JSON
                    analysis = {
                        "source_analyses": [],
                        "cross_source_analysis": {
                            "common_themes": [],
                            "major_concerns": [],
                            "positive_developments": [],
                            "overall_public_sentiment": "Unable to determine",
                            "sentiment_differences": []
                        },
                        "executive_summary": text_response[:500]  # Use response as summary
                    }
            except json.JSONDecodeError:
                # Handle non-JSON response
                analysis = {
                    "source_analyses": [],
                    "cross_source_analysis": {
                        "common_themes": [],
                        "major_concerns": [],
                        "positive_developments": [],
                        "overall_public_sentiment": "Unable to determine",
                        "sentiment_differences": []
                    },
                    "executive_summary": response.text[:500]  # Use response as summary
                }
                
            result =  {
                "status": "success",
                "analysis": analysis
            }
            # Save results to file 
            from rabbit_sdk.utils import save_analysis_results
            task_id = hashlib.md5(task.encode()).hexdigest()[:8]
            save_analysis_results(result, task_id)

            return result
                
        except Exception as e:
            logger.error(f"Error performing analysis task: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }