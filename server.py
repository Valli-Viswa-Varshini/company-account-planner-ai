from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Force reload .env file
load_dotenv(override=True)

# Debug: Print first 10 chars of API key to verify it's the new one
key = os.getenv("GEMINI_API_KEY")
if key:
    print(f"DEBUG: Loaded GEMINI_API_KEY starting with: {key[:10]}...")
else:
    print("DEBUG: GEMINI_API_KEY not found!")

from agent import graph
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import asyncio

app = FastAPI()

# Serve static files (frontend build) in production
from fastapi.staticfiles import StaticFiles
import os
if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
    
    @app.get("/")
    async def serve_frontend():
        from fastapi.responses import FileResponse
        return FileResponse("frontend/dist/index.html")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResearchRequest(BaseModel):
    message: str
    conversation_history: list = []

class ConversationManager:
    """Manages conversational flow and user intent"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))
    
    def parse_intent(self, message: str, history: list) -> dict:
        """Determine user intent and extract company/goals"""
        
        # Build context from history
        context = "\n".join([f"{h['role']}: {h['content']}" for h in history[-3:]])
        
        prompt = f"""You are a helpful, conversational AI Research Assistant. 
Your goal is to help users research companies and generate strategic account plans.

Analyze the user's message and the conversation history.

SCENARIOS:
1. **Research Request**: User wants to research a specific company.
   - Action: Extract 'company' and 'goals'. Set 'wants_research' to true.
   
2. **Confused/Exploratory User**: User asks for suggestions (e.g., "suggest tech companies", "I don't know what to research").
   - Action: You MUST provide helpful suggestions. List 3-4 relevant companies they might be interested in.
   - Set 'wants_research' to false.
   - Set 'response' to your helpful suggestion message.

3. **Clarification Needed**: User is vague but implies a specific company (e.g., "the big search company").
   - Action: Ask a clarifying question.
   - Set 'wants_research' to false.
   - Set 'response' to your clarifying question.

4. **Off-Topic/Chit-Chat**: User says "hello", "how are you", or asks unrelated questions.
   - Action: Be polite but gently guide them back to company research.
   - Set 'wants_research' to false.
   - Set 'response' to a polite reply redirecting to research.

Previous conversation:
{context}

User message: {message}

Respond in JSON format:
{{
    "wants_research": true/false,
    "company": "company name or null",
    "goals": "specific goals or general overview",
    "response": "Your conversational response here (for scenarios 2, 3, 4)"
}}
"""
        
        response = self.llm.invoke(prompt)
        try:
            import json
            import re
            # Extract JSON from markdown code blocks if present
            text = response.content
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            return json.loads(text)
        except:
            # Fallback for parsing errors
            return {
                "wants_research": False,
                "company": None,
                "goals": "",
                "response": "I can help you research companies. Could you tell me which company you're interested in, or ask for suggestions?"
            }

conversation_manager = ConversationManager()

@app.post("/api/chat")
async def chat(request: ResearchRequest):
    """Conversational endpoint that handles natural language"""
    
    async def event_generator():
        try:
            # Parse user intent
            intent = conversation_manager.parse_intent(request.message, request.conversation_history)
            
            # If user wants research and we have a company
            if intent.get("wants_research") and intent.get("company") and intent["company"] != "unknown":
                # Send acknowledgment
                yield json.dumps({
                    "type": "message",
                    "role": "assistant",
                    "content": f"Great! I'll research **{intent['company']}** for you. This will take a moment..."
                }) + "\n"
                
                # Run the agent
                initial_state = {
                    "company": intent["company"],
                    "goals": intent["goals"],
                    "messages": [],
                    "research_data": [],
                    "plan_sections": {},
                    "critique_count": 0,
                    "sources": []
                }
                
                for event in graph.stream(initial_state):
                    yield json.dumps({"type": "agent_event", "data": event}) + "\n"
                    await asyncio.sleep(0.1)
            
            else:
                # Handle conversational responses (Suggestions, Clarifications, Off-topic)
                yield json.dumps({
                    "type": "message",
                    "role": "assistant",
                    "content": intent.get("response", "I specialize in researching companies. Which one would you like to explore?")
                }) + "\n"
                
        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
    
    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

# Keep the old endpoint for backward compatibility
@app.post("/api/research")
async def start_research(request: ResearchRequest):
    initial_state = {
        "company": request.company,
        "goals": request.goals,
        "messages": [],
        "research_data": [],
        "plan_sections": {},
        "critique_count": 0
    }

    async def event_generator():
        try:
            for event in graph.stream(initial_state):
                yield json.dumps(event) + "\n"
                await asyncio.sleep(0.1)
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
