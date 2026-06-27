import os
from typing import Type, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class ScopedSerperInput(BaseModel):
    query: str = Field(description="The web search query.")
    query_type: str = Field(description="The category of the search query. Must be one of: compliance, domain_terminology, comparable_features.")

class ScopedSerperTool(BaseTool):
    name: str = "Scoped Web Search Tool"
    description: str = (
        "Search the web for compliance, domain terminology, or comparable features. "
        "You must specify the query and its category query_type. Allowed categories are: "
        "compliance, domain_terminology, comparable_features."
    )
    args_schema: Type[BaseModel] = ScopedSerperInput
    
    def _run(self, query: str, query_type: str) -> str:
        from ..settings import Settings
        settings = Settings.load()
        allowed = settings.research.allowed_query_types
        
        if query_type not in allowed:
            return (
                f"Error: Search query rejected. The query type '{query_type}' is not allowed. "
                f"Allowed categories are: {', '.join(allowed)}."
            )
            
        try:
            # Check for API key
            if not os.environ.get("SERPER_API_KEY"):
                return (
                    f"[MOCK SEARCH RESULTS FOR: '{query}' (Category: '{query_type}')]\n"
                    f"1. Mock result showing compliance guidelines for the queried topic.\n"
                    f"2. Terminology explanation matching standard domain models.\n"
                    f"3. Feature comparison details of industry standard applications."
                )
            
            from crewai_tools import SerperDevTool
            serper = SerperDevTool()
            return serper._run(search_query=query)
        except Exception as e:
            return f"Error executing search: {str(e)}"
