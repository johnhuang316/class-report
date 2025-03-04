#!/usr/bin/env python3
"""
Simple load testing script for the Kindergarten Daily Report Generator.
This script sends concurrent requests to the application to test its performance.

Usage:
    python load_test.py --url http://localhost:8000 --concurrency 10 --requests 100
"""

import argparse
import asyncio
import aiohttp
import time
import logging
from typing import Dict, Any, List
import json
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample Notion page IDs for testing (these are fake IDs)
SAMPLE_PAGE_IDS = [
    "1234567890abcdef1234567890abcdef",
    "abcdef1234567890abcdef1234567890",
    "12345678abcdef123456789abcdef123",
    "abcdef123456789abcdef123456789ab",
    "1234abcdef5678abcdef9012abcdef34"
]

async def send_request(session: aiohttp.ClientSession, url: str, page_id: str) -> Dict[str, Any]:
    """Send a request to the API and return the result."""
    start_time = time.time()
    
    try:
        # 使用新的 API 格式
        sample_content = [
            "今天我們學習了聖經故事。",
            "孩子們唱了讚美詩歌。",
            "我們一起做了手工。",
            "大家都很開心地參與活動。"
        ]
        
        async with session.post(
            f"{url}/generate-report", 
            json={
                "content": "\n".join(sample_content),
                "image_paths": []
            },
            timeout=30
        ) as response:
            status = response.status
            try:
                data = await response.json()
            except:
                data = await response.text()
                
            elapsed = time.time() - start_time
            return {
                "status": status,
                "data": data,
                "elapsed": elapsed,
                "page_id": page_id
            }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "status": 0,
            "data": str(e),
            "elapsed": elapsed,
            "page_id": page_id,
            "error": str(e)
        }

async def health_check(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    """Check if the application is healthy."""
    try:
        async with session.get(f"{url}/health", timeout=5) as response:
            status = response.status
            data = await response.json()
            return {
                "status": status,
                "data": data
            }
    except Exception as e:
        return {
            "status": 0,
            "data": str(e),
            "error": str(e)
        }

async def run_load_test(url: str, concurrency: int, num_requests: int) -> List[Dict[str, Any]]:
    """Run the load test with the specified parameters."""
    logger.info(f"Starting load test: {url}, concurrency={concurrency}, requests={num_requests}")
    
    async with aiohttp.ClientSession() as session:
        # First check if the application is healthy
        health_result = await health_check(session, url)
        if health_result["status"] != 200:
            logger.error(f"Health check failed: {health_result}")
            return []
        
        logger.info(f"Health check passed: {health_result}")
        
        # Create a list of tasks for the requests
        tasks = []
        for i in range(num_requests):
            # Select a random page ID from the sample list
            page_id = random.choice(SAMPLE_PAGE_IDS)
            tasks.append(send_request(session, url, page_id))
        
        # Run the tasks with limited concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request(task):
            async with semaphore:
                return await task
        
        bounded_tasks = [bounded_request(task) for task in tasks]
        
        # Wait for all tasks to complete
        start_time = time.time()
        results = await asyncio.gather(*bounded_tasks)
        total_time = time.time() - start_time
        
        # Log the results
        success_count = sum(1 for r in results if r["status"] == 200)
        error_count = len(results) - success_count
        avg_time = sum(r["elapsed"] for r in results) / len(results) if results else 0
        
        logger.info(f"Load test completed in {total_time:.2f} seconds")
        logger.info(f"Requests: {len(results)}, Success: {success_count}, Errors: {error_count}")
        logger.info(f"Average request time: {avg_time:.2f} seconds")
        logger.info(f"Requests per second: {len(results) / total_time:.2f}")
        
        return results

def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the results of the load test."""
    if not results:
        return {"error": "No results to analyze"}
    
    # Calculate statistics
    response_times = [r["elapsed"] for r in results]
    status_codes = {}
    for r in results:
        status = r["status"]
        if status in status_codes:
            status_codes[status] += 1
        else:
            status_codes[status] = 1
    
    # Find min, max, avg, median, p95, p99 response times
    response_times.sort()
    min_time = min(response_times)
    max_time = max(response_times)
    avg_time = sum(response_times) / len(response_times)
    median_time = response_times[len(response_times) // 2]
    p95_time = response_times[int(len(response_times) * 0.95)]
    p99_time = response_times[int(len(response_times) * 0.99)]
    
    return {
        "total_requests": len(results),
        "status_codes": status_codes,
        "response_times": {
            "min": min_time,
            "max": max_time,
            "avg": avg_time,
            "median": median_time,
            "p95": p95_time,
            "p99": p99_time
        }
    }

def main():
    """Parse arguments and run the load test."""
    parser = argparse.ArgumentParser(description="Load test for Kindergarten Daily Report Generator")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="Base URL of the application")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent requests")
    parser.add_argument("--requests", type=int, default=20, help="Total number of requests to send")
    parser.add_argument("--output", type=str, help="Output file for detailed results (JSON)")
    args = parser.parse_args()
    
    # Run the load test
    results = asyncio.run(run_load_test(args.url, args.concurrency, args.requests))
    
    # Analyze and display the results
    analysis = analyze_results(results)
    logger.info(f"Analysis: {json.dumps(analysis, indent=2)}")
    
    # Save detailed results if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump({"results": results, "analysis": analysis}, f, indent=2)
        logger.info(f"Detailed results saved to {args.output}")

if __name__ == "__main__":
    main()
