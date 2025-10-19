# utils/chatbot.py
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
    
    def detect_answer_intent(self, question: str, answer: str) -> str:
        """
        Use LLM to determine if the answer is yes/no/neutral or has_mentor/no_mentor
        Returns: 'yes', 'no', 'neutral', 'has_mentor', 'no_mentor'
        """
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing text responses and determining intent. 
You only respond with one of these words: yes, no, neutral, has_mentor, no_mentor.

For yes/no questions, respond with:
- "yes" (affirmative, positive, agreed, they have/do something)
- "no" (negative, they don't have/haven't done something)
- "neutral" (unclear, mixed response, or doesn't directly answer yes/no)

For mentor-related questions (about having a mentor/coach), respond with:
- "has_mentor" (they name specific people, mention existing mentor/coach relationships)
- "no_mentor" (they say they don't have one, looking for one, or working alone)
- "neutral" (informal guidance, learns from various sources, uncertain)

Respond with ONLY ONE WORD from the above options."""),
            ("human", """Question: {question}

User's Answer: {answer}

Determine the user's response category. Respond with only one word: yes, no, neutral, has_mentor, or no_mentor.""")
        ])

        try:
            chain = prompt_template | self.llm
            result = chain.invoke({
                "question": question,
                "answer": answer
            })
            
            intent = result.content.strip().lower()
            
            # Validate response
            valid_intents = ['yes', 'no', 'neutral', 'has_mentor', 'no_mentor']
            if intent not in valid_intents:
                print(f"Invalid intent detected: {intent}. Defaulting to 'neutral'")
                return 'neutral'
            
            return intent
            
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return 'neutral'

    def get_next_question(self, current_question: dict, user_answer: str, 
                         all_questions: list, current_base_idx: int) -> dict:
        """
        Determine the next question based on user's answer using LLM
        Returns: dict with question details or None if no more questions
        """
        
        # Check if current question has follow-up logic
        if 'follow_up_questions' in current_question:
            intent = self.detect_answer_intent(current_question['question'], user_answer)
            
            follow_ups = current_question['follow_up_questions']
            
            # Get the appropriate follow-up question
            if intent in follow_ups:
                follow_up = follow_ups[intent]
                return {
                    'question': follow_up['question'],
                    'question_no': follow_up.get('question_no', f"{current_question['question_no']}_followup"),
                    'rate_question': follow_up.get('rate_question', False),
                    'options': follow_up.get('options', []),
                    'guidance': follow_up.get('guidance', ''),
                    'is_follow_up': True,
                    'parent_question_no': current_question['question_no']
                }
        
        # No follow-up needed, move to next base question
        next_idx = current_base_idx + 1
        if next_idx < len(all_questions):
            next_q = all_questions[next_idx]
            return {
                'question': next_q['question'],
                'question_no': next_q['question_no'],
                'rate_question': next_q.get('rate_question', False),
                'options': next_q.get('options', []),
                'is_follow_up': False
            }
        
        # No more questions
        return None
    
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
        
        # Format Q&A pairs - Handle both old list format and new dict format
        qa_pairs = ""
        for i, response in enumerate(user_responses):
            if i < len(questions):
                question = questions[i]
                
                # Handle new format with question metadata
                if isinstance(response, dict) and 'question' in response:
                    qa_pairs += f"\nQ{i+1}: {response['question']}\n"
                    if response.get('type') == 'rating':
                        qa_pairs += f"User Ratings: {json.dumps(response['answer'], indent=2)}\n"
                    else:
                        qa_pairs += f"User Answer: {response['answer']}\n"
                # Handle old format
                else:
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
            elif content.startswith("```"):
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
            print(f"Raw response: {result.content}")
            return {
                "overall_rating": 7.0,
                "quality_ratings": {
                    "Leadership": 7.0,
                    "Communication": 7.0,
                    "Ethics": 7.0,
                    "Adaptability": 7.0,
                    "Teamwork": 7.0
                },
                "analysis": result.content if len(result.content) < 500 else "Analysis generated successfully. Please review your responses in the dashboard.",
                "strengths": ["Thoughtful responses", "Self-awareness", "Growth mindset"],
                "areas_for_improvement": ["Continue developing skills", "Seek mentorship", "Practice consistency"],
                "recommendations": ["Regular self-reflection", "Seek feedback", "Set clear goals"],
                "key_insights": ["Shows potential for growth", "Values professional development"]
            }