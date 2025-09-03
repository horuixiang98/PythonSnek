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
        
        call = getsdk().trace_outgoing_remote_call(
            'ScannerPyMethod', 'ScannerPyService', 'dupypr://plus-demo.com/ScannerEndpoint',
            onesdk.Channel(onesdk.ChannelType.IN_PROCESS, 'plus-demo.com'),
            protocol_name='Scanner_PY_PROTOCOL')
        with call:
            dbinfo = sdk.create_database_info(
                'CheckCarPlate', oneagent.sdk.DatabaseVendor.SQLSERVER,
                oneagent.sdk.Channel(oneagent.sdk.ChannelType.TCP_IP, '127.0.0.1:6666'))
            with sdk.trace_sql_database_request(dbinfo, 'SELECT JGP9898 FROM CarPlate;') as tracer:
                # Do actual DB request
                tracer.set_rows_returned(42) # Optional
                tracer.set_round_trip_count(3) # Optional 
                # Note that this property can only be accessed after starting the
                # tracer. See the documentation on tagging for more information.
                strtag = call.outgoing_dynatrace_string_tag
                deductCredit = sdk.trace_incoming_remote_call(
                    'deductCreditMethod', 'deductCreditServiceName', 'rmi://plus-demo.com/ScannerEndpoint/deductCredit',
                    protocol_name='RMI/custom',
                    str_tag=strtag)
                with deductCredit:
                    pass # Here you would do the actual work that is timed
