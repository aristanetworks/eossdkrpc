# Security Configuration

## ACL rules
Currently, the default port for EosSdkRpc (port: 9543) is not permitted by the default control-plane ACL. The port must be explicitly permitted to allow remote access.

!!! info ""
    See see the [exposing the RPC port](/guides/aclrules/).

## Remote clients
Transports must be configured with an SSL profile for remote clients to successfully issue an RPC request to EosSdkRpc. In an insecure (non-TLS/mTLS) remote client attempts to execute an RPC they will be met with an unauthenticated grpc::Status.

## TLS and mutual TLS 
!!! info ""
    Supported since 4.29.2F release.

gRPC supports various security mechanisms, including Transport Layer Security (TLS) for securing communication between clients and servers. You can configure security options when setting up the server and client by first configuring an SSL profile within EOS:

### EOS SSL profile configuration
#### TLS 
With TLS only the client verifies the server using the server certificate and trusted certificate (CA cert).
```
hostname(config)#
hostname(config)#management security
hostname(config-mgmt-security)#ssl profile myprofile
hostname(config-mgmt-sec-ssl-profile-myprofile)#certificate server.pem key server.key
```

#### Mutual TLS
With mutual TLS (mTLS) both the client and server verify eachother using trusted certificates (CA certs) and hence must both provide their own certificates.
```
hostname(config)#
hostname(config)#management security
hostname(config-mgmt-security)#ssl profile myprofile
hostname(config-mgmt-sec-ssl-profile-myprofile)#certificate server.pem key server.key
hostname(config-mgmt-sec-ssl-profile-myprofile)#trust certificate ca.pem
```

!!! info ""
    Certificates should be in PEM format and certificate chains are also supported.

Ensure the SSL profile is valid:

Ensure the configured ssl profile is valid (in this case `myprofile`). The server will fail to start if the configured ssl profile is considered invalid:
```
hostname(config)#show mananagement security ssl profile
   Profile                      State
---------------------------- -----------
   myprofile                    valid
```

### EosSdkRpc SSL profile configuration
Once the SSL profile is configured and valid, the ssl profile may then be referenced in the EosSdkRpc transport configuration:
```
hostname(config)#
hostname(config)#management api eos-sdk-rpc
hostname(config-mgmt-api-eos-sdk-rpc)#transport grpc foo
hostname(config-mgmt-api-eos-sdk-rpc-foo)#ssl profile myprofile
```

!!! note ""
    If listening on multiple endpoints each endpoint address must exist as a SAN entry in the certificate.
    
    - `<interface IP>` for local interface
    - `localhost` for localhost unix-socket
    - `127.0.0.1` for localhost loopback

The client should then use the equivalent of a secure channel in your desired language, passing a valid client key and certificate, and also in the case of mTLS, the CA of the server certificate.

### Optional AAA authentication may also be enabled via the following configuration:
```
hostname(config)#
hostname(config)#management api eos-sdk-rpc
hostname(config-mgmt-api-eos-sdk-rpc)#transport grpc foo
hostname(config-mgmt-api-eos-sdk-rpc-foo)#metadata username authentication channel secure  
```

!!! note ""
    AAA authentication is currently only available for transports configured with an SSL profile.

When enabled, this feature requires the client to include a valid username and password in the metadata of the RPC call. 

- The username should be stored as a key-value pair with string “username” as the key and the user's username as the value.
- The password should be stored as a key-value pair with string “password” as the key and the user's password as the value.

#### AAA authentication failure
If user authentication fails for a given RPC call, an error message is returned to the client.
Example error message:
```
grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
        status = StatusCode.UNAUTHENTICATED
        details = "Username and password authentication failed."
        …
```


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
