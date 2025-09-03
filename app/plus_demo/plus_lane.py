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
        dbinfoCheckCarPlate = sdk.create_database_info(
            'CheckCarPlate', oneagent.sdk.DatabaseVendor.SQLSERVER,
            oneagent.sdk.Channel(oneagent.sdk.ChannelType.TCP_IP, '127.0.0.1:6666'))
        with sdk.trace_sql_database_request(dbinfoCheckCarPlate, 'SELECT JGP9898 FROM CarPlate;') as tracer:
            # Do actual DB request
            tracer.set_rows_returned(42) # Optional
            tracer.set_round_trip_count(3) # Optional 
            with tracer:
                call = getsdk().trace_outgoing_remote_call(
                    'ScannerPyMethod', 'ScannerPyService', 'dupypr://plus-demo.com/ScannerEndpoint',
                    onesdk.Channel(onesdk.ChannelType.IN_PROCESS, 'plus-demo.com'),
                    protocol_name='Scanner_PY_PROTOCOL')
                with call:
                        # Note that this property can only be accessed after starting the
                        # tracer. See the documentation on tagging for more information.
                        strtag = call.outgoing_dynatrace_string_tag
                        do_remote_call(strtag, success=True)


def do_remote_call_thread_func(strtag, success):
    try:
        incall = getsdk().trace_incoming_remote_call(
            'deductCreditMethod', 'deductCreditService',
            'dupypr://plus-demo.com/ScannerEndpoint',
            protocol_name='RMI/custom', str_tag=strtag)
        with incall:
            if not success:
                raise RuntimeError('Remote call failed on the server side.')
            dbinfoDeductCredit = getsdk().create_database_info(
                'deductCredit', onesdk.DatabaseVendor.SQLSERVER,
                onesdk.Channel(onesdk.ChannelType.TCP_IP, '10.0.0.42:6666'))

            with dbinfoDeductCredit:
                traced_db_operation(
                    dbinfoDeductCredit, "BEGIN TRAN;")
                traced_db_operation(
                    dbinfoDeductCredit,
                    "SELECT TOP 1 qux FROM baz ORDER BY quux;")
                traced_db_operation(
                    dbinfoDeductCredit,
                    "SELECT foo, bar FROM baz WHERE qux = 23")
                traced_db_operation(
                    dbinfoDeductCredit,
                    "UPDATE baz SET foo = foo + 1 WHERE qux = 23;")
                traced_db_operation(dbinfoDeductCredit, "COMMIT;")
    except Exception as e:
        raise

def do_remote_call(strtag, success):
    # This function simulates doing a remote call by calling a function
    # do_remote_call_thread_func in another thread, passing a string tag. See
    # the documentation on tagging for more information.
    workerthread = threading.Thread(
        target=do_remote_call_thread_func,
        args=(strtag, success))
    workerthread.start()

    # Note that we need to join the thread, as all tagging assumes synchronous
    # calls.
    workerthread.join()

def traced_db_operation(dbinfo, sql):
    print('+db', dbinfo, sql)

    # Entering the with block automatically start the tracer.
    with getsdk().trace_sql_database_request(dbinfo, sql) as tracer:

        # In real-world code, you would do the actual database operation here,
        # i.e. call the database's API.

        # Set an optional "exit"-field on the tracer. Whenever there is a
        # setter available on a tracer (as opposed to an optional parameter to a
        # trace_* function), it may be called anytime between creating and
        # ending the tracer (i.e. also after starting it).
        tracer.set_round_trip_count(3)

    print('-db', dbinfo, sql)