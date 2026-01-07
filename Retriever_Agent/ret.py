# %% [markdown]
# SQL RAG AGENT

# %%
import os
from dotenv import load_dotenv 

load_dotenv()

# %%
from langchain_core.documents import Document

def load_txt_and_chunk(path: str) -> list[Document]:
    with open(path, "r") as f:
        raw = f.read()

    chunks = [c.strip() for c in raw.split("###") if c.strip()]
    docs = []

    for chunk in chunks:
        lines = chunk.splitlines()
        title = lines[0].strip() if lines else "unknown"

        docs.append(
            Document(
                page_content=chunk,
                metadata={
                    "type": "schema",
                    "table": title,
                    "source": path
                }
            )
        )

    return docs

schema_docs = load_txt_and_chunk("schema.txt")

# %%
from langchain_text_splitters import CharacterTextSplitter

with open("schema.txt") as f:
    schema_doc = f.read()

text_splitter = CharacterTextSplitter(
    separator="###",
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)

texts = text_splitter.create_documents([schema_doc])
print(texts[0])

# %%
texts

# %%
print(len(schema_docs))
print(schema_docs[0].page_content)
print("Metadata:", schema_docs[0].metadata)

# %%
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

schema_store = Chroma.from_documents(
    schema_docs,
    embedding=embeddings,
    collection_name="schema_rag"
)

schema_retriever = schema_store.as_retriever(k=4)


# %%
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from typing import List, Tuple

engine = create_engine("postgresql+psycopg2://postgres:Nst%401995@localhost:5432/postgres")

@tool
def run_sql_query(query: str) -> str:
    """Execute a read-only SQL query and return rows."""
    
    print("\n--- SQL GENERATED ---")
    print(query)

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

# %%
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0
)

SYSTEM_PROMPT = """
You are a database assistant.

You will be given:
- Relevant database schema context
- A user question

Steps:
1. Understand schema
2. Generate correct PostgreSQL SELECT query
3. Use run_sql tool
4. If query fails, fix and retry
5. Answer clearly

Rules:
- Never modify data
- Never guess columns not in schema
"""


# %%
from langchain.agents import create_agent

agent = create_agent(
    llm,
    tools=[run_sql_query, get_table_schema],
    system_prompt=SYSTEM_PROMPT,
)

# %%
question = "I need info of loans which were disbursed between jan 2023 and june 2023"

# %%
from IPython.display import display, Markdown

schema_context = schema_retriever.invoke(question)
context_text = "\n\n".join(d.page_content for d in schema_context)

response = agent.invoke({
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Schema:\n{context_text}"},
        {"role": "user", "content": question},
    ],
    # "recursion_limit": 10,
})

# agent.invoke returns a structured dict - extract text
display(Markdown(response["messages"][-1].content))

# %% [markdown]
# 

# %% [markdown]
# | Loan ID                              | Customer ID                          | Branch ID                            | Loan Type | Principal    | Interest Rate (%) | Tenure (Months) | Disbursed At | Status |
# | ------------------------------------ | ------------------------------------ | ------------------------------------ | --------- | ------------ | ----------------- | --------------- | ------------ | ------ |
# | 1aec7993-2abd-46d4-9ae4-f1952b9ed951 | ec5bf63f-2a89-460f-a8ea-5fe2674503b2 | dc59f73e-d87a-486f-8f78-9dddff16106d | HOME      | 1,945,675.00 | 13.46             | 36              | 2023-04-07   | NPA    |
# | 70979651-1dff-46d5-95dc-c55557f6a559 | 3024a891-5f3b-45a1-9c1e-e978aeb31601 | 5384586d-6e16-46a7-93e2-aecd70687f04 | AUTO      | 791,717.00   | 16.84             | 60              | 2023-06-25   | NPA    |
# | 84954583-a5b2-45c2-9de0-10a367534495 | 33ea8cc9-a813-48fb-b094-a8f37267d65b | 225ba84c-cf19-4ccb-b5f9-a04f9070fa8c | AUTO      | 143,085.00   | 12.36             | 120             | 2023-01-07   | NPA    |
# | 1f1b7c72-b5fc-4bf4-86f3-f84934514e47 | 60d47bc4-1d9c-49af-990f-834c70e8986e | 225ba84c-cf19-4ccb-b5f9-a04f9070fa8c | PERSONAL  | 1,448,575.00 | 11.26             | 36              | 2023-02-09   | ACTIVE |
# | ff4147e9-feea-4f84-bd46-937cbb0bb4bf | 93c15b25-17e6-4f0f-bfe3-99626dff6045 | 411285e5-25a5-40f8-bca3-dc28ad9cde62 | HOME      | 101,223.00   | 10.45             | 60              | 2023-06-05   | ACTIVE |
# 
# 

# %%
for step in agent.stream(
    {"messages": [{"role": "user", "content": question}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()

# %%
for step in agent.stream(
    {"messages": [{"role": "user", "content": "just give me the names of all tables"}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()

# %%
def streamer_agent(question):
    for step in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        yield step["messages"][-1].pretty_print()

# %%
[msg for msg in streamer_agent("How financially exposed is the bank to each customer?")]

## BadRequestError: Error code: 400 - {'error': {'message': "'messages.3' : for 'role:tool' the following must be satisfied[('messages.3.content' : one of the following must be satisfied[('messages.3.content' : value must be a string) OR ('messages.3.content' : minimum number of items is 1)])]", 'type': 'invalid_request_error'}}
## During task with name 'model' and id 'b4dbd05b-57e9-1a60-e00d-f279c85bb975'

# %%



