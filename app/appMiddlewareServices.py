from fastapi import FastAPI, Request, Form
import oneagent
import oneagent.sdk as onesdk # All other SDK functions
from oneagent.common import MessagingDestinationType
import time
import threading
from typing import Annotated
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


@app.post("/appMiddlewareService")
def app_middleware_service(request: Request):
    sdk = getsdk()
    # Get query parameters
    # headers = dict(request.headers)
    params = dict(request.query_params)
    print('Strtag parameter:', params.get('strtag'))
    method = '/GetMiddlewareMethod'
    service = 'GetMiddlewareService'
    endpoint = 'dupypr://localhost/getMiddlewareEndpoint'
    protocol = 'Middleware_PY_PROTOCOL'
    call = getsdk().trace_outgoing_remote_call(
        method, service, endpoint,
        onesdk.Channel(onesdk.ChannelType.IN_PROCESS, 'localhost'),
        protocol_name=protocol)
    try:
        response = requests.post('http://localhost:8002/appCategoryService', params={'strtag': tag})
        if response.status_code == 200:
            print("Successfully called appCategoryService")
        else:
            print(f"Failed to call appCategoryService: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
    # try:
        
    #     link = sdk.create_in_process_link()
    #     with sdk.trace_in_process_link(link):
    #         do_remote_call(method,service,endpoint,protocol, params.get('strtag'), True)
    #         print('AppMiddlewareService Executed')

    # except RuntimeError: # Swallow the exception raised above.
    #     pass
    return {'message': 'AppMiddlewareService Executed'}

def do_remote_call(method, service, endpoint, protocol, strtag, success):
    # This function simulates doing a remote call by calling a function
    # do_remote_call_thread_func in another thread, passing a string tag. See
    # the documentation on tagging for more information.
    workerthread = threading.Thread(
        target=do_remote_call_thread_func,
        args=(method, service, endpoint, protocol, strtag, success))
    workerthread.start()
    # Note that we need to join the thread, as all tagging assumes synchronous
    # calls.
    workerthread.join()

def traced_db_operation(dbinfo, sql):
    print('+db', dbinfo, sql)
    with getsdk().trace_sql_database_request(dbinfo, sql) as tracer:
        tracer.set_round_trip_count(3)
    print('-db', dbinfo, sql)

def do_remote_call_thread_func(method, service, endpoint, protocol, strtag, success):
    try:
        print('+thread')
        # We use positional arguments to specify required values and named
        # arguments to specify optional values.
        incall = getsdk().trace_incoming_remote_call(
            method, service,
            endpoint,
            protocol_name=protocol, str_tag=strtag)
        with incall:
            if not success:
                raise RuntimeError('Remote call failed on the server side.')
            dbinfo = getsdk().create_database_info(
                'MiddlewareQuery', onesdk.DatabaseVendor.SQLSERVER,
                onesdk.Channel(onesdk.ChannelType.TCP_IP, '10.0.0.42:6666'))
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