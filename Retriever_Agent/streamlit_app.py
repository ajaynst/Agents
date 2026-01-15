import os
import streamlit as st
from dotenv import load_dotenv
from langchain_text_splitters import CharacterTextSplitter
from glob import glob
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from langchain_groq import ChatGroq
from langchain.agents import create_agent
import torch
from typing import List, Tuple


from sentence_transformers import SentenceTransformer
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
import torch

# Manually load the SentenceTransformer model and specify the device
device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = "sentence-transformers/all-MiniLM-L6-v2"

# Load the model manually to ensure it is on the right device
model = SentenceTransformer(model_name, device=device)

# Now initialize the HuggingFaceEmbeddings with just the model name
embeddings = HuggingFaceEmbeddings(
    model_name=model_name  # Pass the model name as a string
)

# If you want to handle device setting manually, you will need to use the 'model' you created
# for additional tasks like embedding creation, but HuggingFaceEmbeddings works as expected
# with the model name.



# Explicitly set the device to cpu or cuda
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load environment variables
load_dotenv()

GROQ_API = os.environ.get("GROQ_API_KEY")
DB_UNAME = os.environ.get("DB_UNAME")
DB_PASS = os.environ.get("DB_PASS")

# Setup the text splitter
text_splitter = CharacterTextSplitter(
    separator="###",
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)

# Load and split documents
texts = []
for file_path in glob("docs/*.txt"):
    with open(file_path, "r") as f:
        doc = f.read()

    file_chunks = text_splitter.create_documents(
        [doc],
        metadatas=[{"source": file_path}]
    )
    texts.extend(file_chunks)

# # Initialize embeddings and vector store
# embeddings = HuggingFaceEmbeddings(
#     model_name="sentence-transformers/all-MiniLM-L6-v2",
#     device=device
# )

schema_store = Chroma.from_documents(
    texts,
    embedding=embeddings,
    collection_name="schema_rag"
)

schema_retriever = schema_store.as_retriever(k=4)

# Setup the database connection
username = DB_UNAME
password = DB_PASS
db_ip = "localhost"
db_port = "5432"
database = "postgres"
engine = create_engine(f"postgresql+psycopg2://{username}:{password}@{db_ip}:{db_port}/{database}")

# Define tools
@tool
def query_vecdb(question: str) -> str:
    """Retrieve relevant database schema based on the user question."""
    docs = schema_retriever.invoke(question)
    return "\n\n".join(d.page_content for d in docs)

@tool
def run_sql_query(query: str) -> str:
    """Execute a validated read-only SQL query."""
    with engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchmany(5)
        return str(rows)

@tool
def get_table_schema(table_name: str) -> List[Tuple]:
    """Return column schema information for a table."""
    query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = :table_name
        ORDER BY ordinal_position
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"table_name": table_name})
        return result.fetchall()

@tool
def list_table():
    """Return names of tables present in the database."""
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public';
    """
    with engine.connect() as conn:
        result = conn.execute(text(query))
        return str(result.fetchall())

# Initialize the LLM (language model)
llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0
)

# System prompt configuration
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

# Create the agent
agent = create_agent(
    llm,
    tools=[
        query_vecdb,
        get_table_schema,
        list_table,
        run_sql_query,
    ],
    system_prompt=SYSTEM_PROMPT,
)

# Streamlit UI
st.title("PostgreSQL Database Assistant")

question = st.text_area("Ask your SQL-related question:")

if st.button("Submit"):
    if question:
        with st.spinner("Processing your query..."):
            intermediate_output = []
            for step in agent.stream(
                {"messages": [{"role": "user", "content": question}]},
                stream_mode="values",
            ):
                intermediate_output.append(step["messages"][-1].content)
            
            # Display intermediate outputs
            for idx, output in enumerate(intermediate_output):
                st.markdown(f"### Step {idx + 1}")
                st.write(output)

            # Final result (last step output)
            st.markdown("### Final Result:")
            st.write(intermediate_output[-1])
    else:
        st.warning("Please enter a question.")
