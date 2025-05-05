import asyncio
from pydantic import BaseModel, Field
from typing import List, Optional
from prompts import SECTION_PLANNING_PROMPT, SECTION_WRITING_PROMPT, FINAL_REPORT_PROMPT
from web_search import get_research_for_topic

class Section(BaseModel):
    """Class representing a section of the report"""
    name: str
    description: str
    content: str = ""

def extract_text_from_llm_response(response):
    """
    Extract text content from an LLM response object.
    
    Args:
        response: Response from LLM, could be string, AIMessage, or other object
        
    Returns:
        str: The text content from the response
    """
    if hasattr(response, 'content'):
        return response.content
    elif hasattr(response, 'text'):
        return response.text
    else:
        return str(response)

async def plan_report_sections(topic, sources, llm):
    """
    Plan the sections of the report based on researched sources.
    
    Args:
        topic (str): Report topic
        sources (str): Formatted source information
        llm: Language model for section planning
        
    Returns:
        list: List of Section objects
    """
    prompt = SECTION_PLANNING_PROMPT.format(topic=topic, sources=sources)
    response = await llm.ainvoke(prompt)
    response_text = extract_text_from_llm_response(response)
    
    # Parse the response to extract sections
    lines = response_text.strip().split('\n')
    sections = []
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a section title (starts with a number)
        if line[0].isdigit() and '. ' in line:
            # This is likely a section title
            if current_section:
                sections.append(current_section)
            
            parts = line.split('. ', 1)
            if len(parts) > 1:
                title = parts[1].split(':', 1)[0].strip()
                current_section = Section(name=title, description="")
        elif current_section:
            # This is likely the description
            if current_section.description:
                current_section.description += " " + line
            else:
                current_section.description = line
    
    # Add the last section
    if current_section:
        sections.append(current_section)
    
    # Ensure we have at least some sections
    if not sections:
        # Create a simple default structure if parsing failed
        sections = [
            Section(name="Introduction", description="Introduction to the topic"),
            Section(name="Main Content", description="Main discussion of the topic"),
            Section(name="Conclusion", description="Summary and conclusions")
        ]
        
    return sections

async def write_section(title, description, sources, llm):
    """
    Write content for a single section using the provided sources.
    
    Args:
        title (str): Section title
        description (str): Section description
        sources (str): Formatted source information
        llm: Language model for content writing
        
    Returns:
        str: Written section content
    """
    prompt = SECTION_WRITING_PROMPT.format(
        section_title=title,
        section_description=description,
        sources=sources
    )
    response = await llm.ainvoke(prompt)
    return extract_text_from_llm_response(response)

async def compile_final_report(topic, sections, llm):
    """
    Compile all sections into a cohesive final report.
    
    Args:
        topic (str): Report topic
        sections (list): List of Section objects with content
        llm: Language model for report compilation
        
    Returns:
        str: Complete report text
    """
    # Format sections for the prompt
    formatted_sections = ""
    for i, section in enumerate(sections, 1):
        formatted_sections += f"Section {i}: {section.name}\n"
        formatted_sections += f"Description: {section.description}\n"
        formatted_sections += f"Content:\n{section.content}\n\n"
    
    prompt = FINAL_REPORT_PROMPT.format(topic=topic, sections=formatted_sections)
    response = await llm.ainvoke(prompt)
    return extract_text_from_llm_response(response)

async def generate_report(topic, llm, tavily_client, num_queries=3):
    """
    Generate a complete report on the given topic.
    
    Args:
        topic (str): Report topic
        llm: Language model
        tavily_client: Initialized Tavily client
        num_queries (int): Number of search queries to generate
        
    Returns:
        str: Complete report text
    """
    print(f"Generating report on: {topic}")
    
    # Step 1: Research the topic
    print("Researching topic...")
    sources = await get_research_for_topic(topic, num_queries, tavily_client, llm)
    
    # Step 2: Plan report sections
    print("Planning report sections...")
    sections = await plan_report_sections(topic, sources, llm)
    print(f"Planned {len(sections)} sections")
    
    # Step 3: Write each section
    print("Writing report sections...")
    for section in sections:
        print(f"  Writing section: {section.name}")
        section.content = await write_section(section.name, section.description, sources, llm)
    
    # Step 4: Compile final report
    print("Compiling final report...")
    final_report = await compile_final_report(topic, sections, llm)
    
    return final_report 