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
    wappinfo = sdk.create_web_application_info(virtual_host='plus-demo.com',application_id='PlusApplication',context_root='/lane-one/')
    with wappinfo:
        wreq = sdk.trace_incoming_web_request(
            wappinfo,
            'http://plus-demo.com/lane-one/',
            'GET',
            headers={'Host': 'plus-demo.com'},
            remote_address='127.0.0.1:12345')

    with wreq:
        wreq.add_parameter('my_form_field', '1234')
        # Process web request
        wreq.add_response_headers({'Content-Length': '1234'})
        wreq.set_status_code(200) # OK

        url = 'http://plus-demo.com/lane-one/RFID'
        headers = {
            'header1': '1234',
            'header2': '5678'
        }
        # Use requests library for making HTTP requests
        tracer = sdk.trace_outgoing_web_request(url, 'GET', headers)

        with tracer:
            # Get and set the Dynatrace tag
            tag = tracer.outgoing_dynatrace_string_tag
            headers['X-Dynatrace'] = tag
            response = requests.get(url, headers=headers)

