from fastapi import FastAPI, Request
from oneagent.sdk import OneAgentSDK
import time

app = FastAPI()
sdk = OneAgentSDK()

# Check SDK status at startup
@app.on_event("startup")
async def startup_event():
    if sdk.get_current_state() != OneAgentSDK.State.ACTIVE:
        print("Dynatrace OneAgent SDK not active!")
    else:
        print("Dynatrace OneAgent SDK is active")

# Middleware to trace all incoming requests
@app.middleware("http")
async def add_dynatrace_trace(request: Request, call_next):
    with sdk.trace_incoming_web_request(
        url=str(request.url),
        method=request.method,
        remote_host=request.client.host if request.client else "unknown",
        remote_port=request.client.port if request.client else 0,
        headers=dict(request.headers)
    ) as tracer:
        tracer.start()
        
        # Add the tracer to the request state for use in endpoints
        request.state.dynatrace_tracer = tracer
        
        try:
            response = await call_next(request)
            tracer.set_status_code(response.status_code)
            return response
        except Exception as e:
            tracer.error(str(e))
            raise
        finally:
            tracer.end()

# Example endpoint with custom tracing
@app.get("/items/{item_id}")
async def read_item(item_id: int, request: Request):
    # Example of custom tracing within an endpoint
    with sdk.trace_custom_service("Item Processing", "ItemService"):
        # Simulate some processing time
        time.sleep(0.1)
        
        # You can access the tracer from the request if needed
        # request.state.dynatrace_tracer.add_parameter("item_id", str(item_id))
        
        return {"item_id": item_id}

# Health check endpoint (untraced)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}