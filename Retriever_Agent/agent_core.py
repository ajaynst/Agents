import os
from dotenv import load_dotenv
from langchain_text_splitters import CharacterTextSplitter
from glob import glob
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from output_formatter import format_output

class SQLAgent:
    def __init__(self):
        load_dotenv()
        self.db_uname = os.environ.get("DB_UNAME")
        self.db_pass = os.environ.get("DB_PASS")
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.db_ip = "localhost"
        self.db_port = "5432"
        self.database = "postgres"
        self.engine = self._create_db_engine()
        self.llm = self._initialize_llm()
        self.schema_retriever = self._setup_vector_store()
        self.agent = self._create_agent()

    def _create_db_engine(self):
        return create_engine(
            f"postgresql+psycopg2://{self.db_uname}:{self.db_pass}@{self.db_ip}:{self.db_port}/{self.database}"
        )

    def _initialize_llm(self):
        return ChatGroq(model="llama3-8b-8192", temperature=0, api_key=self.groq_api_key)

    def _setup_vector_store(self):
        text_splitter = CharacterTextSplitter(
            separator="###",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        texts = []
        for file_path in glob("docs/*.txt"):
            with open(file_path, "r") as f:
                doc = f.read()
            file_chunks = text_splitter.create_documents(
                [doc], metadatas=[{"source": file_path}]
            )
            texts.extend(file_chunks)

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        schema_store = Chroma.from_documents(
            texts, embedding=embeddings, collection_name="schema_rag"
        )
        return schema_store.as_retriever(k=4)

    def _create_agent(self):
        @tool
        def query_vecdb(question: str) -> str:
            """
            Retrieve relevant database schema and business rules based on the user question.
            Always call this before generating SQL.
            """
            docs = self.schema_retriever.invoke(question)
            return "\n\n".join(d.page_content for d in docs)

        @tool
        def run_sql_query(query: str) -> str:
            """Execute a validated read-only SQL query and return the raw result."""
            print("\n--- SQL GENERATED ---")
            print(query)
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(query))
                    rows = result.mappings().all()
                    return rows
            except Exception as e:
                return f"Error executing query: {e}"

        @tool
        def request_clarification(reason: str) -> str:
            """Ask the user for clarification before generating SQL."""
            return f"CLARIFICATION_NEEDED: {reason}"

        tools = [query_vecdb, run_sql_query, request_clarification]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are an expert PostgreSQL query assistant for a banking database. Your primary goal is to help users by understanding their natural language questions, generating accurate SQL queries, and providing answers in a clear, human-readable format.

**Your Operating Procedure:**

1.  **Understand the User's Goal:** Analyze the user's question to determine their intent.

2.  **Consult the Knowledge Base:** ALWAYS start by using the `query_vecdb` tool with the user's question. This tool provides you with critical information about the database schema, business rules, and JOIN relationships. This is your primary source of truth for how to query the database.

3.  **Ask for Clarification (If Necessary):**
    *   If the user's question is ambiguous (e.g., "show me John's data"), or a term is vague ("top customers", "recent activity"), you MUST use the `request_clarification` tool to ask for more specific information.
    *   Do not proceed with a query if you are uncertain. It is better to ask for clarification than to return an incorrect answer.

4.  **Formulate the SQL Query:**
    *   Based on the user's intent and the information from the knowledge base, construct a single, syntactically correct PostgreSQL SELECT query.
    *   **CRITICAL RULE**: You MUST apply the `deleted_at IS NULL` filter for every table involved in the query unless the user explicitly asks for historical or deleted data.
    *   Do not invent table or column names. Only use what is described in the knowledge base.

5.  **Execute the Query:**
    *   Use the `run_sql_query` tool to execute the query.

6.  **Present the Results:**
    *   After getting the results from `run_sql_query`, you must decide on the best format for the user.
    *   If the result is a single value (e.g., a count, sum, or average), create a concise, natural-language sentence.
    *   If the result contains multiple rows or columns, format it as a Markdown table.
    *   If there are no results, inform the user that no matching records were found.

**Restrictions:**
*   You are a read-only assistant. You MUST NOT generate any SQL that modifies the database (no INSERT, UPDATE, DELETE, etc.).
*   Never expose sensitive information like user passwords.
*   Do not respond with the SQL query itself, only the final, formatted answer.
"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        agent = create_agent(model=self.llm, tools=tools, system_prompt=prompt)
        
        return agent

    def invoke(self, question: str):
        try:
            result = self.agent.invoke({
                "input": question,
            })
            
            output = result.get("output", "")
            if "CLARIFICATION_NEEDED" in output:
                return output
            
            if isinstance(output, list) and all(isinstance(i, dict) for i in output):
                 return format_output(question, output)

            return output

        except Exception as e:
            return f"An error occurred: {e}"

if __name__ == '__main__':
    sql_agent = SQLAgent()
    # Example usage:
    # result = sql_agent.invoke("What is the total number of customers?")
    # print(result)
    # result = sql_agent.invoke("Show me all the loans for the customer with id '3024a891-5f3b-45a1-9c1e-e978aeb31601'")
    # print(result)
