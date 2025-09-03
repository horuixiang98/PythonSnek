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
        dbinfo = sdk.create_database_info(
            'CheckCarPlate', oneagent.sdk.DatabaseVendor.SQLSERVER,
            oneagent.sdk.Channel(oneagent.sdk.ChannelType.TCP_IP, '127.0.0.1:6666'))
        with sdk.trace_sql_database_request(dbinfo, 'SELECT JGP9898 FROM CarPlate;') as tracer:
            # Do actual DB request
            tracer.set_rows_returned(42) # Optional
            tracer.set_round_trip_count(3) # Optional 
        call = getsdk().trace_outgoing_remote_call(
            'ScannerPyMethod', 'ScannerPyService', 'dupypr://plus-demo.com/ScannerEndpoint',
            onesdk.Channel(onesdk.ChannelType.IN_PROCESS, 'plus-demo.com'),
            protocol_name='Scanner_PY_PROTOCOL')
        with call:
                # Note that this property can only be accessed after starting the
                # tracer. See the documentation on tagging for more information.
                strtag = call.outgoing_dynatrace_string_tag
                do_remote_call_thread_func(strtag, True)
                # deductCredit = sdk.trace_incoming_remote_call(
                #     'deductCreditMethod', 'deductCreditServiceName', 'rmi://plus-demo.com/ScannerEndpoint/deductCredit',
                #     protocol_name='RMI/custom',
                #     str_tag=strtag)
                # with deductCredit:
                #     do_remote_call_thread_func(strtag, True)
                #     pass # Here you would do the actual work that is timed


def do_remote_call_thread_func(strtag, success):
    try:
        print('+thread')
        # We use positional arguments to specify required values and named
        # arguments to specify optional values.
        incall = getsdk().trace_incoming_remote_call(
            'dummyPyMethod', 'DummyPyService',
            'dupypr://localhost/dummyEndpoint',
            protocol_name='DUMMY_PY_PROTOCOL', str_tag=strtag)
        with incall:
            if not success:
                raise RuntimeError('Remote call failed on the server side.')
            dbinfo = getsdk().create_database_info(
                'Northwind', onesdk.DatabaseVendor.SQLSERVER,
                onesdk.Channel(onesdk.ChannelType.TCP_IP, '10.0.0.42:6666'))

            # This with-block will automatically free the database info handle
            # at the end. Note that the handle is used for multiple tracers. In
            # general, it is recommended to reuse database (and web application)
            # info handles as often as possible (for efficiency reasons).
            with dbinfo:
                traced_db_operation(
                    dbinfo, "BEGIN TRAN;")
                traced_db_operation(
                    dbinfo,
                    "SELECT TOP 1 qux FROM baz ORDER BY quux;")
                traced_db_operation(
                    dbinfo,
                    "SELECT foo, bar FROM baz WHERE qux = 23")
                traced_db_operation(
                    dbinfo,
                    "UPDATE baz SET foo = foo + 1 WHERE qux = 23;")
                traced_db_operation(dbinfo, "COMMIT;")
        print('-thread')
    except Exception as e:
        failed[0] = e
        raise