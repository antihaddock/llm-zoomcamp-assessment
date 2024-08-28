"""
db.py

This module provides functions for interacting with the PostgreSQL database used in the application.
It includes functionality to initialize the database, save conversations and feedback, and retrieve
data for analysis.

Functions:
    - get_db_connection: Establishes a connection to the PostgreSQL database.
    - init_db: Initializes the database by creating necessary tables.
    - save_conversation: Saves a conversation entry into the 'conversations' table.
    - save_feedback: Saves feedback related to a conversation into the 'feedback' table.
    - get_recent_conversations: Retrieves recent conversations with optional relevance filtering.
    - get_feedback_stats: Retrieves statistics of feedback, summarizing counts of positive and negative feedback.

Dependencies:
    - psycopg2: Used for database connectivity.
    - zoneinfo: Handles time zone management.

Ensure the environment variables for database connection are set correctly before running this module.
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.extensions import connection
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List

tz = ZoneInfo("Australia/Sydney")


def get_db_connection() -> connection:
    """
    Establishes a connection to the PostgreSQL database using credentials 
    and configuration from environment variables.

    Returns:
        connection: A connection object to the PostgreSQL database.
    """
    db_connection = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "course_assistant"),
        user=os.getenv("POSTGRES_USER", "your_username"),
        password=os.getenv("POSTGRES_PASSWORD", "your_password"),
    )
    return db_connection


def init_db() -> None:
    """
    Initializes the database by creating the necessary tables.
    Drops existing tables 'feedback' and 'conversations' if they exist.

    The function creates:
        - 'conversations' table: Stores conversation data.
        - 'feedback' table: Stores feedback data linked to conversations.

    Uses a connection obtained from `get_db_connection()`.

    Returns:
        None
    """
    conn: connection = get_db_connection()
    
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS feedback")
            cur.execute("DROP TABLE IF EXISTS conversations")

            cur.execute("""
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    course TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    response_time FLOAT NOT NULL,
                    relevance TEXT NOT NULL,
                    relevance_explanation TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    eval_prompt_tokens INTEGER NOT NULL,
                    eval_completion_tokens INTEGER NOT NULL,
                    eval_total_tokens INTEGER NOT NULL,
                    openai_cost FLOAT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE feedback (
                    id SERIAL PRIMARY KEY,
                    conversation_id TEXT REFERENCES conversations(id),
                    feedback INTEGER NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()


def save_conversation(
    conversation_id: str, 
    question: str, 
    answer_data: Dict[str, Any], 
    course: str, 
    timestamp: Optional[datetime] = None
) -> None:
    """
    Saves a conversation entry into the 'conversations' table.

    If no timestamp is provided, the current timestamp is used.

    Args:
        conversation_id (str): The unique identifier for the conversation.
        question (str): The question posed in the conversation.
        answer_data (Dict[str, Any]): A dictionary containing answer details, including:
            - answer (str): The answer text.
            - model_used (str): The model used to generate the answer.
            - response_time (float): The response time for the answer.
            - relevance (str): The relevance of the answer.
            - relevance_explanation (str): An explanation of the relevance.
            - prompt_tokens (int): The number of tokens in the prompt.
            - completion_tokens (int): The number of tokens in the completion.
            - total_tokens (int): The total number of tokens.
            - eval_prompt_tokens (int): The number of tokens in the evaluation prompt.
            - eval_completion_tokens (int): The number of tokens in the evaluation completion.
            - eval_total_tokens (int): The total number of tokens in the evaluation.
            - openai_cost (float): The cost associated with the OpenAI API call.
        course (str): The course related to the conversation.
        timestamp (Optional[datetime]): The timestamp of the conversation. Defaults to current time.

    Returns:
        None
    """
    if timestamp is None:
        timestamp = datetime.now(tz)

    conn: connection = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations 
                (id, question, answer, course, model_used, response_time, relevance, 
                relevance_explanation, prompt_tokens, completion_tokens, total_tokens, 
                eval_prompt_tokens, eval_completion_tokens, eval_total_tokens, openai_cost, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
                """,
                (
                    conversation_id,
                    question,
                    answer_data["answer"],
                    course,
                    answer_data["model_used"],
                    answer_data["response_time"],
                    answer_data["relevance"],
                    answer_data["relevance_explanation"],
                    answer_data["prompt_tokens"],
                    answer_data["completion_tokens"],
                    answer_data["total_tokens"],
                    answer_data["eval_prompt_tokens"],
                    answer_data["eval_completion_tokens"],
                    answer_data["eval_total_tokens"],
                    answer_data["openai_cost"],
                    timestamp,
                ),
            )
        conn.commit()
    finally:
        conn.close()

def save_feedback(conversation_id: str, feedback: int, timestamp: Optional[datetime] = None) -> None:
    """
    Saves feedback related to a conversation into the 'feedback' table.

    If no timestamp is provided, the current timestamp is used.

    Args:
        conversation_id (str): The unique identifier for the conversation to which the feedback relates.
        feedback (int): The feedback score for the conversation.
        timestamp (Optional[datetime]): The timestamp when the feedback was given. Defaults to current time.

    Returns:
        None
    """
    if timestamp is None:
        timestamp = datetime.now(tz)

    conn: connection = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feedback (conversation_id, feedback, timestamp) 
                VALUES (%s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
                """,
                (conversation_id, feedback, timestamp),
            )
        conn.commit()
    finally:
        conn.close()


def get_feedback_stats() -> Dict[str, int]:
    """
    Retrieves the statistics of feedback given, summarizing the counts of positive and negative feedback.

    Returns:
        Dict[str, int]: A dictionary containing the counts of 'thumbs_up' (positive feedback) 
                        and 'thumbs_down' (negative feedback).
    """
    conn: connection = get_db_connection()

    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN feedback > 0 THEN 1 ELSE 0 END) as thumbs_up,
                    SUM(CASE WHEN feedback < 0 THEN 1 ELSE 0 END) as thumbs_down
                FROM feedback
            """)
            return cur.fetchone()
    finally:
        conn.close()