from fastapi import FastAPI, Request, Form
import oneagent
import oneagent.sdk as onesdk # All other SDK functions
from oneagent.common import MessagingDestinationType
import time
import threading
from typing import Annotated

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


@app.post("/mock_incoming_web_request")
def mock_incoming_web_request(request: Request):
    sdk = getsdk()
    # Get query parameters
    headers = dict(request.headers)
    params = dict(request.query_params)
    print('Link parameter:', params.get('link'))
    wappinfo = sdk.create_web_application_info(
        virtual_host='snek.com', # Logical name of the host server.
        application_id='PythonSnekApp', # Unique web application ID.
        context_root='/python-web-app/') # App's prefix of the path part of the URL.

    # with wappinfo:
    wreq = sdk.trace_incoming_web_request(
        wappinfo,
        url=str(request.url),
        method=request.method,
        headers=headers,
        str_tag=params.get('link'))
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
        mock_process_incoming_message()
        mock_process_incoming_message()

def mock_process_incoming_message():
    sdk = getsdk()

    # Create the messaging system info object.
    msi_handle = sdk.create_messaging_system_info(
        'PythonSenderVendor', 'PythonDestination', MessagingDestinationType.QUEUE,
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
