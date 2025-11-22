# Implementation Plan: Company Research AI Agent

## Current Status Analysis
- **Codebase**: Simple Streamlit app (`app.py`) using Google Gemini.
- **Architecture**: Linear (User Input -> LLM -> Output).
- **Discrepancy**: The `readme.md` describes a sophisticated "Cyclic Graph Architecture" with LangGraph and Tavily, but the code does not implement this.
- **Missing Features**:
  - Real-time web search (currently relies on LLM training data).
  - "Updates during research" (currently static).
  - Conflict resolution/Critique loop.

## Proposed Improvements
To meet the "Agentic Behaviour" and "Intelligence" criteria:

1.  **Integrate Real Web Search**:
    - Use **Tavily API** (or DuckDuckGo if free is preferred) to fetch real-time data about companies.
    - This satisfies "Gather information from multiple sources".

2.  **Implement Agentic Workflow**:
    - Create a loop: `Plan -> Search -> Analyze -> (Optional: Search More) -> Synthesize`.
    - Provide intermediate updates to the UI (e.g., "Found annual report, analyzing revenue...").

3.  **Enhance UI/UX**:
    - Improve the Streamlit interface with custom CSS for a "Premium" feel.
    - Add a clear "Researching..." state with dynamic logs.

4.  **Deployment**:
    - Prepare for deployment on Streamlit Cloud (easiest) or Render/Vercel.

## Step-by-Step Plan
1.  **Security**: Move API keys to `secrets.toml` or `.env`.
2.  **Backend Logic**:
    - Create a `ResearchAgent` class that uses tools.
    - Implement `search_company` tool.
    - Implement `generate_plan` with citations.
3.  **Frontend**:
    - Update `app.py` to handle the async nature of the agent (streaming updates).
    - Add "Edit" functionality for the account plan (already partially there, needs refinement).
4.  **Testing**:
    - Test with "Confused User", "Efficient User", etc.

## Questions for User
- Do you have a **Tavily API Key**? (Recommended for search).
- Do you want to stick with **Streamlit** (Python-only, faster) or switch to **Next.js** (More customizable, but more complex)?
