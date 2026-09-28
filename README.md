# ✈️ Wanderlust Concierge

An AI-powered personal travel assistant built with Google Agent Development Kit (ADK), Google Cloud Agent Platform, and Gemini models. Wanderlust Concierge helps travelers discover destinations, plan customized itineraries, calculate travel budgets in a secure Python sandbox, search real-time weather and nearby attractions, and generate multi-modal scenic images and video previews.

![Wanderlust Concierge Demo](demo.gif)

---

## 🌟 Architecture & Implemented Capabilities

Wanderlust Concierge is powered by a multi-tool agent architecture integrated with Google Cloud services:

### 🗄️ Firestore Destination Catalog
- **Destination Lookup & Browsing**: Streams travel destination records from Google Cloud Firestore (`destinations` collection), supporting filtering by travel categories (Culture & History, Beach & Coastal, Urban & Culinary, Nature & Adventure).
- **Detailed Information**: Fetches full details, daily budget baselines, and key attractions for specific destinations.

### 🧮 Python Sandbox Code Execution
- **Trip Budget Calculation**: Executes Python code inside `AgentEngineSandboxCodeExecutor` to calculate detailed daily expense breakdowns, accommodation estimates, food budgets, and activity costs dynamically.

### 🌤️ Live Weather & Location Intelligence
- **Weather Forecasts**: Retrieves real-time weather conditions and temperature forecasts for target cities.
- **Geocoding & Nearby Attractions**: Converts addresses to geographic coordinates and queries nearby points of interest (restaurants, lodging, landmarks) using Google Maps Places API.

### 📸 Multi-Modal Image & Video Generation
- **Scenic Landmark Visuals**: Generates high-quality destination images using `gemini-3.1-flash-lite-image` in the `global` region and uploads the image bytes directly to Google Cloud Storage (`wanderlust-concierge-media-099df584`).
- **AI Destination Video Previews**: Generates short scenic travel video previews using Google's Omni model (`gemini-omni-flash-preview`) via the Vertex AI Interactions API, saving ADK session artifacts and serving public Cloud Storage media URLs.

### 🧠 Session Memory Bank
- **Dietary & Preference Recall**: Integrates `VertexAiMemoryBankService` to persist user travel preferences, dietary restrictions, and allergies across sessions, automatically tailoring itineraries accordingly.

### 🎨 Structured A2UI Protocol & Custom Web UI
- **A2UI v0.8 Interface**: Emits structured A2UI component JSON (Cards, Columns, Rows, Images, Text) for rich UI rendering alongside a custom FastAPI proxy and plain HTML5 chat frontend with glassmorphism design.

---

## 🛠️ Project Structure

```
wanderlust-concierge/
├── app/
│   ├── agent.py              # Root ADK Agent definition & system prompts
│   ├── tools.py              # Firestore, Weather, Places, Image & Video tools
│   ├── a2ui_utils.py         # A2UI response formatting & callbacks
│   └── fast_api_app.py       # FastAPI application entrypoint
├── frontend/
│   ├── main.py               # Minimal FastAPI proxy for Cloud Run deployment
│   ├── Procfile              # Uvicorn entrypoint for web execution
│   └── static/
│       └── index.html        # Custom chat interface with A2UI renderer
├── agents-cli-manifest.yaml  # Agent Platform deployment metadata
└── README.md
```

---

## 🚀 Setup & Local Execution Instructions

### Prerequisites
- Python 3.11+
- Google Cloud SDK (`gcloud`) authenticated to your GCP project
- Google Maps API key (for Places search)

### 1. Clone & Setup Environment

```bash
git clone <repository-url>
cd wanderlust-concierge

# Initialize Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r app/requirements.txt
pip install -r frontend/requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `frontend/` folder:

```bash
AGENT_ENGINE_RESOURCE_NAME=projects/<YOUR_PROJECT_ID>/locations/us-east1/reasoningEngines/<YOUR_REASONING_ENGINE_ID>
AGENT_DIRECTORY=app
GOOGLE_MAPS_API_KEY=<YOUR_GOOGLE_MAPS_API_KEY>
```

### 3. Start Local Frontend Proxy & Chat Interface

```bash
cd frontend
python main.py
```

Open your web browser and navigate to the port reported by Uvicorn (typically port 8080) to interact with Wanderlust Concierge locally.

---

## ☁️ Deployment Instructions

### Deploy Agent to Agent Platform

```bash
agents-cli deploy \
  --project <YOUR_PROJECT_ID> \
  --no-confirm-project \
  --update-env-vars GOOGLE_MAPS_API_KEY=<YOUR_GOOGLE_MAPS_API_KEY>
```

### Deploy Frontend Web App to Cloud Run

```bash
cd frontend
gcloud run deploy wanderlust-concierge-frontend \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="<YOUR_AGENT_ENGINE_RESOURCE_NAME>",AGENT_DIRECTORY="app"
```
