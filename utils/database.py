# utils/database.py
import json
import os
import uuid
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any
from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error
import urllib.parse
from dotenv import load_dotenv


class Database:
    def __init__(self):
        """Initialize MySQL database connection"""
        load_dotenv()
        try:
            mysql_url = st.secrets["MYSQL_URL"]
        except (KeyError, FileNotFoundError):
            mysql_url = os.getenv("MYSQL_URL")
        url = urllib.parse.urlparse(mysql_url)

        self.host = url.hostname
        self.port = url.port
        self.user = url.username
        self.password = url.password
        mysql_db = url.path.lstrip('/') 
        self.database = mysql_db
        
        # Initialize database on creation
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for MySQL database connections"""
        conn = None
        try:
            conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                ssl_disabled=False
            )
            yield conn
            conn.commit()
        except Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn and conn.is_connected():
                conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table with password - MYSQL SYNTAX
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS p1_mb_users (
                    id VARCHAR(36) PRIMARY KEY,
                    username VARCHAR(255) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sessions table - MYSQL SYNTAX
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS p1_mb_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed INT DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES p1_mb_users(id) ON DELETE CASCADE
                )
            """)
            
            # Character responses table - MYSQL SYNTAX
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS p1_mb_character_responses (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    session_id VARCHAR(36) NOT NULL,
                    character_id INT NOT NULL,
                    character_name VARCHAR(255) NOT NULL,
                    read_passage INT DEFAULT 0,
                    responses TEXT NOT NULL,
                    analysis TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES p1_mb_sessions(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better query performance
            # MySQL doesn't support IF NOT EXISTS for indexes, so wrap in try-except
            try:
                cursor.execute("""
                    CREATE INDEX idx_p1_mb_sessions_user_id 
                    ON p1_mb_sessions(user_id)
                """)
            except Error:
                pass  # Index already exists
            
            try:
                cursor.execute("""
                    CREATE INDEX idx_p1_mb_character_responses_session_id 
                    ON p1_mb_character_responses(session_id)
                """)
            except Error:
                pass
            
            try:
                cursor.execute("""
                    CREATE INDEX idx_p1_mb_users_username 
                    ON p1_mb_users(username)
                """)
            except Error:
                pass
            
            conn.commit()
            print("Database Initialized")
    
    def create_user_with_password(self, user_id: str, username: str, password: str):
        """Create a new user with password"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO p1_mb_users (id, username, password) VALUES (%s, %s, %s)",
                    (user_id, username, password)
                )
                return {"id": user_id, "username": username}
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def verify_user_login(self, username: str, password: str) -> Dict:
        """Verify user login credentials"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT id, username, created_at FROM p1_mb_users WHERE username = %s AND password = %s",
                    (username, password)
                )
                row = cursor.fetchone()
                
                if row:
                    return row
                return None
        except Exception as e:
            print(f"Error verifying login: {e}")
            return None
    
    def check_username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM p1_mb_users WHERE username = %s", (username,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking username: {e}")
            return False
    
    def create_user(self, user_id: str, username: str):
        """Create a new user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO p1_mb_users (id, username, password) VALUES (%s, %s, '')",
                    (user_id, username)
                )
                return {"id": user_id, "username": username}
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def create_session(self, session_id: str, user_id: str):
        """Create a new session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO p1_mb_sessions (id, user_id, completed) VALUES (%s, %s, 0)",
                    (session_id, user_id)
                )
                return {"id": session_id, "user_id": user_id}
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
        
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its associated data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Foreign key constraints will handle cascading deletes
                cursor.execute("DELETE FROM p1_mb_sessions WHERE id = %s", (session_id,))
                return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

    
    def save_character_response(self, session_id: str, character_id: int, 
                                character_name: str, read_passage: bool,
                                responses: List[Any], analysis: Dict):
        """Save character assessment response"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                # Insert character response (convert bool to int, JSON to string)
                cursor.execute("""
                    INSERT INTO p1_mb_character_responses 
                    (session_id, character_id, character_name, read_passage, responses, analysis)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    session_id, 
                    character_id, 
                    character_name, 
                    int(read_passage),
                    json.dumps(responses),
                    json.dumps(analysis)
                ))
                
                # Update session completed count
                cursor.execute(
                    "SELECT completed FROM p1_mb_sessions WHERE id = %s",
                    (session_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    current_completed = row["completed"]
                    cursor.execute(
                        "UPDATE p1_mb_sessions SET completed = %s WHERE id = %s",
                        (current_completed + 1, session_id)
                    )
                
                return {"session_id": session_id, "character_id": character_id}
        except Exception as e:
            print(f"Error saving character response: {e}")
            return None
    
    def get_session_responses(self, session_id: str) -> List[Dict]:
        """Get all responses for a session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT character_id, character_name, read_passage, responses, analysis, created_at
                    FROM p1_mb_character_responses
                    WHERE session_id = %s
                    ORDER BY created_at
                """, (session_id,))
                
                rows = cursor.fetchall()
                return [
                    {
                        "character_id": row["character_id"],
                        "character_name": row["character_name"],
                        "read_passage": bool(row["read_passage"]),
                        "responses": json.loads(row["responses"]),
                        "analysis": json.loads(row["analysis"]),
                        "created_at": row["created_at"]
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting session responses: {e}")
            return []
    
    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """Get all sessions for a user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT id, created_at, completed
                    FROM p1_mb_sessions
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                
                rows = cursor.fetchall()
                return [
                    {
                        "id": row["id"],
                        "created_at": row["created_at"],
                        "completed": row["completed"]
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting user sessions: {e}")
            return []
    
    def get_session_info(self, session_id: str) -> Dict:
        """Get session information with user details"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT s.id, s.user_id, s.created_at, s.completed, u.username
                    FROM p1_mb_sessions s
                    JOIN p1_mb_users u ON s.user_id = u.id
                    WHERE s.id = %s
                """, (session_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return {
                        'session_id': row["id"],
                        'user_id': row["user_id"],
                        'created_at': row["created_at"],
                        'completed': row["completed"],
                        'username': row["username"]
                    }
                return None
        except Exception as e:
            print(f"Error getting session info: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Dict:
        """Get user by username"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT id, username, created_at FROM p1_mb_users WHERE username = %s",
                    (username,)
                )
                row = cursor.fetchone()
                
                if row:
                    return row
                return None
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
    
    def get_user_sessions_by_username(self, username: str) -> List[Dict]:
        """Get all sessions for a user by username"""
        try:
            # First get user by username
            user = self.get_user_by_username(username)
            if not user:
                return []
            
            # Then get all sessions for that user
            return self.get_user_sessions(user['id'])
        except Exception as e:
            print(f"Error getting user sessions by username: {e}")
            return []
    
    def create_or_get_user(self, username: str) -> str:
        """Create user if not exists, or get existing user ID"""
        try:
            # Check if user exists
            existing_user = self.get_user_by_username(username)
            
            if existing_user:
                return existing_user['id']
            
            # Create new user
            user_id = str(uuid.uuid4())
            self.create_user(user_id, username)
            return user_id
            
        except Exception as e:
            print(f"Error in create_or_get_user: {e}")
            return str(uuid.uuid4())