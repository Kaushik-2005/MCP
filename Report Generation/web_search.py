import asyncio
from tavily import AsyncTavilyClient

async def search_web(queries, tavily_client):
    """
    Perform web searches for multiple queries concurrently.
    
    Args:
        queries (list): List of search query strings
        tavily_client: Initialized AsyncTavilyClient
        
    Returns:
        list: List of search results, one per query
    """
    # Limit the number of queries to reduce token usage
    limited_queries = queries[:3]  # Only use the first 3 queries
    
    search_tasks = []
    for query in limited_queries:
        search_tasks.append(
            tavily_client.search(
                query,
                max_results=3,  # Reduced from 5 to 3
                include_raw_content=False,  # Don't include raw content to save tokens
                topic="general"
            )
        )
    
    # Execute all searches concurrently
    search_results = await asyncio.gather(*search_tasks)
    return search_results

def format_sources(search_results, max_tokens_per_source=300):
    """
    Format search results into a readable text for the LLM.
    
    Args:
        search_results (list): List of search result dictionaries from Tavily
        max_tokens_per_source (int): Maximum tokens to include for each source
        
    Returns:
        str: Formatted text with source information
    """
    # Extract and deduplicate sources
    unique_sources = {}
    
    for result in search_results:
        for source in result.get('results', []):
            if source['url'] not in unique_sources:
                unique_sources[source['url']] = source
    
    # Limit the number of sources to reduce token usage
    limited_sources = list(unique_sources.values())[:5]  # Only use the first 5 sources
    
    # Format output
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(limited_sources, 1):
        formatted_text += f"Source {i}:\n"
        formatted_text += f"Title: {source['title']}\n"
        formatted_text += f"URL: {source['url']}\n"
        
        # Truncate content to reduce tokens
        content = source.get('content', '')
        char_limit = max_tokens_per_source * 4  # Approx 4 chars per token
        if len(content) > char_limit:
            content = content[:char_limit] + "... [truncated]"
        formatted_text += f"Content: {content}\n\n"
        
        # Don't include raw content to save tokens
        # raw_content = source.get('raw_content', '')
        # if raw_content:
        #     # Approximate 4 chars per token
        #     char_limit = max_tokens_per_source * 4
        #     if len(raw_content) > char_limit:
        #         raw_content = raw_content[:char_limit] + "... [truncated]"
        #     formatted_text += f"Full content: {raw_content}\n\n"
            
    return formatted_text

async def get_research_for_topic(topic, num_queries, tavily_client, llm):
    """
    Performs complete research on a topic by generating queries and searching.
    
    Args:
        topic (str): The topic to research
        num_queries (int): Number of search queries to generate
        tavily_client: Initialized AsyncTavilyClient
        llm: Language model for generating queries
        
    Returns:
        str: Formatted sources text
    """
    from prompts import QUERY_GENERATION_PROMPT
    
    # Generate search queries
    prompt = QUERY_GENERATION_PROMPT.format(topic=topic, num_queries=num_queries)
    response = await llm.ainvoke(prompt)
    
    # Extract the content from the AIMessage object
    # The attribute may be 'content', 'text', or another field depending on the LLM's response format
    if hasattr(response, 'content'):
        response_text = response.content
    elif hasattr(response, 'text'):
        response_text = response.text
    else:
        # If it's already a string or we can't identify the attribute, convert to string
        response_text = str(response)
    
    # Parse response into a list of queries
    query_lines = [line.strip() for line in response_text.strip().split('\n') if line.strip()]
    
    # Ensure we have at least one query
    if not query_lines:
        # Fallback to using the topic itself as a query
        query_lines = [topic]
    
    print(f"Generated {len(query_lines)} search queries")
    
    # Perform web searches
    search_results = await search_web(query_lines, tavily_client)
    
    # Format sources
    sources = format_sources(search_results)
    
    return sources 