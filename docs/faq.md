# Frequently Asked Questions

## General gRPC questions

### Can I use gRPC with languages other than C++ and Python?
gRPC supports many programming languages, including C++, Python, Go, C#, and more. The gRPC tools can generate client and server code for these languages.

!!! info ""
    See: https://grpc.io/docs/languages/

### How do I create a gRPC client?
To create a gRPC client, you typically need to generate client code using the gRPC tools from your service definition file (.proto). Then, you can use the generated client classes to make RPC calls to the server.

#### Where are the protobufs located?
The proto files for each service in EosSdkRpc are located either at this github link, or in the /usr/share/EosSdkRpc/proto directory on an Arista EOS device.

#### How to generate source files for a given language from the proto files?
C++: see the [simple c++ client](/guides/howto/#simple-c-client/) section of the HOWTO guide

Python:
If you haven't already, you need to install the Protocol Buffers compiler (protoc). You can download precompiled binaries from the official repository: https://github.com/protocolbuffers/protobuf/releases

You'll also need the grpcio-tools package to generate gRPC code for Python. You can install it using pip:
```
pip install grpcio-tools
```

Use the protoc compiler and the python_out option to generate Python code from your .proto file:
```
protoc -I /path/to/protobufs --python_out=/path/to/output_dir /path/to/protobufs/example.proto
```
Replace /path/to/protobufs with the actual path to the directory containing your .proto file, and replace /path/to/output_dir with the directory where you want the Python code to be generated.

### How many clients are able to connect to a single transport?
There is no maximum number of clients for a gRPC server; it's a dynamic and context-dependent parameter that should be determined on a case by case basis due to hardware and performance constraints.

However, as with most gRPC servers EosSdkRpc allows a max of 100 concurrent streams by default. A gRPC channel uses one HTTP/2 connection, and all concurrent calls are multiplexed on that single connection. If the amount of active calls hits the connection stream limit, any additional calls made will be added to a queue in the client. These calls in the queue must wait for other active calls to complete before they are sent.

!!! info ""
    See: https://grpc.io/docs/guides/performance/

### What is the maximum message size?
The max message size in gRPC is limited to 4MB by default. This can be increased by setting the following client channel options:
- grpc.max_send_message_length
- Grpc.max_receive_message_length

This should only be required in very specific cases, e.g making a show command request with the EapiService and the returned content is extremely large.

### How can I handle timeouts and deadlines in gRPC clients?
You can set timeouts and deadlines when making RPC calls using gRPC. This helps ensure that calls do not hang indefinitely and fail gracefully when expected responses are not received within the specified time.

Python Example:

!!! note "Python example"
    Use the optional timeout parameter, which sets duration of time in seconds to allow for the RPC.
    ```python
    my_timeout_in_seconds = 10
    self.grpc_client.fooRpc( fooRpcRequestMessage, timeout=my_timeout_in_seconds)
    ```

### How do I handle errors in gRPC clients?
gRPC uses status codes to indicate the outcome of an RPC call. The returned grpc::Status object should be checked to determine the status of the call and handle errors accordingly.

!!! info
    Sample mapping of EOS SDK errors to gRPC errors can be found in our [HOWTO guide](/guides/howto/#error-handling/)

#### Common Errors:

| gRPC Status             | description                               |
|-------------------------|-------------------------------------------|
| GRPC_STATUS_CANCELLED   | The request was cancelled
| GRPC_STATUS_DEADLINE_EXCEEDED | The request deadline expired before the server returned a response
| GRPC_STATUS_UNIMPLEMENTED | The RPC has not been implemented on the server side. This could be because the service has not been enabled via the EosSdkRpc transport service configuration command: `service <list of services to enable> | all` |
| GRPC_STATUS_UNAVAILABLE | This status code usually indicates the client is unable to form a successful connection to the server. This can be caused by many issues depending on the language used by the client. Common causes are the gRPC server not running, ACL rules blocking the IP/port, certificate issues, attempting to connect to a different server. |
| GRPC_STATUS_UNKNOWN | Server may have thrown an exception |

!!! info
    See: [official gRPC website](https://grpc.github.io/grpc/core/md_doc_statuscodes.html) for further information.

#### Other:

##### RPC inactive/failed to connect to address
  Please ensure the Arista device has the correct access control in place to permit traffic on the port used to configure the given EosSdkRpc transport. The default EosSdkRpc port is not blocked by default and must be explicitly enabled for remote clients connecting over an interface.

!!! info ""
    See see the [exposing the RPC port](/guides/howto/#exposing-the-rpc-port/) section of the HOWTO guide.

##### No match found for server name: <dns name>
If an SSL profile is in use and there is a mismatch between the common name (or SAN) of the certificate and the device the following trace will appear in the logs (/var/log/agents/EosSdkRpcAgent-<agent name> ):

```
E0223 09:47:05.375500672   30883 ssl_transport_security.cc:1839] No match found for server name: <dns name>
```

Ensure the certificate used by the device has the dns name or IP address used to connect by the client present in the CN or SAN field.

##### Peer did not return a certificate.
If the transport is enabled with mTLS config ( `trust certificate <certificate>` configuration present in the configured SSL profile ) and the client does not provide a valid certificate, a similar trace to the following will appear in the logs:

```
E0223 09:53:34.288937269   32483 ssl_transport_security.cc:1469] Handshake failed with fatal error SSL_ERROR_SSL: error:140890C7:SSL routines:ssl3_get_client_certificate:peer did not return a certificate.
```

!!! note
    A client certificate may also be validated against a trusted certificate manually using the following openssl command:
    ```
    $ openssl verify -verbose -CAfile ca.crt client.crt
    client.crt: OK
    ```

##### RSA_padding_check_PKCS1_type_1:block type is not 01
If the certificate presented to the server by the client are not signed by a trusted CA, a trace similar to the following may appear in the logs:

```
E0223 09:59:07.960911143   32483 ssl_transport_security.cc:1469] Handshake failed with fatal error SSL_ERROR_SSL: error:0407006A:rsa routines:RSA_padding_check_PKCS1_type_1:block type is not 01.
```

## Questions specific to EosSdkRpc

### How can I secure gRPC communication?
gRPC supports various security mechanisms, including Transport Layer Security (TLS) for securing communication between clients and servers. You can configure security options when setting up the server and client by first configuring an SSL profile within EOS:

Mutual TLS example:
```
hostname(config)#
hostname(config)#management security
hostname(config-mgmt-security)#ssl profile myprofile
hostname(config-mgmt-sec-ssl-profile-myprofile)#certificate server.pem key server.key
hostname(config-mgmt-sec-ssl-profile-myprofile)#trust certificate ca.pem
```

Once the SSL profile is configured and valid (verify using `show management security ssl profile`), the ssl profile may then be referenced in the EosSdkRpc transport configuration:

```
hostname(config)#
hostname(config)#management api eos-sdk-rpc
hostname(config-mgmt-api-eos-sdk-rpc)#transport grpc foo
hostname(config-mgmt-api-eos-sdk-rpc-foo)#ssl profile myprofile
```

The client should then use the equivalent of a secure channel in your desired language, passing a valid client key and certificate, and also in the case of mTLS, the CA of the server certificate.

!!! info ""
    Certificates should be in PEM format and certificate chains are also supported.

Optional AAA authentication may also be enabled via the following configuration:
```
hostname(config-mgmt-api-eos-sdk-rpc-foo)#metadata username authentication channel secure  
```
In this case, the client must send a valid username and password to the server via the metadata of the RPC request. 

!!! note "Python"
    Example for setting the username/password for each RPC request made on the given channel:
    ```python
	class AuthenticationCallCredentials( grpc.AuthMetadataPlugin ):
	def __init__( self, credentials ):
	  self.creds = credentials

	def __call__( self, context, callback ):
	  callback( self.creds, None )

	tlsCredentials = grpc.ssl_channel_credentials( certsAsString )
	callCredentials = grpc.metadata_call_credentials(
		     AuthenticationCallCredentials(
			(
			   ( 'username', f'{username}' ),
			   ( 'password', f'{password}' ),
			)
		     ) )
	compositeCredentials = grpc.composite_channel_credentials(
		  tlsCredentials, authCredentials )
	self.channel = grpc.secure_channel( address, compositeCredentials )
    ```

## Troubleshooting EosSdkRpc

### Where are EosSdkRpc logs located?
The logs for EosSdkRpc transports are located in /var/log/agents directory, the naming format for each transport will be
`EosSdkRpcAgent-<transport name>-<process id>`

e.g `EosSdkRpcAgent-foo-12345`

### How to enable more verbose EosSdkRpc gRPC logging:
All C core library based gRPC implementations have built in support for both of the `GRPC_VERBOSITY` and `GRPC_TRACE` environment variables. These can be used to enable more verbose logging from within GRPC for both the EosSdkRpc transport and the client. 

!!! info ""
    Other gRPC environment variables may be found at the official [gRPC github](https://github.com/grpc/grpc/blob/master/doc/environment_variables.md)

####Server-side

Set the environment variable for the transport named `foo` ( agent name: `EosSdkRpcAgent-foo` ):
```
hostname(config)#
hostname(config)#agent EosSdkRpcAgent-foo environ GRPC_VERBOSITY=DEBUG
```

The agent must be restarted for the environment variable to take effect:
```
hostname(config)#
hostname(config)#man api eos-sdk-rpc
hostname(config-mgmt-api-eos-sdk-rpc)#transport grpc foo
hostname(config-eos-sdk-rpc-transport-default)#disabled
hostname(config-eos-sdk-rpc-transport-default)#no disabled
This is an EosSdk application
Full agent name is 'EosSdkRpcAgent-foo
```

More verbose logging should now be present in: `/var/log/agents/EosSdkRpcAgent-foo-<pid>`

#### Client-side

Examples:
!!! info "Python:"
    GRPC_VERBOSITY=debug python Client.py

!!! info "Dotnet:"
    GRPC_VERBOSITY=debug dotnet run

### How to verify the EosSdkRpc process is running?

!!! info "bash and pgrep"
    hostname(config)#bash pgrep EosSdkRpc | xargs ps
    PID TTY      STAT   TIME COMMAND
    26963 ?        Sl     0:07 EosSdkRpc-RPC

or

!!! info
    sh daemon
    Agent: RPC (running with PID 26963)
    Uptime: 0:00:39 (Start time: Thu Feb 23 09:25:10 2023)
    No configuration options stored.

    No status data stored.

### How to verify the EosSdkRpc is actively listening on the configured addresses?

!!! info ""
    using netstat and grep:
    ```
    hostname(config)#bash sudo netstat -ptnl | grep 9543
    tcp6       0      0 :::9543                 :::*                    LISTEN      26963/EosSdkRpc-RPC
    ```
    `-x` for unix socket
    `-t` for tcp

### How to verify the port is being forwarded in the configured ACLs?

Use the `show run | sec <port>` command to easily parse the running config for any custom access-list.
```
hostname(config)#show run | sec 9543
ip access-list rpc
   300 permit tcp any any eq 9543
```

Verify the correct access-list is in use:
```
#show run | sec system control-plane
system control-plane
   ip access-group rpc in
```

