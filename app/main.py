from fastapi import FastAPI, Request
import oneagent
import oneagent.sdk as onesdk # All other SDK functions
from oneagent.common import MessagingDestinationType
import time
import threading

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

# Middleware to trace all incoming requests
# @app.middleware("http")
# async def add_dynatrace_trace(request: Request, call_next):
#     init_result = oneagent.initialize()
#     print('OneAgent SDK initialization result' + repr(init_result))
#     webapp_info = sdk.create_web_application_info(
#         virtual_host=request.url.hostname,  # or your specific application name
#         application_id="PythonSnekApp",    # your application identifier
#         context_root="/"                    # base path of your application
#     )
#     with sdk.trace_incoming_web_request(
#         webapp_info=webapp_info,
#         url=str(request.url),
#         method=request.method,
#         headers=dict(request.headers)
#     ) as tracer:
#         tracer.start()
        
#         # Add the tracer to the request state for use in endpoints
#         request.state.dynatrace_tracer = tracer
        
#         try:
#             response = await call_next(request)
#             tracer.set_status_code(response.status_code)
#             return response
#         except Exception as e:
#             tracer.error(str(e))
#             raise
#         finally:
#             tracer.end()

# Example endpoint with custom tracing
@app.get("/items/{item_id}")
async def read_item(item_id: int, request: Request):
    # Example of custom tracing within an endpoint
    with sdk.trace_custom_service("Item Processing", "ItemService"):
        # Simulate some processing time
        time.sleep(0.1)
        
        # You can access the tracer from the request if needed
        # request.state.dynatrace_tracer.add_parameter("item_id", str(item_id))
        
        return {"item_id": item_id}

# Health check endpoint (untraced)
@app.get("/health")
async def health_check():
    with sdk.trace_incoming_remote_call(
        method="GET",
        name="HealthCheck",
        endpoint="/health"
    ) as tracer:
        print(tracer)
        tracer.start()
        time.sleep(0.01)
        tracer.end()    
        return {"status": "healthy"}

@app.get("/mock_incoming_web_request")
def mock_incoming_web_request():
    sdk = getsdk()
    wappinfo = sdk.create_web_application_info(
        virtual_host='snek.com', # Logical name of the host server.
        application_id='PythonSnekApp', # Unique web application ID.
        context_root='/python-web-app/') # App's prefix of the path part of the URL.

    with wappinfo:
        wreq = sdk.trace_incoming_web_request(
            wappinfo,
            'http://app1.com/python-snek-app/snek?=baz',
            'GET',
            headers={'Host': 'app1.com', 'X-foo': 'bar'},
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

                tracer.set_correlation_id('1000583')



@app.get("/mock_outgoing_web_request")
def mock_outgoing_web_request():
    sdk = getsdk()

    # Create tracer and and request headers.
    tracer = sdk.trace_outgoing_web_request('http://example.com/python-snek-app/snek?=foz', 'GET',
                                            headers={'X-not-a-useful-header': 'python-was-here'})

    with tracer:
        # Now get the outgoing dynatrace tag. You have to add this tag as request header to your
        # request if you want that the path is continued on the receiving site. Use the constant
        # oneagent.common.DYNATRACE_HTTP_HEADER_NAME as request header name.
        tag = tracer.outgoing_dynatrace_string_tag

        # Here you process and send your web request.
        _process_my_outgoing_req
        uest(tag)

        # As soon as the response is received, you can add the response headers to the
        # tracer and you shouldn't forget to set the status code, too.
        tracer.add_response_headers({'Content-Length': '1234'})
        tracer.set_status_code(200) # OK
        outgoing_remote_call(success=True)
        outgoing_remote_call(success=True)
        outgoing_remote_call(success=False)

def _process_my_outgoing_request(_tag):
    pass


@app.get("/mock_incoming_outgoing_web_request")
def mock_incoming_outgoing_web_request():
    mock_incoming_web_request()
    mock_outgoing_web_request()
    mock_outgoing_message()


def mock_outgoing_message():
    sdk = getsdk()

    # Create the messaging system info object.
    msi_handle = sdk.create_messaging_system_info(
        'MyPythonReceiverVendor', 'MyPythonDestination', MessagingDestinationType.TOPIC,
        onesdk.Channel(onesdk.ChannelType.TCP_IP, '10.11.12.13:1415'))

    with msi_handle:
        # Create the outgoing message tracer;
        with sdk.trace_outgoing_message(msi_handle) as tracer:
            # Set the message and correlation IDs.
            tracer.set_vendor_message_id('msgId')
            tracer.set_correlation_id('1000583')

            print('handle outgoing message')


# DB tracing example

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


def do_remote_call_thread_func(strtag, success):
    try:
        print('+thread')
        # We use positional arguments to specify required values and named
        # arguments to specify optional values.
        incall = getsdk().trace_incoming_remote_call(
            'GetUserMethod', 'GetUserService',
            'dupypr://localhost/getUserEndpoint',
            protocol_name='USER_PY_PROTOCOL', str_tag=strtag)
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

def do_remote_call(strtag, success):
    # This function simulates doing a remote call by calling a function
    # do_remote_call_thread_func in another thread, passing a string tag. See
    # the documentation on tagging for more information.

    failed[0] = None
    workerthread = threading.Thread(
        target=do_remote_call_thread_func,
        args=(strtag, success))
    workerthread.start()

    # Note that we need to join the thread, as all tagging assumes synchronous
    # calls.
    workerthread.join()

    if failed[0] is not None:
        raise failed[0] #pylint:disable=raising-bad-type


def outgoing_remote_call(success):
    print('+remote')
    # We use positional arguments to specify required values and named arguments
    # to specify optional values.
    call = getsdk().trace_outgoing_remote_call(
        'dummyPyMethod', 'DummyPyService', 'dupypr://localhost/dummyEndpoint',
        onesdk.Channel(onesdk.ChannelType.IN_PROCESS, 'localhost'),
        protocol_name='DUMMY_PY_PROTOCOL')
    try:
        with call:
            # Note that this property can only be accessed after starting the
            # tracer. See the documentation on tagging for more information.
            strtag = call.outgoing_dynatrace_string_tag
            do_remote_call(strtag, success)
    except RuntimeError: # Swallow the exception raised above.
        pass
    print('-remote')
failed = [None]

@app.get("/test_out")
def test_out():
    outcall = sdk.trace_outgoing_remote_call(
    'remoteMethodToCall', 'RemoteServiceName', 'rmi://Endpoint/service',
    oneagent.sdk.Channel(oneagent.sdk.ChannelType.TCP_IP, 'remoteHost:1234'),
    protocol_name='RMI/custom')
    with outcall:
        # Note: You can access outgoing_dynatrace_*_tag only after the trace
        # has started!
        strtag = outcall.outgoing_dynatrace_string_tag
        print('strtag' + strtag)
        test_in(strtag)
        return strtag

@app.get("/test_in")
def test_in(trace_id: str):
    incall = sdk.trace_incoming_remote_call(
    'remoteMethodToCall', 'RemoteServiceName', 'rmi://Endpoint/service',
    protocol_name='RMI/custom',
    str_tag=trace_id)
    print('test_in_strtag' + trace_id)
    return trace_id
    with incall:
        pass # Here you would do the actual work that is timed