import os
import logging
import openai
from functools import lru_cache
from typing import Dict, List, Optional, Union
from ..config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPTEvaluator:
    def __init__(self):
        """Initialize GPT Evaluator with API credentials"""
        self.api_key = Config.OPENAI_API_KEY
        self.org_id = Config.OPENAI_ORG_ID
        
        if not self.api_key:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key not configured")
            
        openai.api_key = self.api_key
        if self.org_id:
            openai.organization = self.org_id
            
        self._test_connection()

    def _test_connection(self) -> None:
        """Test connection to OpenAI API"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            logger.info("Successfully connected to OpenAI API")
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI API: {str(e)}")
            raise

    @lru_cache(maxsize=100)
    def evaluate_resume(self, resume_text: str, job_requirements: str) -> Dict:
        """
        Evaluate resume against job requirements
        
        Args:
            resume_text: Extracted text from resume
            job_requirements: Job requirements text
            
        Returns:
            Dictionary containing evaluation results
        """
        try:
            prompt = f"""
            Resume Text:
            {resume_text}
            
            Job Requirements:
            {job_requirements}
            
            Please evaluate this resume against the job requirements and provide:
            1. Match Score (0-100)
            2. Key Strengths (max 3)
            3. Areas for Improvement (max 3)
            4. Overall Assessment (2-3 sentences)
            
            Format the response as JSON with these keys: matchScore, strengths, improvements, assessment
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error evaluating resume: {str(e)}")
            return {
                "error": str(e),
                "matchScore": 0,
                "strengths": [],
                "improvements": [],
                "assessment": "Error occurred during evaluation"
            }

    def chat_with_gpt(self, message: str) -> str:
        """
        Chat with GPT about resumes and job requirements
        
        Args:
            message: User message with optional resume context
            
        Returns:
            GPT response
        """
        try:
            system_prompt = """You are an AI HR assistant helping to analyze resumes and answer questions about candidates.
            When provided with resume information, analyze it carefully and provide insights based on the data.
            If no resume data is available, inform the user and answer general HR-related questions."""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message['content'].strip()
            
        except Exception as e:
            logger.error(f"Error in chat_with_gpt: {str(e)}")
            raise

    def analyze_job_requirements(self, requirements: str) -> Dict:
        """
        Analyze and structure job requirements
        
        Args:
            requirements: Job requirements text
            
        Returns:
            Dictionary with structured requirements
        """
        try:
            prompt = f"""
            Job Requirements:
            {requirements}
            
            Please analyze these job requirements and provide:
            1. Required Skills (technical & soft skills)
            2. Required Experience (years and type)
            3. Education Requirements
            4. Key Responsibilities
            
            Format the response as JSON with these keys: skills, experience, education, responsibilities
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error analyzing requirements: {str(e)}")
            return {
                "error": str(e),
                "skills": [],
                "experience": "Not available",
                "education": "Not available",
                "responsibilities": []
            }
