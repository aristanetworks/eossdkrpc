# Basic configuration

!!! info ""
    This is the recommended method of configuring EosSdkRpc starting from 4.29 release.

The new EosSdkRpc CLI is built on top of the existing daemon CLI and allows the configuration of:

- Listening interface + port (default port is 9543)
- RPC services to enable (default is none)
- Enable/disable the server instance
- Multiple EosSdkRpc agents

All EosSdkRpc configuration commands reside under the eos-sdk-rpc management mode. Multiple gRPC servers are supported and each EosSdkRpc gRPC server is defined using the transport command:

```
hostname#config
hostname(config)#management api eos-sdk-rpc
hostname(config-mgmt-api-gnmi)#transport grpc foo
```

## Configure listening endpoints:

Supported since 4.29.0 release:

- Local interface

Supported since 4.30.2 release:

- Localhost loopback
- Localhost unix-socket

!!! info ""
    Support for configuring multiple endpoints per transport is restricted to only one of each type.
    
    e.g configuring two localhost unix-sockets is not supported.

### Listening interface
```
hostname(config-mgmt-api-eos-sdk-rpc-foo)#[no] local interface Management1
```

#### Optionally configure the listening port (the default port is 9543):
```
hostname(config-mgmt-api-eos-sdk-rpc-foo)#[no] local interface Management1 port 9543
```



!!! note 
    - The provided interface must be configured with an active IP address for the server to start, as this is the address that the underlying gRPC server binds to. 
    - The configured VRF for that interface is also the VRF that the server listens in.
    - For remote access, the listening port (default 9543, or otherwise) must also be allowed in the system control-plane ACL (for that VRF). See: [Exposing the RPC port](/guides/aclrules/).
    - Each transport should be configured with a unique interface/port combination.
 
### Localhost loopback address
!!! info ""
    Supported since 4.30.2 release.

```
hostname(config-mgmt-api-eos-sdk-rpc-foo)#[no] localhost loopback
```

#### Optionally configure the listening port (the default port is 9543):
```
hostname(config-mgmt-api-eos-sdk-rpc-foo)#[no] localhost loopback port 9543
```

#### Optionally configure the listening VRF:
```
hostname(config-mgmt-api-eos-sdk-rpc-foo)#[no] localhost loopback port 9543 vrf foo
```

!!! note
    - Only one VRF is supported per transport. If a local interface endpoint is also configured and the local interface VRF configuration conflicts with the VRF configured for the localhost loopback endpoint, the local interface VRF will be preferred and the loopback endpoint will be disabled.

### Localhost unix-socket
!!! info ""
    Supported since 4.30.2 release.

```
hostname(config-mgmt-api-eos-sdk-rpc-foo)#[no] localhost unix file:/tmp/foo.sock
```

!!! note
    - A client may connect to the unix-domain socket path by using unix://<path> e.g unix:///tmp/foo.sock
    - Ensure the correct file permissions are in place for the user attempting to connect to the unix-domain socket

## Enable all supported services:
```
hostname(config-mgmt-api-eos-sdk-rpc-foo)#[no] service all
```

!!! note
    - If all services are configured, this takes precedence over any given list of supported services.

## Enable an explicit list of supported services:
```
hostname(config-mgmt-api-eos-sdk-rpc-foo)#[no] service eapiservice agentservice macsecservice
```

## Enable/disable the transport:
```
hostname(config-mgmt-api-eos-sdk-rpc-foo)#[no] disabled
```

#### Multiple transport example

Configuring a different list of services for each transport. `foo` is running on the default port (9543) and `bar` is running on port 9544. Both transports have been bound to the same ip address configured for the *Management1* interface.

```
management api eos-sdk-rpc
  transport grpc foo
         local interface Management1
         service AgentService EapiService
         no disabled

  transport grpc bar
         local interface Management1 port 9544
         service AgentService BgpPathService
         no disabled
```

!!! note 
    At present there should be no conflicts when running the same services across multiple transports, however, there may be limitations for future services - these will be documented.

## Supported modules

The proto files can be found in the directory `/usr/share/EosSdkRpc/proto/` on the EOS device. Current Supported modules are:

- Agent: allows a client to monitor and query option values (these are set with the option … value CLI command) or set status in the agent’s registry on SysDb. EosSdkRpc does not use any kind of record on SysDb. This space is entirely at the client’s discretion.
- EAPI: allows a client to run CLI commands. Show commands and config commands are supported. Show commands are returned in JSON format.
- Intf: allows a client to monitor interfaces as they are added or removed. Provides functionality to change an interface’s description or administrative status.
- IP-intf: allow a client to monitor, query, remove or add IP addresses to interfaces.
- IP-route: allows a client to create, delete, modify or query static routes.
- Nexthop_group: allows client to create, delete, modify and query nexthop groups.

Each module is organized in the following manner. All RPC proto files are self documented just like the original SDK header counterparts. Whenever generating code for a module, its included dependencies must be explicitly specified too. The table below that lists the required protobufs for each RPC module.

| Module               | Required protobufs                                                                                                |
|----------------------|-------------------------------------------------------------------------------------------------------------------|
| acl.proto            | acl_types.proto, intf_types.proto, ip_intf_types.proto, rpc_types.proto                                           |
| agent.proto          | rpc_types.proto                                                                                                   |
| bgp.proto            | bgp_types.proto                                                                                                   |
| bgp_path.proto       | bgp_path_types.proto, ip_types.proto                                                                              |
| eapi.proto           | eapi_types.proto                                                                                                  |
| eth_lag_intf.proto   | eth_lag_intf_types.proto, intf_types.proto, rpc_types.proto                                                       |
| eth_phy_intf.proto   | eth_phy_intf_types.proto, intf_types.proto, rpc_types.proto                                                       |
| intf.proto           | intf_types.proto, rpc_types.proto                                                                                 |
| ip_intf.proto        | intf_types.proto, ip_intf_types.proto, rpc_types.proto                                                            |
| ip_route.proto       | intf_types.proto, ip_route_types.proto, rpc_types.proto                                                           |
| macsec.proto         | intf_types.proto, macsec_types.proto, rpc_types.proto                                                             |
| mpls_route.proto     | acl_types.proto, intf_types.proto, ip_intf_types.proto, mpls_types.proto, mpls_route_types.proto, rpc_types.proto |
| mpls_vrf_label.proto | mpls_types.proto, mpls_vrf_label_types.proto, rpc_types.proto                                                     |
| nexthop_group.proto  | nexthop_group_types.proto, intf_types.proto, mpls_types.proto, rpc_types.proto                                    |
| policy_map.proto     | acl_types.proto, intf_types.proto, ip_intf_types.proto, policy_map_types.proto, rpc_types.proto                   |

## Previous configuration
!!! info ""
    Releases up to 4.28

EosSdkRpc is built on top of EOS SDK and, therefore, needs to be configured the same way as any other agent compiled with EOS SDK: using the daemon configuration mode. The simplest form of configuration is:

```
daemon rpc
exec /usr/bin/EosSdkRpc
no shutdown
```

As mentioned earlier, the agent listens by default on localhost address so an extra argument is needed to passed on to the executable to change the listening endpoint:

```
daemon rpc
exec /usr/bin/EosSdkRpc --listen 0.0.0.0:9543
no shutdown
```

