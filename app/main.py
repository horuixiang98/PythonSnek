from fastapi import FastAPI, Request
import oneagent
import oneagent.sdk as onesdk # All other SDK functions
from oneagent.common import MessagingDestinationType
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
# @app.middleware("http")
# async def add_dynatrace_trace(request: Request, call_next):
#     init_result = oneagent.initialize()
#     print('OneAgent SDK initialization result' + repr(init_result))
#     webapp_info = sdk.create_web_application_info(
#         virtual_host=request.url.hostname,  # or your specific application name
#         application_id="PythonSnekApp",    # your application identifier
#         context_root="/"                    # base path of your application
#     )
#     with sdk.trace_incoming_web_request(
#         webapp_info=webapp_info,
#         url=str(request.url),
#         method=request.method,
#         headers=dict(request.headers)
#     ) as tracer:
#         tracer.start()
        
#         # Add the tracer to the request state for use in endpoints
#         request.state.dynatrace_tracer = tracer
        
#         try:
#             response = await call_next(request)
#             tracer.set_status_code(response.status_code)
#             return response
#         except Exception as e:
#             tracer.error(str(e))
#             raise
#         finally:
#             tracer.end()

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
def mock_incoming_web_request(request: Request):
    sdk = getsdk()
    wappinfo = sdk.create_web_application_info(
        virtual_host='snek.com', # Logical name of the host server.
        application_id='PythonSnekApp', # Unique web application ID.
        context_root='/python-web-app/') # App's prefix of the path part of the URL.

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
            url= request.url,
            method=request.method,
            headers=dict(request.headers)
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
            mock_process_incoming_message()

def mock_process_incoming_message():
    sdk = getsdk()

    # Create the messaging system info object.
    msi_handle = sdk.create_messaging_system_info(
        'MyPythonSenderVendor', 'MyPythonDestination', MessagingDestinationType.QUEUE,
        onesdk.Channel(onesdk.ChannelType.UNIX_DOMAIN_SOCKET, 'MyPythonChannelEndpoint'))

    with msi_handle:
        # Create the receive tracer for incoming messages.
        with sdk.trace_incoming_message_receive(msi_handle):
            print('here we wait for incoming messages ...')

            # Create the tracer for processing incoming messages.
            tracer = sdk.trace_incoming_message_process(msi_handle)

            # Now we can set the vendor message and correlation IDs. It's possible to set them
            # either before the tracer is started or afterwards. But they have to be set before
            # the tracer ends.
            tracer.set_vendor_message_id('message_id')
            with tracer:

                # Use tracecontext_get_current to log a trace/span ID identifiying the current node.
                tinfo = sdk.tracecontext_get_current()
                print('[!dt dt.trace_id={},dt.span_id={}] handle incoming message'.format(
                    tinfo.trace_id, tinfo.span_id))

                tracer.set_correlation_id('correlation_id')
