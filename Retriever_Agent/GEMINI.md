# Project Overview

This project is a Retrieval-Augmented Generation (RAG) agent designed to answer questions about a PostgreSQL database. It uses a Large Language Model (LLM) to understand user queries and generate SQL to retrieve the relevant information from the database.

**Core Technologies:**

*   **LLM Framework:** LangChain
*   **LLM Provider:** Groq
*   **Vector Database:** ChromaDB
*   **Embeddings:** Hugging Face Sentence Transformers
*   **Database:** PostgreSQL
*   **Database Connector:** SQLAlchemy

**Block Diagram:**

```
+-------------------------+
|     User Question       |
+-------------------------+
           |
           v
+-------------------------+
|   LangChain RAG Agent   |
+-------------------------+
           |
           v
+-----------------------------------+      +-----------------------------+
|        `query_vecdb` Tool         |----->|    Chroma Vector Store      |
|   (Calls Schema Retriever)        |      | (Embeddings of docs/*.txt)  |
+-----------------------------------+      +-----------------------------+
           |
           v
+-------------------------+
|  LLM (ChatGroq)         |
| (Generates SQL Query)   |
+-------------------------+
           |
           v
+-------------------------+      +-----------------------------+
|  run_sql_query Tool     |----->|     PostgreSQL Database     |
|   (Executes SQL)        |      | (Connected via SQLAlchemy)  |
+-------------------------+      +-----------------------------+
           |
           v
+-------------------------+
|   Final Answer to User  |
+-------------------------+

Other Tools Available to the Agent:
- query_vecdb
- run_sql_query
- get_table_schema
- list_table
```

The project consists of a PostgreSQL database with a banking-related schema (customers, branches, accounts, loans, and repayments). A **LangChain agent** is used to interact with this database. The agent's knowledge is augmented by a **ChromaDB vector store**, which contains information about the database schema and business rules from the a text file.

When a user asks a question, the agent first retrieves relevant information from the vector store. This context helps the agent generate an accurate SQL query. The generated query is then executed against the PostgreSQL database, and the results are returned to the user.

# Building and Running

## 1. Setup Environment

Create, activate, and install dependencies on a conda environment

Use `.env` file for storing API Key and Database info

## 2. Setup PostgreSQL Database

Follow the instructions in the `README.md` to set up and configure your PostgreSQL database. Then, refer to files in `trad_db` folder to make and populate the database.

## 5. Running the Application

Use the RAG Retriever Agent notebook

---

> model hallucinated currency symbol

**Before:**

================================[1m Human Message [0m=================================

whats the sum of outstanding loan amount of all customer?
==================================[1m Ai Message [0m==================================
Tool Calls:
...

[(Decimal('30788152.00'),)]
==================================[1m Ai Message [0m==================================

The sum of outstanding loan amount of all customers is **$30,788,152.00. --> amount in USD**


---------
added "Currency is INR" in schema txt (or can be added in system prompt also)
---------

**After:**

================================[1m Human Message [0m=================================

whats the sum of outstanding loan amount of all customer?
==================================[1m Ai Message [0m==================================
Tool Calls:

[(Decimal('30788152.00'),)]
==================================[1m Ai Message [0m==================================

The sum of outstanding loan amount of all customers is **₹ 30,788,152.00. --> amount in INR**

Achieved by added an instruction in system prompt

---

