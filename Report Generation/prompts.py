# Prompt templates for the structured report generator

# Prompt for generating search queries
QUERY_GENERATION_PROMPT = """You are an expert researcher helping to gather information for a report.

The topic of the report is:
{topic}

Your task is to generate {num_queries} search queries that will help gather comprehensive 
information about this topic. Each query should focus on a different aspect of the topic.

Format your response as a list of search queries, one per line."""

# Prompt for planning report sections
SECTION_PLANNING_PROMPT = """You are an expert technical writer planning a report.

The topic of the report is:
{topic}

Based on the following source information:
{sources}

Create an outline with 3-5 sections for a comprehensive report on this topic.
For each section, provide:
1. A clear, descriptive title
2. A brief (1-2 sentence) description of what this section should cover

Format your response as a numbered list of sections with titles and descriptions."""

# Prompt for writing a section
SECTION_WRITING_PROMPT = """You are an expert technical writer creating content for a section of a report.

Section title: {section_title}
Section description: {section_description}

Using the following source information:
{sources}

Write a comprehensive, well-structured section of 300-500 words that:
- Starts with the most important information
- Includes specific facts, figures, and examples from the sources
- Uses clear, professional language
- Formats information with appropriate Markdown (headings, lists, etc.)
- Cites sources where appropriate

Your section should be authoritative, informative, and ready to include in a professional report."""

# Prompt for compiling the final report
FINAL_REPORT_PROMPT = """You are an expert technical writer finalizing a professional report.

Topic: {topic}

Compile the following sections into a cohesive, well-formatted report:

{sections}

Your task is to:
1. Add an engaging introduction (150-200 words) that outlines the report's purpose and key points
2. Add a concise conclusion (150-200 words) that summarizes key findings
3. Format the report consistently using Markdown
4. Add appropriate transitions between sections
5. Include a table of contents

The final report should be professional, cohesive, and ready for business or academic use.""" 