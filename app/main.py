from fastapi import FastAPI, Request
import oneagent
import oneagent.sdk as onesdk 
from oneagent.common import AgentState
import time

app = FastAPI()
sdk = oneagent.get_sdk()
getsdk = oneagent.get_sdk

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
    print('Agent_state: ', sdk.agent_state)
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

@app.get("/mock_incoming_web_request")
def mock_incoming_web_request():
    sdk = getsdk()
    wappinfo = sdk.create_web_application_info(
        virtual_host='PythonSnekApp.com', # Logical name of the host server.
        application_id='PythonSnekApp', # Unique web application ID.
        context_root='/my-web-app/') # App's prefix of the path part of the URL.

    with wappinfo:
        # This with-block will automatically free web application info handle
        # at the end. Note that the handle can be used for multiple tracers. In
        # general, it is recommended to reuse web application info handles as
        # often as possible (for efficiency reasons). For example, if you use
        # WSGI, the web application info could be stored as an attribute of the
        # application object.
        #
        # Note that different ways to specify headers, response headers and
        # parameter (form fields) not shown here also exist. Consult the
        # documentation for trace_incoming_web_request and
        # IncomingWebRequestTracer.
        wreq = sdk.trace_incoming_web_request(
            wappinfo,
            'http://example.com/my-web-app/foo?bar=baz',
            'GET',
            headers={'Host': 'example.com', 'X-foo': 'bar'},
            remote_address='127.0.0.1:12345')
        with wreq:
            wreq.add_parameter('my_form_field', '1234')
            # Process web request
            wreq.add_response_headers({'Content-Length': '1234'})
            wreq.set_status_code(200) # OK

            # Add 3 different custom attributes.
            sdk.add_custom_request_attribute('custom int attribute', 42)
            sdk.add_custom_request_attribute('custom float attribute', 1.778)
            sdk.add_custom_request_attribute('custom string attribute', 'snow is falling')

            # This call will trigger the diagnostic callback.
            sdk.add_custom_request_attribute('another key', None)

            # This call simulates incoming messages.
            # mock_process_incoming_message()