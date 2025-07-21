from fastapi import FastAPI
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List
import platform
import oneagent
import math

# Detect Python implementation (eg. CPython)
print(platform.python_implementation())

description = """
Python Snek API helps you do awesome stuff. 🚀
"""

tags_metadata = [
    {
        "name": "OneAgent Python SDK",
        "description": "OneAgent Python SDK initialization",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://github.com/Dynatrace/OneAgent-SDK-for-Python",
        },
    },
]

app = FastAPI(
        title="Python Snek App",
        description=description,
        summary="This is a backend test API for Python Snek Testing",
        version="0.0.1",
        openapi_tags=tags_metadata,
    )

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.get("/oneagentsdk/init", tags=["OneAgent Python SDK"])
async def initOneAgentSDK():
    init_result = oneagent.initialize()
    # print('OneAgent SDK initialization result' + repr(init_result))
    if init_result:
        return 'SDK should work (but agent might be inactive).'
    else:
        return 'SDK will definitely not work (i.e. functions will be no-ops):', init_result

@app.get("/oneagentsdk/testtrace", tags=["OneAgent Python SDK"])
async def testTrace():
    with oneagent.get_sdk().trace_incoming_remote_call('method', 'service', 'endpoint'):
        pass
    # Perform some complex mathematical operations
    result = 0
    for i in range(1000):
        result += (i ** 2) * (math.sin(i) + math.cos(i))
    # Simulate heavy processing with sleep
        await asyncio.sleep(2)
        return result
    
    


# Store intervals data in memory
# intervals_data: Dict[str, List[Dict]] = {}

# @app.post("/intervals/create")
# async def create_interval(start: int, end: int, step: int = 1):
#     """Create a complex interval with validation and processing"""
#     try:
#         # Validate input parameters
#         if start >= end:
#             return {"error": "Start must be less than end"}
#         if step <= 0:
#             return {"error": "Step must be positive"}
            
#         # Generate unique interval ID
#         interval_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
#         # Calculate interval points with complex logic
#         points = []
#         current = start
#         while current <= end:
#             # Add some complexity with mathematical transformations
#             transformed_value = {
#                 "original": current,
#                 "squared": current ** 2,
#                 "cubic": current ** 3,
#                 "timestamp": datetime.now() + timedelta(seconds=current),
#                 "fibonacci": calculate_fibonacci(current % 10)  # Get fibonacci of last digit
#             }
#             points.append(transformed_value)
#             current += step
            
#         # Store interval data
#         intervals_data[interval_id] = points
        
#         return {
#             "interval_id": interval_id,
#             "points_count": len(points),
#             "start": start,
#             "end": end,
#             "step": step
#         }
        
#     except Exception as e:
#         return {"error": str(e)}

# @app.get("/intervals/{interval_id}")
# async def get_interval(interval_id: str):
#     """Retrieve interval data with additional analytics"""
#     if interval_id not in intervals_data:
#         return {"error": "Interval not found"}
        
#     points = intervals_data[interval_id]
    
#     # Calculate analytics
#     analytics = {
#         "total_points": len(points),
#         "average_original": sum(p["original"] for p in points) / len(points),
#         "max_squared": max(p["squared"] for p in points),
#         "min_squared": min(p["squared"] for p in points),
#         "timestamp_range": {
#             "start": min(p["timestamp"] for p in points),
#             "end": max(p["timestamp"] for p in points)
#         }
#     }
    
#     return {
#         "interval_id": interval_id,
#         "points": points,
#         "analytics": analytics
#     }

# def calculate_fibonacci(n: int) -> int:
#     """Helper function to calculate fibonacci number"""
#     if n <= 0:
#         return 0
#     elif n == 1:
#         return 1
#     else:
#         a, b = 0, 1
#         for _ in range(2, n + 1):
#             a, b = b, a + b
#         return b

# @app.delete("/intervals/{interval_id}")
# async def delete_interval(interval_id: str):
#     """Delete an interval"""
#     if interval_id not in intervals_data:
#         return {"error": "Interval not found"}
        
#     del intervals_data[interval_id]
#     return {"message": f"Interval {interval_id} deleted successfully"}
