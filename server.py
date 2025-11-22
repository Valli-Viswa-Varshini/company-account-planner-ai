from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load env BEFORE importing agent
load_dotenv()

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
        
        prompt = f"""You are a helpful research assistant. Analyze this user message and determine:
1. Is the user asking to research a company? (yes/no)
2. What is the company name? (extract it, or say "unknown")
3. What are their research goals? (extract specific interests, or say "general overview")
4. Should we ask a clarifying question? (yes/no, and what question)

Previous conversation:
{context}

User message: {message}

Respond in JSON format:
{{
    "wants_research": true/false,
    "company": "company name or unknown",
    "goals": "specific goals or general overview",
    "needs_clarification": true/false,
    "clarifying_question": "question to ask or null"
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
            # Fallback: simple keyword detection
            message_lower = message.lower()
            if any(word in message_lower for word in ['research', 'tell me about', 'analyze', 'account plan']):
                # Try to extract company name (simple heuristic)
                words = message.split()
                company = "unknown"
                for i, word in enumerate(words):
                    if word.lower() in ['about', 'on', 'for'] and i + 1 < len(words):
                        company = words[i + 1].strip('.,!?')
                        break
                
                return {
                    "wants_research": True,
                    "company": company,
                    "goals": "general overview",
                    "needs_clarification": company == "unknown",
                    "clarifying_question": "Which company would you like me to research?" if company == "unknown" else None
                }
            else:
                return {
                    "wants_research": False,
                    "company": "unknown",
                    "goals": "",
                    "needs_clarification": True,
                    "clarifying_question": "I can help you research companies and generate strategic account plans. Which company are you interested in?"
                }

conversation_manager = ConversationManager()

@app.post("/api/chat")
async def chat(request: ResearchRequest):
    """Conversational endpoint that handles natural language"""
    
    async def event_generator():
        try:
            # Parse user intent
            intent = conversation_manager.parse_intent(request.message, request.conversation_history)
            
            # If needs clarification, ask question
            if intent.get("needs_clarification"):
                yield json.dumps({
                    "type": "message",
                    "role": "assistant",
                    "content": intent["clarifying_question"]
                }) + "\n"
                return
            
            # If user wants research
            if intent.get("wants_research") and intent["company"] != "unknown":
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
                # Handle off-topic or unclear requests
                yield json.dumps({
                    "type": "message",
                    "role": "assistant",
                    "content": "I specialize in researching companies and creating strategic account plans. Could you tell me which company you'd like to learn about?"
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
