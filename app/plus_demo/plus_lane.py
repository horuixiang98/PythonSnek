from fastapi import FastAPI, Request
import oneagent
import oneagent.sdk as onesdk # All other SDK functions
from oneagent.common import MessagingDestinationType
import time
import threading
import requests

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


@app.get("/plus_lane_one")
def mock_outgoing_web_request(request: Request):
    sdk = getsdk()
    wappinfo = sdk.create_web_application_info(virtual_host='plus-demo.com',application_id='PlusApplication',context_root='/plus_lane_one/')
    with wappinfo:
        wreq = sdk.trace_incoming_web_request(
            wappinfo,
            'http://plus-demo.com/plus_lane_one/',
            'GET',
            headers={'Host': 'plus-demo.com'},
            remote_address='127.0.0.1:12345')

    with wreq:
        wreq.add_parameter('my_form_field', '1234')
        # Process web request
        wreq.add_response_headers({'Content-Length': '1234'})
        wreq.set_status_code(200) # OK

        tracer = sdk.trace_outgoing_web_request('http://plus-demo.com/plus_lane_one/RFID', 'GET',
                                            headers={'X-not-a-useful-header': 'python-was-here'})

    with tracer:
        # Now get the outgoing dynatrace tag. You have to add this tag as request header to your
        # request if you want that the path is continued on the receiving site. Use the constant
        # oneagent.common.DYNATRACE_HTTP_HEADER_NAME as request header name.
        tag = tracer.outgoing_dynatrace_string_tag
        print('Outgoing dynatrace tag:', str(tag))

        # As soon as the response is received, you can add the response headers to the
        # tracer and you shouldn't forget to set the status code, too.
        tracer.add_response_headers({'Content-Length': '1234'})
        tracer.set_status_code(200) # OK
        # outgoing_remote_call(success=True)
        # outgoing_remote_call(success=True)
        # outgoing_remote_call(success=False)