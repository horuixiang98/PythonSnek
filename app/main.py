from fastapi import FastAPI
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List
import platform
import oneagent
import oneagent.sdk as onesdk # All other SDK functions.
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
    sdk = oneagent.get_sdk()
    wappinfo = sdk.create_web_application_info(
        virtual_host='example.com', # Logical name of the host server.
        application_id='MyWebApplication', # Unique web application ID.
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
            return wreq

# async def testTrace():
#     try :
#         incall = getsdk().trace_incoming_remote_call(
#             'dummyPyMethod', 'DummyPyService',
#             'dupypr://localhost/dummyEndpoint',
#             protocol_name='DUMMY_PY_PROTOCOL', str_tag=strtag)
#         with incall:
#             result = 0
#             for i in range(1000):
#                 result += (i ** 2) * (math.sin(i) + math.cos(i))
#             # Simulate heavy processing with sleep
#                 await asyncio.sleep(2)
#                 return result
#     except Exception as e:
#         return e
    
