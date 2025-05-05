import os
import asyncio
from langchain_groq import ChatGroq
from tavily import AsyncTavilyClient
from report_generator import generate_report
import time
import argparse
from dotenv import load_dotenv

# Load environment variables
print("Loading environment variables...")
load_dotenv()

# Debug print to check if environment variables are loaded
print(f"GROQ_API_KEY present: {'GROQ_API_KEY' in os.environ}")
print(f"TAVILY_API_KEY present: {'TAVILY_API_KEY' in os.environ}")
print(f"First few characters of GROQ_API_KEY: {os.getenv('GROQ_API_KEY')[:5] if os.getenv('GROQ_API_KEY') else 'Not found'}")

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate a structured report on a given topic.')
    parser.add_argument('--topic', type=str, help='Report topic (if not provided, will prompt for input)')
    parser.add_argument('--queries', type=int, default=3, help='Number of search queries to generate per topic (default: 3)')
    parser.add_argument('--model', type=str, default="llama3-70b-8192", help='Groq model to use (default: llama3-70b-8192)')
    parser.add_argument('--temperature', type=float, default=0.2, help='Temperature for LLM (default: 0.2)')
    parser.add_argument('--timeout', type=int, default=180, help='Timeout in seconds for LLM API calls (default: 180)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with more detailed error information')
    parser.add_argument('--output-dir', type=str, default="examples", help='Directory to save generated reports (default: examples)')
    args = parser.parse_args()
    
    # Get API keys from environment variables
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY must be set as an environment variable")
    
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY must be set as an environment variable")
    
    # Print model information
    print(f"Using Groq model: {args.model}")
    
    # Initialize clients
    print("Initializing API clients...")
    try:
        tavily_client = AsyncTavilyClient(api_key=tavily_api_key)
        llm = ChatGroq(
            model=args.model,
            temperature=args.temperature,
            api_key=groq_api_key
        )
    except Exception as e:
        print(f"Error initializing API clients: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return
    
    # Get user input if topic not provided via command line
    topic = args.topic
    if not topic:
        topic = input("Enter the topic for your report: ")
    
    # Record start time
    start_time = time.time()
    
    try:
        # Generate report
        report = await generate_report(
            topic=topic,
            llm=llm,
            tavily_client=tavily_client,
            num_queries=args.queries
        )
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        
        # Create the output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Save report to file in the specified directory
        safe_filename = topic.replace(' ', '_').lower().replace('/', '_').replace('\\', '_')
        filename = os.path.join(args.output_dir, f"{safe_filename}_report.md")
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\nReport generated in {int(minutes)} minutes and {int(seconds)} seconds.")
        print(f"Report saved to: {filename}")
        print("\nHere's a preview of the report:")
        print("=" * 50)
        preview_length = min(500, len(report))
        print(report[:preview_length] + ("..." if len(report) > preview_length else ""))
        print("=" * 50)
    
    except Exception as e:
        print(f"\nError generating report: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc() 