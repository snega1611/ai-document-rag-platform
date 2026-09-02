import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5433")
DB_NAME = os.getenv("POSTGRES_DB", "ragdb")
DB_USER = os.getenv("POSTGRES_USER", "raguser")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ragpassword")


def get_connection():

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def test_database():

    try:

        connection = get_connection()

        print("PostgreSQL connected successfully")

        connection.close()

        return True

    except Exception as e:

        print("PostgreSQL connection failed:")
        print(e)

        return False
    
def create_documents_table():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (

            document_id UUID PRIMARY KEY,

            session_id VARCHAR(255) NOT NULL,

            filename VARCHAR(255) NOT NULL,

            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            status VARCHAR(50) NOT NULL

        );
    """)

    connection.commit()

    cursor.close()
    connection.close()

    print("Documents table created successfully")
    
    
def save_document(
    document_id,
    session_id,
    filename,
    status
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO documents (
            document_id,
            session_id,
            filename,
            status
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            document_id,
            session_id,
            filename,
            status
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    print(
        f"Document saved to PostgreSQL: "
        f"{document_id}"
    )
    
def create_questions_table():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (

            question_id SERIAL PRIMARY KEY,

            session_id VARCHAR(255) NOT NULL,

            document_id UUID,

            question TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        );
    """)

    connection.commit()

    cursor.close()
    connection.close()

    print("Questions table created successfully")
    
def save_question(
    session_id,
    document_id,
    question
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO questions (
            session_id,
            document_id,
            question
        )
        VALUES (%s, %s, %s)
        """,
        (
            session_id,
            document_id,
            question
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    print(
        "Question saved to PostgreSQL"
    )
    
def create_evaluations_table():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (

            evaluation_id SERIAL PRIMARY KEY,

            question TEXT NOT NULL,

            answer TEXT NOT NULL,

            faithfulness FLOAT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        );
    """)

    connection.commit()

    cursor.close()
    connection.close()

    print("Evaluations table created successfully")
    
def save_evaluation(
    question,
    answer,
    faithfulness_score
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO evaluations (
            question,
            answer,
            faithfulness
        )
        VALUES (%s, %s, %s)
        """,
        (
            question,
            answer,
            faithfulness_score
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    print("Evaluation saved to PostgreSQL")