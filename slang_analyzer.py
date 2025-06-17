#!/usr/bin/env python3
"""
Slang Term Analyzer - Core Functions
Clean, focused analysis functions for slang term interpretation.
"""

import os
import asyncio
import time
from typing import List, Dict, Any

import anthropic




def get_api_key() -> str:
    """Get Anthropic API key from environment variable."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return api_key


async def analyze_single_haiku(client: anthropic.AsyncAnthropic, slang_term: str) -> str:
    """Single async call to Claude 3.5 Haiku."""
    prompt = f"""What could the slang term "{slang_term}" stand for as an acronym? 
Give me 3-5 creative and plausible interpretations of what each letter could represent.
Be imaginative but keep it reasonable for internet/text slang.

Format your response as a simple list, one interpretation per line."""

    try:
        message = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=500,
            temperature=1.0,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"


async def parse_single_sonnet(client: anthropic.AsyncAnthropic, haiku_result: str, slang_term: str) -> Dict[str, Any]:
    """Single async call to Claude 4 Sonnet for parsing using tool calls."""
    
    # Create dynamic schema for the slang term
    letter_properties = {}
    for letter in slang_term.lower():
        letter_properties[letter] = {
            "type": "string",
            "description": f"What the letter '{letter.upper()}' stands for in this acronym"
        }

    parse_tool = {
        "name": "parse_acronym_definition",
        "description": "Parse and structure an acronym definition",
        "input_schema": {
            "type": "object",
            "properties": {
                "term": {
                    "type": "string",
                    "description": "The slang term being analyzed"
                },
                "primary_meaning": {
                    "type": "string", 
                    "description": "The full expansion of the acronym (e.g., 'You Only Live Once')"
                },
                "letter_breakdown": {
                    "type": "object",
                    "properties": letter_properties,
                    "required": list(letter_properties.keys()),
                    "description": "Breakdown of what each letter in the acronym stands for"
                }
            },
            "required": ["term", "primary_meaning", "letter_breakdown"]
        }
    }

    prompt = f"""Parse this interpretation of the slang term "{slang_term}" as an acronym.

Analysis to parse:
{haiku_result}

Extract the most likely meaning from this analysis. If multiple interpretations are given, pick the most plausible one."""

    try:
        message = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            temperature=0.1,
            tools=[parse_tool],
            tool_choice={"type": "tool", "name": "parse_acronym_definition"},
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract tool call result
        for content_block in message.content:
            if content_block.type == "tool_use":
                return content_block.input
        
        return {
            "term": slang_term,
            "primary_meaning": "Parse failed - no tool use",
            "letter_breakdown": {}
        }
        
    except Exception as e:
        return {
            "term": slang_term,
            "primary_meaning": "Parse failed",
            "error": str(e)
        }


async def analyze_with_haiku(client: anthropic.AsyncAnthropic, slang_term: str, num_runs: int = 100) -> List[str]:
    """Analyze slang term with Claude 3.5 Haiku."""
    # Create tasks for all runs
    tasks = [
        analyze_single_haiku(client, slang_term)
        for _ in range(num_runs)
    ]
    
    # Run with limited concurrency
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
    
    async def run_with_semaphore(task):
        async with semaphore:
            return await task
    
    # Execute all tasks
    results = await asyncio.gather(*[run_with_semaphore(task) for task in tasks])
    
    # Filter out error results
    valid_results = [r for r in results if not r.startswith("Error:")]
    return valid_results


async def parse_with_sonnet(client: anthropic.AsyncAnthropic, haiku_results: List[str], slang_term: str) -> List[Dict[str, Any]]:
    """Parse each Haiku result with Claude 4 Sonnet."""
    # Create tasks for all parsing jobs
    tasks = [
        parse_single_sonnet(client, haiku_result, slang_term)
        for haiku_result in haiku_results
    ]
    
    # Run with limited concurrency
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
    
    async def run_with_semaphore(task):
        async with semaphore:
            return await task
    
    # Execute all tasks
    parsed_results = await asyncio.gather(*[run_with_semaphore(task) for task in tasks])
    return parsed_results


# CLI version for backwards compatibility
async def run_analysis(slang_term: str, sample_size: int):
    """Run the complete analysis pipeline."""
    api_key = get_api_key()
    client = anthropic.AsyncAnthropic(api_key=api_key)
    
    try:
        print(f"Analyzing '{slang_term}' with {sample_size} samples...")
        
        # Generate interpretations
        haiku_results = await analyze_with_haiku(client, slang_term, sample_size)
        print(f"Generated {len(haiku_results)} interpretations")
        
        # Parse results
        parsed_results = await parse_with_sonnet(client, haiku_results, slang_term)
        print(f"Parsed {len(parsed_results)} results")
        
        return {
            'haiku_results': haiku_results,
            'parsed_results': parsed_results
        }
        
    finally:
        await client.close()


def main():
    """Simple CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze slang terms using Claude models")
    parser.add_argument("slang_term", help="The slang term to analyze")
    parser.add_argument("--sample-size", type=int, default=50, help="Number of samples (default: 50)")
    
    args = parser.parse_args()
    
    try:
        results = asyncio.run(run_analysis(args.slang_term, args.sample_size))
        
        # Simple output
        valid_results = [r for r in results['parsed_results'] if 'error' not in r]
        print(f"\n=== Results for '{args.slang_term}' ===")
        print(f"Valid results: {len(valid_results)}")
        
        # Show top interpretations
        from collections import Counter
        meanings = [r.get('primary_meaning', '') for r in valid_results]
        top_meanings = Counter(meanings).most_common(5)
        
        print("\nTop interpretations:")
        for i, (meaning, count) in enumerate(top_meanings, 1):
            print(f"{i}. {meaning} ({count} times)")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()