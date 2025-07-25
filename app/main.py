from fastapi import FastAPI, Request
import oneagent
from oneagent.common import AgentState
import time

app = FastAPI()
sdk = oneagent.get_sdk()

# Check SDK status at startup
@app.on_event("startup")
async def startup_event():
    init_result = oneagent.initialize()
    print('OneAgent SDK initialization result' + repr(init_result))
    with sdk.trace_custom_service('PythonSnekApp', 'PythonSnekService'):
        print('do some fancy stuff')



# Middleware to trace all incoming requests
@app.middleware("http")
async def add_dynatrace_trace(request: Request, call_next):
    init_result = oneagent.initialize()
    print('OneAgent SDK initialization result' + repr(init_result))
    webapp_info = sdk.create_web_application_info(
        virtual_host=request.url.hostname,  # or your specific application name
        application_id="PythonSnekApp",    # your application identifier
        context_root="/"                    # base path of your application
    )
    with sdk.trace_incoming_web_request(
        webapp_info=webapp_info,
        url=str(request.url),
        method=request.method,
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
    with sdk.trace_incoming_remote_call(
        method="GET",
        name="HealthCheck",
        endpoint="/health"
    ) as tracer:
        print(tracer)
        tracer.start()
        time.sleep(0.01)
        tracer.end()    
        return {"status": "healthy"}