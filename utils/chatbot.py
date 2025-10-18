import json
import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

class CharacterChatbot:
    def __init__(self):
        
        try:
            api_key = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))
        except:
            # If secrets.toml doesn't exist or secrets not accessible, use environment variable
            api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found! Please set it in either:\n"
                "1. .streamlit/secrets.toml file: GOOGLE_API_KEY = 'your-key'\n"
                "2. Environment variable: export GOOGLE_API_KEY='your-key'\n"
                "3. .env file: GOOGLE_API_KEY=your-key"
            )
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            temperature=0.3,
            max_retries=2,
            google_api_key=api_key
        )
        
        # Load character data
        with open("assets/character_passage.json", "r", encoding="utf-8") as f:
            self.characters_data = json.load(f)
    
    def analyze_responses(self, character_name: str, passage: str, 
                         questions: list, user_responses: list) -> dict:
        """Analyze user responses using LLM"""
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert HR psychologist analyzing personality traits based on the {character_name} archetype from Mahabharata.

Character Passage:
{passage}

Questions and User Responses:
{qa_pairs}

Analyze the user's responses deeply and provide:
1. Overall rating (1-10) for alignment with {character_name}'s positive traits
2. Specific ratings for each key quality (provide at least 5 quality ratings)
3. Detailed analysis (200-300 words) of their strengths, areas for improvement, and actionable recommendations
4. Key insights about their professional personality

Return ONLY a valid JSON object with this exact structure:
{{
    "overall_rating": <float between 1-10>,
    "quality_ratings": {{
        "quality_name_1": <float between 1-10>,
        "quality_name_2": <float between 1-10>,
        "quality_name_3": <float between 1-10>,
        "quality_name_4": <float between 1-10>,
        "quality_name_5": <float between 1-10>
    }},
    "analysis": "<detailed analysis text>",
    "strengths": ["strength1", "strength2", "strength3"],
    "areas_for_improvement": ["area1", "area2", "area3"],
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
    "key_insights": ["insight1", "insight2", "insight3"]
}}

Ensure all fields are present and properly formatted."""),
            ("human", "Analyze these responses and provide the JSON output.")
        ])
        
        # Format Q&A pairs
        qa_pairs = ""
        for i, response in enumerate(user_responses):
            question = questions[i]
            qa_pairs += f"\nQ{i+1}: {question['question']}\n"
            if question.get('rate_question'):
                qa_pairs += f"User Ratings: {json.dumps(response, indent=2)}\n"
            else:
                qa_pairs += f"User Answer: {response}\n"
        
        # Generate analysis
        chain = prompt_template | self.llm
        result = chain.invoke({
            "character_name": character_name,
            "passage": passage,
            "qa_pairs": qa_pairs
        })
        
        # Parse JSON response
        try:
            # Clean up the response
            content = result.content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            analysis_data = json.loads(content)
            
            # Validate required fields
            required_fields = ['overall_rating', 'quality_ratings', 'analysis', 
                             'strengths', 'areas_for_improvement', 'recommendations', 'key_insights']
            for field in required_fields:
                if field not in analysis_data:
                    raise ValueError(f"Missing required field: {field}")
            
            return analysis_data
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback if JSON parsing fails
            print(f"Error parsing LLM response: {e}")
            return {
                "overall_rating": 7.0,
                "quality_ratings": {
                    "Leadership": 7.0,
                    "Communication": 7.0,
                    "Ethics": 7.0,
                    "Adaptability": 7.0,
                    "Teamwork": 7.0
                },
                "analysis": result.content,
                "strengths": ["Thoughtful responses", "Self-awareness", "Growth mindset"],
                "areas_for_improvement": ["Continue developing skills", "Seek mentorship", "Practice consistency"],
                "recommendations": ["Regular self-reflection", "Seek feedback", "Set clear goals"],
                "key_insights": ["Shows potential for growth", "Values professional development"]
            }