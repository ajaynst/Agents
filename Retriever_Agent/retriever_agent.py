import os
from dotenv import load_dotenv 

load_dotenv()

GROQ_API=os.environ.get("GROQ_API_KEY")
DB_UNAME=os.environ.get("DB_UNAME")
DB_PASS=os.environ.get("DB_PASS")

from langchain_text_splitters import CharacterTextSplitter
from glob import glob

text_splitter = CharacterTextSplitter(
    separator="###",
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)

texts = []
for file_path in glob("docs/*.txt"): # loading all text files in docs folder
    with open(file_path, "r") as f:
        doc = f.read()
    
    file_chunks = text_splitter.create_documents(
        [doc], 
        metadatas=[{"source": file_path}]
    )
    texts.extend(file_chunks)

from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

schema_store = Chroma.from_documents(
    texts,
    embedding=embeddings,
    collection_name="schema_rag"
)

schema_retriever = schema_store.as_retriever(k=4)

schema_retriever.invoke("currency")

from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from typing import List, Tuple

username = DB_UNAME
password = DB_PASS
db_ip = "localhost"
db_port = "5432"
database = "postgres"
engine = create_engine(f"postgresql+psycopg2://{username}:{password}@{db_ip}:{db_port}/{database}")


def validate_sql(query: str):
    q = query.lower().strip()

    if not q.startswith("select"):
        raise ValueError("Only SELECT queries are allowed")

    forbidden = ["insert", "update", "delete", "drop", "alter", ";"]
    # pass_kw = ['deleted_at'] # all queries will have deleted_at 
    
    for kw in forbidden:
        if kw in q:
            raise ValueError(f"Forbidden SQL keyword detected: {kw}")

@tool
def query_vecdb(question: str) -> str:
    """
    Retrieve relevant database schema based on the user question.
    Always call this before generating SQL.
    """
    docs = schema_retriever.invoke(question)
    return "\n\n".join(d.page_content for d in docs)


@tool
def run_sql_query(query: str) -> str:
    """Execute a validated read-only SQL query."""
    
    print("\n--- SQL GENERATED ---")
    print(query)

    # validate_sql(query) # need to solve deleted_at getting caught in forbidden words list

    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchmany(5)
        return str(rows)


@tool
def get_table_schema(table_name: str) -> List[Tuple]:
    """Return column schema information for a table.
    Argument: table_name, example - customers
    """
    query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = :table_name
        ORDER BY ordinal_position
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"table_name": table_name})
        return result.fetchall()

# need more time and work to implement this
# @tool
# def request_clarification(reason: str) -> str:
#     """Ask the user for clarification before generating SQL."""
#     return f"Clarification needed: {reason}"


@tool
def list_table():
    """Return names of table present in the database."""
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public';
    """
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return str(result.fetchall())


# @tool
# def verify_column(table: str, column: str) -> bool:
#     """Verify a column exists in a given table."""
#     # this query is not running 
#     query = """ 
#         SELECT 1
#         FROM information_schema.columns
#         WHERE table_name = :table AND column_name = :column
#     """
#     with engine.connect() as conn:
#         result = conn.execute(text(query), {"table": table, "column": column})
#         return result.first() is not None

from langchain_groq import ChatGroq

# "moonshotai/kimi-k2-instruct-0905"
llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0
)

SYSTEM_PROMPT = """
You are a PostgreSQL database assistant.

You MUST follow this exact sequence:
1. Call schema checking tool
2. Read schema carefully
3. Decide required tables and columns
4. Generate a SELECT-only SQL query
5. Execute it using run_sql_query
6. Answer in plain English

Before writing SQL:
- List tables you will use
- List columns you will use
- Verify each exists in schema

Rules:
- Never generate SQL before schema is retrieved
- Never guess table or column names
- Never modify data
- If schema is insufficient, ask for clarification

After writing the SQL:
- Run it with sql query runner tool
- Only return the result if the query tool gives an output
- If there's an error rework on it
"""

from langchain.agents import create_agent

agent = create_agent(
    llm,
    tools=[
        query_vecdb,
        get_table_schema,
        list_table,
        run_sql_query,
        # request_clarification,
        # verify_column
    ],
    system_prompt=SYSTEM_PROMPT,
)

def streamer_agent(question):
    for step in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        yield step["messages"][-1].pretty_print()