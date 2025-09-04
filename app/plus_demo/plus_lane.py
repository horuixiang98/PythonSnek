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

class TraceObject:
    def __init__(self, method: str, service: str, endpoint: str, protocol: str):
        self.Method = method
        self.Service = service
        self.Endpoint = endpoint
        self.Protocol = protocol

# Check SDK status at startup
@app.on_event("startup")
async def startup_event():
    init_result = oneagent.initialize()
    print('OneAgent SDK initialization result' + repr(init_result))
    with sdk.trace_custom_service('PythonSnekApp', 'PythonSnekService'):
        print('Application initialized')

##################################### API #######################################
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

        # Check CarPlate in DB
        traceCarPlateInfo = TraceObject('ScannerPyMethod', 'ScannerPyService', 'dupypr://plus-demo.com/ScannerEndpoint', 'Scanner_PY_PROTOCOL')
        traceCarPlateTag = trace_outgoing_remote_call_func(traceCarPlateInfo)
        with traceCarPlateTag:
            do_incoming_remote_call(traceCarPlateTag, success=True, trace_obj=traceCarPlateInfo)
        # dbinfoCheckCarPlate = sdk.create_database_info(
        #     'CheckCarPlate', oneagent.sdk.DatabaseVendor.SQLSERVER,
        #     oneagent.sdk.Channel(oneagent.sdk.ChannelType.TCP_IP, '127.0.0.1:6666'))
        # with sdk.trace_sql_database_request(dbinfoCheckCarPlate, 'SELECT JGP9898 FROM CarPlate;') as tracer:
        # Do actual DB request
        # tracer.set_rows_returned(42) # Optional
        # tracer.set_round_trip_count(3) # Optional 
        # with tracer:
        traceInfo = TraceObject('ScannerPyMethod', 'ScannerPyService', 'dupypr://plus-demo.com/ScannerEndpoint', 'Scanner_PY_PROTOCOL')
        traceTag = trace_outgoing_remote_call_func(traceInfo)
        with traceTag:
            traceInfo = TraceObject('deductCreditMethod', 'deductCreditService', 'dupypr://plus-demo.com/ScannerEndpoint', 'RMI/custom')
            do_incoming_remote_call(traceTag, success=True, trace_obj=traceInfo)


##################################### Functions #######################################
def trace_outgoing_remote_call_func(trace_obj: TraceObject):
    call = getsdk().trace_outgoing_remote_call(
                    trace_obj.Method, trace_obj.Service, trace_obj.Endpoint,
                    onesdk.Channel(onesdk.ChannelType.IN_PROCESS, trace_obj.Endpoint),
                    protocol_name=trace_obj.Protocol)
    with call:
            strtag = call.outgoing_dynatrace_string_tag
            return strtag

def trace_incoming_remote_call_func(strtag, success, trace_obj: TraceObject):
    incall = getsdk().trace_incoming_remote_call(
            trace_obj.Method, trace_obj.Service,
            trace_obj.Endpoint,
            protocol_name=trace_obj.Protocol, str_tag=strtag)

    with incall:
        if not success:
            raise RuntimeError('Remote call failed on the server side.')
        return incall



def traced_db_operation(dbinfo, sql):

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


def do_incoming_remote_call(strtag, success, trace_obj: TraceObject):
    workerthread = threading.Thread(
        target=do_remote_call_thread_func,
        args=(strtag, success, trace_obj))
    workerthread.start()
    # Note that we need to join the thread, as all tagging assumes synchronous
    # calls.
    workerthread.join()

def do_remote_call_thread_func(strtag, success, trace_obj: TraceObject):
    try:
        incall = trace_incoming_remote_call_func(strtag, success, trace_obj)
        with incall:
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