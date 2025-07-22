from fastapi import FastAPI, Request
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List
import platform
import oneagent
import oneagent.sdk as onesdk # All other SDK functions.
from oneagent.common import AgentState
import math

# Detect Python implementation (eg. CPython)
print(platform.python_implementation())

sdk = oneagent.get_sdk()

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
        with oneagent.get_sdk().trace_incoming_remote_call('method', 'service', 'endpoint'):
            pass
        if sdk.agent_state not in (AgentState.ACTIVE, AgentState.TEMPORARILY_INACTIVE):
            print('Too bad, you will not see data from this process.')
            print('Agent state:', oneagent.get_sdk().agent_state)
            print('Agent found:', oneagent.get_sdk().agent_found)
            print('Agent is compatible:', oneagent.get_sdk().agent_is_compatible)
            print('Agent version:', oneagent.get_sdk().agent_version_string)
        oneagent.shutdown()
        return 'SDK should work (but agent might be inactive).'
    else:
        return 'SDK will definitely not work (i.e. functions will be no-ops):', init_result

@app.get("/oneagentsdk/testtrace", tags=["OneAgent Python SDK"])
async def testTrace(request: Request):
    # Initialize SDK if not already done
    if not oneagent.initialize():
        init_result = oneagent.initialize()
        if not init_result:
            return {"error": "OneAgent SDK failed to initialize"}

    sdk = oneagent.get_sdk()

    # Create web application info (similar to the documentation example)
    wappinfo = sdk.create_web_application_info(
        virtual_host=request.headers.get("host", "localhost"),
        application_id="PythonSnekApp",
        context_root="/"
    )

    with wappinfo:
        # Trace incoming web request
        wreq = sdk.trace_incoming_web_request(
            webapp_info=wappinfo,
            url=str(request.url),
            method=request.method,
            headers=dict(request.headers),
            remote_address=request.client.host if request.client else "unknown"
        )

        with wreq:
            # Set response code
            wreq.set_status_code(200)

            # Add custom attributes
            sdk.add_custom_request_attribute("framework", "FastAPI")
            sdk.add_custom_request_attribute("endpoint", "/oneagentsdk/testtrace")

            # Trace a database operation (as shown in documentation)
            db_info = sdk.create_database_info(
                "test_db",  # database name
                "POSTGRESQL",  # vendor
                onesdk.Channel(onesdk.ChannelType.TCP_IP, "localhost:5432")  # connection
            )

            db_trace = sdk.trace_sql_database_request(
                database=db_info,
                sql="SELECT * FROM dummy",
            )
            with db_trace:
                await asyncio.sleep(0.1)  # Simulate DB query
                db_trace.set_rows_returned(1)

            # Trace a remote call
            remote_trace = sdk.trace_outgoing_remote_call(
                "payment_service",
                "process_payment",
                "payment.service:8080",
                onesdk.Channel(onesdk.ChannelType.IN_PROCESS, 'localhost'),
                "POST",
            )
            with remote_trace:
                await asyncio.sleep(0.2)  # Simulate remote call
                # remote_trace.set_status_code(200)

            # Calculate primes (CPU work simulation)
            primes = []
            for num in range(2, 100):
                if all(num % i != 0 for i in range(2, int(math.sqrt(num)) + 1)):
                    primes.append(num)

            # Add response headers
            wreq.add_response_headers({
                "Content-Type": "application/json",
                "X-Custom-Header": "PythonSnek"
            })
            # Shutdown SDK
            shutdown_error = oneagent.shutdown()
            if shutdown_error:
                print('Error shutting down SDK:', shutdown_error)

            return {
                "message": "Trace test completed successfully",
                "primes_calculated": len(primes),
                "sdk_status": oneagent.initialize(),
                "trace_details": {
                    "web_request": True,
                    "database": True,
                    "remote_call": True
                }
            }


@app.get("/simple-trace")
async def simple_trace(request: Request):
    # Initialize OneAgent SDK
    if not oneagent.initialize():
        return {"error": "OneAgent SDK not initialized"}

    sdk = oneagent.get_sdk()

    # 1️⃣ Trace ONLY the incoming HTTP request (will appear in Dynatrace)
    with sdk.create_web_application_info(
        virtual_host=request.headers.get("host", "localhost"),
        application_id="PythonSnekApp",
        context_root="/"
    ) as web_app_info:
        
        with sdk.trace_incoming_web_request(
            web_app_info,
            str(request.url),
            request.method,
            headers=dict(request.headers),
            remote_address=request.client.host if request.client else "unknown"
        ) as web_trace:
            web_trace.set_status_code(200)  # Mark the request as successful
            sdk.add_custom_request_attribute("endpoint", "/simple-trace")
            oneagent.shutdown()

            return {"message": "This is a single traced request!"}