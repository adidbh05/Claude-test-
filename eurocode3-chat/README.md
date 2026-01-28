# Eurocode 3 Structural Design Chat

An AI-powered chat application specialized in steel structural design according to **Eurocode 3 (EN 1993)**.

![Steel Structure Design](https://img.shields.io/badge/Standard-EN%201993-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-red)

## Features

- **Expert Knowledge**: Comprehensive understanding of EN 1993-1-1 through EN 1993-1-12
- **Step-by-Step Calculations**: Detailed solutions with proper notation and clause references
- **Conversation Memory**: Persistent storage of design discussions
- **Rate Limiting**: Built-in protection against API abuse
- **Modern UI**: Clean, structural engineering-themed interface
- **LLM Integration**: Support for OpenAI, Anthropic, Ollama, and local models

## Design Capabilities

| Category | Topics |
|----------|--------|
| Cross-section | Classification (Class 1-4), effective properties |
| Resistance | Tension, compression, bending, shear, combined actions |
| Stability | Flexural buckling, lateral-torsional buckling, plate buckling |
| Connections | Bolted (bearing, slip-resistant), welded (fillet, butt) |
| Materials | S235, S275, S355, S420, S460, stainless steels |
| Special | Fatigue (EN 1993-1-9), fire design (EN 1993-1-2) |

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd eurocode3-chat

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### Configuration

Edit `.env` to configure:

```env
# Use mock LLM for testing (no API key needed)
USE_MOCK_LLM=true

# Or connect to real LLM
USE_MOCK_LLM=false
LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here
```

### Running the Application

```bash
# From the project root
cd backend
python -m uvicorn main:app --reload --port 8000

# Or use the run script
python run.py
```

Visit http://localhost:8000 in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send a message and receive AI response |
| GET | `/api/conversations` | List all conversations |
| GET | `/api/conversations/{id}` | Get conversation history |
| DELETE | `/api/conversations/{id}` | Delete a conversation |
| GET | `/api/rate-limit` | Get current rate limit status |
| GET | `/health` | Service health check |

### Example API Usage

```bash
# Send a chat message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Calculate the bending resistance of an IPE 300 in S355 steel"}'

# List conversations
curl http://localhost:8000/api/conversations
```

## Project Structure

```
eurocode3-chat/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── models.py          # Pydantic models
│   ├── database/
│   │   ├── __init__.py
│   │   └── memory.py          # SQLite conversation storage
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── rate_limiter.py    # Rate limiting middleware
│   ├── services/
│   │   ├── __init__.py
│   │   └── llm_service.py     # LLM integration + EC3 system prompt
│   └── main.py                # FastAPI application
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css      # Structural engineering theme
│   │   └── js/
│   │       └── app.js         # Frontend application
│   └── templates/
│       └── index.html         # Main HTML template
├── config/
│   └── settings.py            # Application settings
├── requirements.txt
├── .env.example
├── run.py
└── README.md
```

## Rate Limits

Default limits (configurable via environment):
- **30 requests per minute**
- **500 requests per hour**

Rate limit headers are included in responses:
- `X-RateLimit-Limit-Minute`
- `X-RateLimit-Remaining-Minute`
- `X-RateLimit-Limit-Hour`
- `X-RateLimit-Remaining-Hour`

## Example Queries

Ask the assistant about:

1. **Beam Design**
   > "Calculate the bending and shear resistance of an IPE 400 beam in S355 steel"

2. **Column Buckling**
   > "Check flexural buckling for an HEB 200 column, L=4m, N_Ed=800kN, S355"

3. **Connection Design**
   > "Design a fillet weld for a 200kN shear connection using S355 steel"

4. **Cross-section Classification**
   > "Classify an IPE 300 section in S355 under combined bending and compression"

5. **Code References**
   > "What are the interaction equations for combined axial and bending in EC3?"

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: SQLite (conversation memory)
- **Frontend**: Vanilla JS, CSS3
- **LLM**: OpenAI/Anthropic API compatible

## Safety Notice

All calculations provided by this application are for educational and preliminary design purposes. Final designs must be verified by a qualified structural engineer in accordance with local regulations and National Annexes.

## License

MIT License - See LICENSE file for details.

---

Built with engineering precision.
