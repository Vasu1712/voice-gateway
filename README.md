# Onix

Onix is a full-duplex, real-time voice AI agent capable of holding natural, interruptible conversations. It leverages GraphRAG (Graph Retrieval-Augmented Generation) to ground its responses in a Neo4j knowledge graph, ensuring factual accuracy while maintaining conversational flow.

Built entirely with local, privacy-first models (Llama 3.2, Whisper, Piper), Onix runs efficiently on consumer hardware.

---

## Architecture

The system uses a WebSocket-based full-duplex pipeline. It listens for user audio, detects speech activity (VAD), transcribes it (STT), queries a Knowledge Graph (GraphRAG), generates a response (LLM), and synthesizes speech (TTS)—all in real time.

---

## Key Features

### Full-Duplex Communication
Talk and listen simultaneously. The agent handles interruptions (barge-ins) naturally—if you interrupt, it stops talking immediately.

### GraphRAG
Uses LangGraph and Neo4j to ground answers in structured data. The agent dynamically writes Cypher queries to fetch relevant information.

### Privacy-First
- **LLM**: Runs locally via Ollama (Llama 3.2)
- **STT**: Runs locally via Faster-Whisper
- **TTS**: Runs locally via Piper

### Low Latency
Optimized for streaming. Text is synthesized into audio token-by-token (streaming TTS) rather than waiting for full sentences.

---

## Tech Stack

### Backend
- Python 3.11  
- FastAPI  
- Uvicorn (WebSockets)

### Graph Database
- Neo4j (requires APOC plugin)

### LLM Orchestration
- LangChain  
- LangGraph  
- LangChain-Neo4j  

### Models
- **LLM**: `llama3.2:1b` (via Ollama)  
- **STT**: `faster-whisper` (tiny / base)  
- **TTS**: `piper` (`en_US-lessac-medium`)

---

## Prerequisites

Before installing Python dependencies, ensure the following external tools are installed.

### 1. Neo4j Database

You need a running Neo4j instance.

**Docker (recommended):**
```bash
docker run -d \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:latest
```

### 2. Ollama

Install Ollama from https://ollama.com
 and pull the required model:

ollama pull llama3.2:1b

### 3. Piper TTS

Download the Piper binary and ensure it is available in your system PATH.

Piper GitHub Releases

Download en_US-lessac-medium.onnx and its corresponding .json config

Place them in: app/models/piper/

## Installation

### Clone the Repository
```bash 
git clone https://github.com/yourusername/onix.git
cd onix
```

### Create a Virtual Environment (python 3.11 is recommended)

python3.11 -m venv .venv
source .venv/bin/activate

### Install Dependencies

Important:
To avoid conflicts between numba (used by Whisper) and langchain-neo4j, install NumPy with a constraint.

pip install "numpy>=1.22,<2.4"
pip install -r requirements.txt


If requirements.txt is missing, install manually:

pip install fastapi uvicorn[standard] faster-whisper ollama \
            langchain-ollama langchain-neo4j langgraph \
            pydantic-settings

Configure Environment Variables

Create a .env file in the project root:

DB_URL=bolt://localhost:7687
DB_USERNAME=neo4j
DB_PASSWORD=password

## Usage

### Start the Server
python3 -m uvicorn app.main:app --reload

### Access the UI

Open your browser and navigate to:

http://localhost:8000


