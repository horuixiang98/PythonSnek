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


@app.get("/master")
def mock_outgoing_web_request(request: Request):
    sdk = getsdk()

    # Create tracer and and request headers.
    tracer = sdk.trace_outgoing_web_request('https://isatec.com/master', 'GET',
                                            headers={'X-not-a-useful-header': 'python-was-here'})

    with tracer:
        # Now get the outgoing dynatrace tag. You have to add this tag as request header to your
        # request if you want that the path is continued on the receiving site. Use the constant
        # oneagent.common.DYNATRACE_HTTP_HEADER_NAME as request header name.
        tag = tracer.outgoing_dynatrace_string_tag
        print('Outgoing dynatrace tag:', str(tag))

        # # Here you process and send your web request.
        # _process_my_outgoing_request(tag)

        # # As soon as the response is received, you can add the response headers to the
        # # tracer and you shouldn't forget to set the status code, too.
        # tracer.add_response_headers({'Content-Length': '1234'})
        # tracer.set_status_code(200) # OK
        # outgoing_remote_call(success=True)
        # outgoing_remote_call(success=True)
        # outgoing_remote_call(success=False)
        try:
            link = sdk.create_in_process_link()
            response = requests.post('http://localhost:8000/appUserService', params={'strtag': tag})
            if response.status_code == 200:
                print("Successfully called appUserService")
            else:
                print(f"Failed to call appUserService: {response.status_code}")
            
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
        # mock_incoming_web_request(link)