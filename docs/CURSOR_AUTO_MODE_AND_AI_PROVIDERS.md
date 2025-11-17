# Cursor Auto Mode & AI Provider Usage Explained

## 🎯 **Part 1: How Agent-MCP Works with Cursor's "Auto" Mode**

### **What is Cursor's Auto Mode?**

Cursor's "Auto" mode is a feature where Cursor's AI assistant **automatically decides** when to use MCP tools without you explicitly asking. It's like having an AI assistant that proactively uses tools when it thinks they'll help.

---

### **How Auto Mode Works with Agent-MCP**

#### **1. Automatic Tool Selection**

When you're working in Cursor with Agent-MCP connected:

**You type:**
> "I need to implement user authentication"

**Cursor's AI (in Auto Mode) automatically:**
1. **Recognizes** this is a complex task
2. **Decides** to use Agent-MCP tools
3. **Calls tools automatically:**
   ```python
   # Cursor's AI automatically calls:
   create_agent(agent_id="auth-backend", capabilities=["backend", "auth"])
   create_task(title="Implement user authentication", ...)
   assign_task(task_id="...", agent_id="auth-backend")
   ```
4. **Responds** with what it did:
   > "I've created a backend agent and assigned the authentication task to it. The agent will work on implementing the login system."

**You didn't ask it to create agents or tasks - it did it automatically!**

---

#### **2. Proactive Context Management**

**You're coding and mention:**
> "This function needs to handle OAuth2"

**Cursor's AI automatically:**
1. **Recognizes** you're adding new information
2. **Calls tool:**
   ```python
   update_project_context(
       context_key="auth_oauth2",
       value="OAuth2 implementation details...",
       description="OAuth2 authentication pattern"
   )
   ```
3. **Stores** this in the knowledge graph
4. **Future agents** can now query this context

**Result:** Your project knowledge grows automatically as you work!

---

#### **3. Automatic Task Coordination**

**You say:**
> "The backend API is done, now we need the frontend"

**Cursor's AI automatically:**
1. **Queries** existing tasks: `view_tasks()`
2. **Finds** the backend task
3. **Updates** its status: `update_task_status(task_id="...", status="completed")`
4. **Creates** new frontend task: `create_task(title="Build frontend UI", ...)`
5. **Assigns** to frontend agent: `assign_task(...)`

**All without you explicitly asking!**

---

#### **4. Automatic RAG Queries**

**You ask:**
> "How does our error handling work?"

**Cursor's AI automatically:**
1. **Recognizes** this is a knowledge question
2. **Calls:** `ask_project_rag(query="error handling patterns")`
3. **Agent-MCP:**
   - Searches PostgreSQL RAG embeddings
   - Finds relevant code/docs/comments
   - Returns context
4. **Cursor's AI** uses this context to answer accurately

**Result:** Answers are based on your actual project, not generic knowledge!

---

### **Auto Mode vs. Manual Mode**

#### **Manual Mode (You Control Tools)**
```
You: "Use the create_agent tool to make a backend agent"
Cursor: [Calls create_agent tool]
You: "Now assign a task to it"
Cursor: [Calls assign_task tool]
```

#### **Auto Mode (Cursor Decides)**
```
You: "I need a backend agent for API work"
Cursor: [Automatically calls create_agent, create_task, assign_task]
Cursor: "Done! I've set up a backend agent and assigned it the API task."
```

**Auto Mode = Cursor's AI is proactive and uses tools intelligently**

---

### **How Agent-MCP Tools Appear in Auto Mode**

When Cursor's AI sees you mention:
- **"Create an agent"** → Automatically uses `create_agent`
- **"Assign this task"** → Automatically uses `assign_task`
- **"What do we know about X"** → Automatically uses `ask_project_rag`
- **"Update the context"** → Automatically uses `update_project_context`
- **"List all tasks"** → Automatically uses `view_tasks`

**The AI understands your intent and uses the right tools automatically!**

---

## 🤖 **Part 2: Purpose of OpenAI/Ollama in Agent-MCP**

### **Why Agent-MCP Needs AI Providers**

Agent-MCP uses AI providers (OpenAI or Ollama) for **two main purposes**:

1. **Embeddings** (Vector representations of text)
2. **Chat Completions** (LLM reasoning and generation)

---

## 📊 **1. EMBEDDINGS: The Foundation of RAG**

### **What Are Embeddings?**

Embeddings convert text into **vectors** (arrays of numbers) that capture meaning:

```
"user authentication" → [0.2, 0.8, 0.1, 0.5, ...] (1536 numbers)
"login system"       → [0.3, 0.7, 0.2, 0.4, ...] (1536 numbers)
"database schema"    → [0.1, 0.2, 0.9, 0.3, ...] (1536 numbers)
```

**Similar concepts = similar vectors = can be found via similarity search**

---

### **How Agent-MCP Uses Embeddings**

#### **A. RAG Indexing (Background Process)**

```python
# Runs automatically every 5 minutes
async def run_rag_indexing_periodically():
    # 1. Scan project files (markdown, code, docs)
    files = scan_project_directory()
    
    # 2. Chunk the content
    chunks = chunk_files(files)
    
    # 3. Generate embeddings for each chunk
    for chunk in chunks:
        embedding = openai.embeddings.create(
            model="text-embedding-3-large",
            input=chunk.text
        )  # Returns [0.2, 0.8, 0.1, ...]
        
        # 4. Store in PostgreSQL with pgvector
        cursor.execute(
            "INSERT INTO rag_embeddings (chunk_id, embedding) VALUES (%s, %s::vector)",
            (chunk_id, embedding)
        )
```

**Purpose:** Build a searchable knowledge base of your project

**What gets indexed:**
- Markdown files (README, docs, etc.)
- Code files (with code-aware chunking in advanced mode)
- Project context (stored knowledge)
- Task descriptions

---

#### **B. RAG Querying (When You Ask Questions)**

```python
# When you ask: "How does authentication work?"
async def ask_project_rag(query: str):
    # 1. Embed your query
    query_embedding = openai.embeddings.create(
        model="text-embedding-3-large",
        input=query
    )  # [0.25, 0.75, 0.15, ...]
    
    # 2. Vector similarity search in PostgreSQL
    cursor.execute("""
        SELECT chunk_text, source_ref, 
               1 - (embedding <=> %s::vector) as similarity
        FROM rag_embeddings
        ORDER BY embedding <=> %s::vector
        LIMIT 5
    """, (query_embedding, query_embedding))
    
    # 3. Returns most relevant chunks
    # 4. LLM synthesizes answer from chunks
```

**Purpose:** Find relevant project knowledge to answer questions

**Result:** Answers based on YOUR project, not generic knowledge!

---

### **Embedding Models Used**

#### **OpenAI (Default)**
- **Model:** `text-embedding-3-large`
- **Dimensions:** 1536 (simple) or 3072 (advanced)
- **Cost:** ~$0.13 per 1M tokens
- **Quality:** Excellent
- **Speed:** Fast (API call)

#### **Ollama (Local Alternative)**
- **Model:** `nomic-embed-text` (768 dims) or `mxbai-embed-large` (1024 dims)
- **Dimensions:** 768-1024 (depends on model)
- **Cost:** $0 (runs locally)
- **Quality:** Very good (slightly less than OpenAI)
- **Speed:** ~37ms per text (local)

**Configuration:**
```bash
# Use OpenAI (default)
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Use Ollama (local)
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

---

## 🧠 **2. CHAT COMPLETIONS: LLM Reasoning**

### **What Are Chat Completions?**

Chat completions use LLMs (like GPT-4 or Llama) to:
- **Reason** about complex problems
- **Generate** text responses
- **Synthesize** information from multiple sources
- **Make decisions** based on context

---

### **How Agent-MCP Uses Chat Completions**

#### **A. RAG Query Synthesis**

```python
# After finding relevant chunks via vector search
async def query_rag_system(query: str):
    # 1. Vector search finds relevant chunks (using embeddings)
    relevant_chunks = vector_search(query)
    
    # 2. Build context from chunks
    context = build_context(relevant_chunks)
    
    # 3. Use LLM to synthesize answer
    response = openai.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[
            {"role": "system", "content": "You are a helpful assistant..."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
        ]
    )
    
    # 4. Return synthesized answer
    return response.choices[0].message.content
```

**Purpose:** Turn raw chunks into coherent, contextual answers

**Example:**
- **Chunks found:** 5 code snippets about authentication
- **LLM synthesizes:** "Based on your codebase, authentication uses JWT tokens stored in cookies. The login endpoint is at `/api/auth/login` and validates credentials against the users table..."

---

#### **B. Task Placement Validation**

```python
# When creating a task, validate placement using RAG + LLM
async def validate_task_placement(title, description, parent_task):
    # 1. Query RAG about existing tasks
    rag_response = await ask_project_rag(
        f"Analyze task placement: {title} with parent {parent_task}"
    )
    
    # 2. Use LLM to reason about placement
    analysis = openai.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[{
            "role": "system",
            "content": "You are a task hierarchy validator. Analyze if this task placement makes sense..."
        }, {
            "role": "user",
            "content": f"Task: {title}\nRAG Context: {rag_response}\nValidate placement..."
        }]
    )
    
    # 3. Return validation result
    return parse_validation(analysis)
```

**Purpose:** Intelligently validate task hierarchy and suggest improvements

**Example:**
- **You create:** Task "Add user profile page" with no parent
- **LLM analyzes:** "This should be a child of 'Build user dashboard' task based on project structure"
- **Result:** Suggests correct parent task

---

#### **C. PydanticAI Agent Orchestration**

```python
# PydanticAI agents use LLMs for structured reasoning
class AgentOrchestrator:
    def __init__(self):
        # Uses OpenAI or Ollama for agent reasoning
        self.orchestrator = Agent(
            model=OpenAIModel("gpt-4.1-2025-04-14"),  # or Ollama model
            system_prompt="You coordinate multiple agents...",
            result_type=OrchestrationResult
        )
    
    async def orchestrate(self, request):
        # LLM reasons about which agents to use
        # Coordinates RAG agent + Task agent
        # Synthesizes results
        return await self.orchestrator.run(request)
```

**Purpose:** Coordinate multiple agents intelligently

**Example:**
- **Request:** "Build a user dashboard with authentication"
- **LLM orchestrates:**
  1. Use RAG agent to find existing auth code
  2. Use Task agent to create dashboard tasks
  3. Coordinate both agents
  4. Synthesize final plan

---

#### **D. Intent Classification**

```python
# Classify what type of query this is
class QueryIntentClassifier:
    async def classify(self, query: str):
        # Use LLM to classify intent
        response = openai.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=[{
                "role": "system",
                "content": "Classify query intent: code_search, task_management, context_update..."
            }, {
                "role": "user",
                "content": query
            }]
        )
        
        # Returns: "code_search", "task_management", etc.
        return parse_intent(response)
```

**Purpose:** Understand what the user wants to route to the right tool

---

### **Chat Models Used**

#### **OpenAI (Default)**
- **Model:** `gpt-4.1-2025-04-14` (or configurable)
- **Use Cases:**
  - RAG query synthesis
  - Task placement validation
  - Agent orchestration
  - Intent classification
- **Cost:** ~$0.01-0.03 per 1K tokens
- **Quality:** Excellent reasoning

#### **Ollama (Local Alternative)**
- **Model:** `llama3.2`, `codellama`, `mistral`, etc.
- **Use Cases:** Same as OpenAI
- **Cost:** $0 (runs locally)
- **Quality:** Very good (slightly less reasoning capability)
- **Speed:** Depends on hardware

**Configuration:**
```bash
# OpenAI
OPENAI_API_KEY=sk-...
CHAT_MODEL=gpt-4.1-2025-04-14

# Ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.2
```

---

## 🔄 **Complete Flow: How It All Works Together**

### **Example: You Ask Cursor "How does our auth work?"**

#### **Step 1: Cursor's AI (Auto Mode)**
```
Recognizes: Knowledge question
Decides: Use ask_project_rag tool
Calls: ask_project_rag(query="How does our auth work?")
```

#### **Step 2: Agent-MCP Receives Tool Call**
```python
# Tool: ask_project_rag
async def ask_project_rag_tool_impl(arguments):
    query = arguments["query"]  # "How does our auth work?"
    
    # A. Generate query embedding (OpenAI/Ollama)
    query_embedding = openai.embeddings.create(
        model="text-embedding-3-large",
        input=query
    )  # [0.2, 0.8, 0.1, ...]
    
    # B. Vector search in PostgreSQL
    cursor.execute("""
        SELECT chunk_text, source_ref,
               1 - (embedding <=> %s::vector) as similarity
        FROM rag_embeddings
        ORDER BY embedding <=> %s::vector
        LIMIT 5
    """, (query_embedding, query_embedding))
    
    relevant_chunks = cursor.fetchall()
    # Found: 5 code snippets about authentication
    
    # C. Build context from chunks
    context = "\n".join([chunk['chunk_text'] for chunk in relevant_chunks])
    
    # D. Use LLM to synthesize answer (OpenAI/Ollama)
    response = openai.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[
            {"role": "system", "content": "Answer based on project context..."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
    )
    
    answer = response.choices[0].message.content
    # "Based on your codebase, authentication uses JWT tokens..."
    
    return [TextContent(text=answer)]
```

#### **Step 3: Result Back to Cursor**
```
Cursor's AI receives: "Based on your codebase, authentication uses JWT tokens..."
Cursor's AI responds to you: "Here's how authentication works in your project: [answer]"
```

---

## 📊 **Summary: Why OpenAI/Ollama?**

### **Embeddings (Vector Search)**
- **Purpose:** Convert text → vectors for similarity search
- **Used for:** RAG indexing, RAG querying
- **Frequency:** 
  - Indexing: Every 5 minutes (background)
  - Querying: Every time you ask a question
- **Provider Options:** OpenAI (cloud) or Ollama (local)

### **Chat Completions (LLM Reasoning)**
- **Purpose:** Reason, synthesize, generate responses
- **Used for:**
  - RAG query synthesis
  - Task placement validation
  - Agent orchestration
  - Intent classification
- **Frequency:** Every RAG query, task creation, agent coordination
- **Provider Options:** OpenAI (cloud) or Ollama (local)

---

## 💡 **Key Insights**

### **1. Embeddings = Search Engine**
- Like Google's search, but for YOUR project
- Finds relevant code/docs based on meaning, not keywords
- Powers the RAG system

### **2. Chat Completions = Reasoning Engine**
- Like having a smart assistant that understands context
- Synthesizes information from multiple sources
- Makes intelligent decisions

### **3. Together = Intelligent Knowledge System**
- Embeddings find relevant information
- LLM synthesizes it into useful answers
- Result: AI that knows YOUR project intimately

---

## 🎯 **When to Use OpenAI vs. Ollama**

### **Use OpenAI if:**
- ✅ You want best quality
- ✅ You're okay with API costs (~$10-50/month typical)
- ✅ You want cloud-based (no local setup)
- ✅ You need highest reasoning capability

### **Use Ollama if:**
- ✅ You want zero cost
- ✅ You care about privacy (everything local)
- ✅ You have decent hardware (8GB+ RAM)
- ✅ You want offline capability
- ✅ You're doing development/testing

**You can mix them:**
- Use Ollama for embeddings (cheaper, local)
- Use OpenAI for chat completions (better reasoning)

---

## 🔍 **Real-World Example: Complete Flow**

**You in Cursor (Auto Mode):**
> "Create a task to implement user profiles and assign it to the backend agent"

**What Happens:**

1. **Cursor's AI recognizes intent** → Uses Agent-MCP tools

2. **Calls `create_task` tool:**
   ```python
   create_task(
       title="Implement user profiles",
       description="Add user profile endpoints and database schema"
   )
   ```

3. **Agent-MCP validates task placement:**
   - **Embedding:** Converts task description to vector
   - **Vector search:** Finds similar existing tasks
   - **LLM analysis:** "This should be a child of 'User Management' task"
   - **Returns:** Validation with parent suggestion

4. **Agent-MCP creates task** in PostgreSQL

5. **Calls `assign_task` tool:**
   ```python
   assign_task(
       task_id="task_123",
       agent_id="backend-agent"
   )
   ```

6. **Agent-MCP:**
   - Updates task in database
   - Assigns to backend agent
   - Returns success

7. **Cursor's AI responds:**
   > "✅ Created task 'Implement user profiles' and assigned it to backend-agent. The task has been validated and placed under the 'User Management' parent task."

**All automatic! No manual tool calls needed!**

---

## 🎓 **Key Takeaways**

### **Cursor Auto Mode:**
- Cursor's AI **automatically decides** when to use Agent-MCP tools
- You don't need to explicitly call tools
- The AI understands your intent and uses tools proactively
- Makes Agent-MCP feel like a natural extension of Cursor

### **AI Providers (OpenAI/Ollama):**
- **Embeddings:** Power the RAG system (vector search)
- **Chat Completions:** Power reasoning and synthesis
- **Both are essential** for Agent-MCP to work
- **You can choose** OpenAI (cloud) or Ollama (local)

**The result:** An intelligent, context-aware multi-agent system that understands your project and coordinates agents automatically! 🚀
