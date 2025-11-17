# Ollama Auto-Detection Feature

## 🎯 **Overview**

Agent-MCP can now automatically detect which Ollama models you have available and select the best one based on the request type (chat, embedding, code).

---

## 🔍 **How It Works**

### **1. Model Detection**

When Agent-MCP starts or when using Ollama, it:
1. Queries Ollama's `/api/tags` endpoint
2. Gets list of all available models
3. Caches the list for 5 minutes (to avoid repeated API calls)
4. Selects best model based on request type

### **2. Model Selection Priority**

**For Chat Models:**
1. `OLLAMA_CHAT_MODEL` env var (if set)
2. `llama3.2` (if available)
3. `llama3.1` (if available)
4. `llama3` (if available)
5. `mistral` (if available)
6. `qwen2.5` (if available)
7. `phi3` (if available)
8. Any model with "llama", "mistral", "qwen", or "phi" in name
9. First available model (fallback)

**For Embedding Models:**
1. `OLLAMA_EMBEDDING_MODEL` env var (if set)
2. `nomic-embed-text` (if available)
3. `mxbai-embed-large` (if available)
4. `all-minilm` (if available)
5. Any model with "embed" or "nomic" in name
6. First available model (fallback)

**For Code Models:**
1. `codellama` (if available)
2. `deepseek-coder` (if available)
3. `qwen2.5-coder` (if available)
4. `llama3.2` (fallback)
5. Any model with "code" in name
6. First available model (fallback)

---

## 🚀 **Usage**

### **Automatic (Recommended)**

Just set `EMBEDDING_PROVIDER=ollama` and Agent-MCP will auto-detect:

```bash
# .env
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_CHAT_MODEL=llama3.2  # Optional - will auto-detect if not set
# OLLAMA_EMBEDDING_MODEL=nomic-embed-text  # Optional - will auto-detect if not set
```

**What happens:**
1. Agent-MCP queries Ollama for available models
2. Selects best chat model (e.g., `llama3.2` if you have it)
3. Selects best embedding model (e.g., `nomic-embed-text` if you have it)
4. Uses them automatically

### **Manual Override**

You can still manually specify models:

```bash
# .env
EMBEDDING_PROVIDER=ollama
OLLAMA_CHAT_MODEL=llama3.1  # Force specific model
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large  # Force specific model
```

If the specified model isn't available, it will fall back to auto-detection.

---

## 📋 **Example Scenarios**

### **Scenario 1: You have llama3.2 and nomic-embed-text**

```bash
# You have:
ollama list
# llama3.2
# nomic-embed-text

# Agent-MCP will use:
# Chat: llama3.2 ✅
# Embedding: nomic-embed-text ✅
```

### **Scenario 2: You have mistral but not llama3.2**

```bash
# You have:
ollama list
# mistral
# nomic-embed-text

# Agent-MCP will use:
# Chat: mistral ✅ (fallback to available model)
# Embedding: nomic-embed-text ✅
```

### **Scenario 3: You have custom model names**

```bash
# You have:
ollama list
# my-custom-llama-model
# my-embedding-model

# Agent-MCP will use:
# Chat: my-custom-llama-model ✅ (detected "llama" keyword)
# Embedding: my-embedding-model ✅ (detected "embed" keyword)
```

---

## 🔧 **API Usage**

### **Check Available Models**

```python
from agent_mcp.external.ollama_service import get_available_ollama_models

models = await get_available_ollama_models()
# Returns: [{"name": "llama3.2", "modified_at": "..."}, ...]
```

### **Get Best Model for Type**

```python
from agent_mcp.external.ollama_service import (
    get_best_chat_model,
    get_best_embedding_model,
    get_best_code_model
)

chat_model = await get_best_chat_model()
# Returns: "llama3.2" (or best available)

embedding_model = await get_best_embedding_model()
# Returns: "nomic-embed-text" (or best available)

code_model = await get_best_code_model()
# Returns: "codellama" (or best available)
```

### **Check if Specific Model Available**

```python
from agent_mcp.external.ollama_service import get_ollama_detector

detector = get_ollama_detector()
is_available = await detector.is_model_available("llama3.2")
# Returns: True or False
```

---

## ⚙️ **Configuration**

### **Cache TTL**

Model list is cached for 5 minutes by default. To change:

```python
from agent_mcp.external.ollama_service import get_ollama_detector

detector = get_ollama_detector()
detector._cache_ttl = 600.0  # 10 minutes
```

### **Force Refresh**

To force refresh the model list:

```python
models = await detector.list_available_models(force_refresh=True)
```

---

## 🐛 **Troubleshooting**

### **Issue: "No Ollama models available"**

**Cause:** Ollama not running or not accessible

**Solution:**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve

# Check OLLAMA_BASE_URL is correct
# For Docker: http://host.docker.internal:11434
# For local: http://localhost:11434
```

### **Issue: Wrong model selected**

**Cause:** Preferred model not available, fallback used

**Solution:**
1. Pull the preferred model: `ollama pull llama3.2`
2. Or manually specify: `OLLAMA_CHAT_MODEL=your-model`

### **Issue: Model detection slow**

**Cause:** First detection queries Ollama API

**Solution:**
- Model list is cached for 5 minutes
- Subsequent requests are instant
- You can increase cache TTL if needed

---

## 📊 **Benefits**

### **1. Automatic Setup**
- No need to manually specify models
- Works with whatever you have installed
- Adapts to your setup

### **2. Smart Fallbacks**
- If preferred model not available, uses best alternative
- Never fails due to missing model
- Graceful degradation

### **3. Flexible**
- Works with custom model names
- Detects models by keywords
- Easy to extend

### **4. Efficient**
- Caches model list (5 min TTL)
- Only queries Ollama when needed
- Fast subsequent requests

---

## 🎯 **Summary**

**Auto-detection means:**
- ✅ No manual model configuration needed
- ✅ Automatically uses best available model
- ✅ Smart fallbacks if preferred model missing
- ✅ Works with any Ollama models you have
- ✅ Cached for performance

**Just set `EMBEDDING_PROVIDER=ollama` and it works!** 🚀
