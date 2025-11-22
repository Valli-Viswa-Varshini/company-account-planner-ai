import os
from typing import TypedDict, Annotated, List, Dict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import Tool

# Define State
class AgentState(TypedDict):
    company: str
    goals: str
    messages: List[str]
    research_data: List[str]
    plan_sections: Dict[str, str]
    critique_count: int
    sources: List[str]  # URLs of sources

# Initialize LLM
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Fallback for local dev if not in env but in secrets.toml (manual check)
    # Or just raise a clearer error
    raise ValueError("GEMINI_API_KEY not found in environment variables")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

# Tools
import warnings
from langchain_core._api.deprecation import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

if os.getenv("TAVILY_API_KEY"):
    from langchain_community.tools.tavily_search import TavilySearchResults
    search_tool = TavilySearchResults()
else:
    search_tool = DuckDuckGoSearchRun()

def research_node(state: AgentState):
    company = state["company"]
    goals = state["goals"]
    
    # Define search queries for different aspects
    queries = [
        f"{company} company overview and business model",
        f"{company} key products services and revenue streams",
        f"{company} major competitors and market share",
        f"{company} recent strategic partnerships and news {goals}"
    ]
    
    query_labels = [
        "📊 Researching company overview and business model...",
        "🛍️ Analyzing products, services, and revenue streams...",
        "🏆 Investigating competitors and market position...",
        "📰 Gathering recent news and strategic partnerships..."
    ]
    
    results = []
    messages = []
    sources = []
    
    for q, label in zip(queries, query_labels):
        messages.append(label)  # Progress update
        
        try:
            raw_result = search_tool.invoke(q)
            
            # Extract URLs if available (Tavily returns structured data)
            if isinstance(raw_result, list):
                for item in raw_result:
                    if isinstance(item, dict) and 'url' in item:
                        sources.append(item['url'])
                result_text = "\n".join([str(item) for item in raw_result])
            else:
                result_text = str(raw_result)
            
            results.append(result_text)
        except Exception as e:
            results.append(f"Search failed for {q}: {e}")
            messages.append(f"⚠️ Had trouble finding data for: {label.split('...')[0]}")
    
    combined_results = "\n\n".join(results)
    
    # Add sources to state (we'll need to modify AgentState to include this)
    final_message = f"✅ Gathered comprehensive data from {len(sources)} sources (Overview, Products, Competitors, News)..."
    messages.append(final_message)
    
    return {
        "research_data": [combined_results],
        "messages": messages,
        "sources": sources  # This will be added to state
    }

def critique_node(state: AgentState):
    """Analyze research data for conflicts or gaps"""
    company = state["company"]
    data = "\n".join(state["research_data"])
    
    # Use LLM to detect conflicts or gaps
    critique_prompt = f"""
    Analyze this research data about {company}. Check for:
    1. Conflicting information (e.g., different revenue numbers)
    2. Missing critical information
    3. Outdated data
    
    Research Data:
    {data[:2000]}  # Limit to avoid token overflow
    
    Respond in JSON:
    {{
        "has_conflicts": true/false,
        "conflict_description": "brief description or null",
        "needs_more_research": true/false,
        "quality_score": 1-10
    }}
    """
    
    try:
        response = llm.invoke(critique_prompt)
        import json
        import re
        text = response.content
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        critique = json.loads(text)
        
        # If conflicts found, add a message
        if critique.get("has_conflicts"):
            conflict_msg = f"⚠️ I found some conflicting information about {company}: {critique.get('conflict_description', 'data inconsistencies')}. Proceeding with the most reliable sources..."
            return {
                "critique_count": state.get("critique_count", 0) + 1,
                "messages": [conflict_msg]
            }
    except:
        pass  # Fallback to simple increment
    
    return {"critique_count": state.get("critique_count", 0) + 1}

def synthesize_node(state: AgentState):
    data = "\n".join(state["research_data"])
    company = state["company"]
    
    from langchain_core.output_parsers import JsonOutputParser
    from langchain_core.prompts import PromptTemplate
    from pydantic import BaseModel, Field

    # Define the desired data structure using Pydantic
    class AccountPlan(BaseModel):
        overview: str = Field(description="Company overview")
        products_services: str = Field(description="Key products and services")
        markets_customers: str = Field(description="Target markets and customer segments")
        opportunities: str = Field(description="Strategic opportunities")
        risks: str = Field(description="Potential risks")
        recommended_actions: str = Field(description="Recommended next steps")

    parser = JsonOutputParser(pydantic_object=AccountPlan)

    prompt_template = PromptTemplate(
        template="""
        You are an expert Business Strategist.
        Based on the following research about {company}:
        {data}
        
        Generate a comprehensive Strategic Account Plan.
        {format_instructions}
        
        Ensure the content is professional, detailed, and actionable.
        """,
        input_variables=["company", "data"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = prompt_template | llm | parser

    try:
        result = chain.invoke({"company": company, "data": data})
        return {"plan_sections": result}
    except Exception as e:
        return {
            "plan_sections": {
                "overview": f"Error generating plan: {e}",
                "products_services": "N/A",
                "markets_customers": "N/A",
                "opportunities": "N/A",
                "risks": "N/A",
                "recommended_actions": "N/A"
            }
        }

def should_continue(state: AgentState):
    if state.get("critique_count", 0) < 1: # Force at least one critique/refine loop
        return "research"
    return "synthesize"

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("research", research_node)
builder.add_node("critique", critique_node)
builder.add_node("synthesize", synthesize_node)

builder.set_entry_point("research")
builder.add_edge("research", "critique")
builder.add_conditional_edges("critique", should_continue, {
    "research": "research",
    "synthesize": "synthesize"
})
builder.add_edge("synthesize", END)

graph = builder.compile()
