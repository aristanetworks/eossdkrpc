# EosSdkRpc HOWTO

## Introduction

EosSdkRpc is an agent built on top of our EosSdk that uses gRPC as a mechanism to provide remote access to the SDK.

This agent is present in development versions of EOS, and is currently enabled via the "daemon" command set - starting in the 4.29 release a first-class CLI was created `management api eos-sdk-rpc` and is now the recommended configuration method. The gRPC interface that the agent supports closely matches the interface provided by EosSdk, and the intent is that the .proto interface can be publicly supported. As well as potentially allowing for remote access, using protobuf to specify the interface isolates customer code from the Linux ABI issues that come with building C++ applications on different compiler, libc, and kernel versions.

The default listen point for the agent is `localhost:9543` but this can be changed to allow external access. Only encrypted access is supported for EosSdkRpc agents configured via the `management api eos-sdk-rpc` CLI. An ACL should be used to limit the hosts that have access to the agent.

The API mirroring is intended to be modular in the same fashion as the SDK itself. Each proto file mirrors one specific SDK module and the RPC definitions and messages also aim to be as close as possible to the original SDK API call, in an attempt to make the learning gap as small as possible.

For performance reasons, “setter” RPC calls also come with bulk versions, which minimizes the RPC overhead. These calls differ from their original counterparts by providing a sequence of individual operations which are performed locally in batches, without requiring a round-trip to the client for each operation.

Multiple clients are supported by EosSdkRpc and all state is shared between these clients. Requests are fulfilled without regard to which client invoked the RPC call. Any strategy to coordinate multiple clients is out of the scope of this guide.

## Configuration

#### Releases 4.29 and greater

!!! note
    This is now the recommended method of configuring EosSdkRpc starting from 4.29 release.

The new EosSdkRpc CLI is built on top of the existing daemon CLI and allows the configuration of:

- Listening interface + port (default port is 9543)
- RPC services to enable (default is none)
- Enable/disable the server instance
- Multiple EosSdkRpc agents

```
management api eos-sdk-rpc
  transport grpc <insert server name>
         local interface <insert interface> [ port <port number> ]
         service all
         no disabled
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

!!! note 
    A daemon agent is configured by the “management api eos-sdk-rpc” CLI. This is distinguishable from other daemon agents by the use of the transport name as the agent name and  “/usr/bin/EosSdkRpcAgent” as the executeable.

#### Releases up to 4.28

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

### Exposing the RPC port

Even though the agent is listening on external addresses, we still need to grant access to the agent port with an ACL. For those who have already set up a custom ACL to the control plane, a rule needs to be added: `permit tcp <source> <dest> eq 9543` (replace `9543` with your configured port).

To set up a custom ACL for the control plane, we start by obtaining the default ACL:

```
# sh ip access-lists default-control-plane-acl
IP Access List default-control-plane-acl [readonly]
       counters per-entry
       10 permit icmp any any
       20 permit ip any any tracked [match 482 packets, 0:35:48 ago]
       30 permit udp any any eq bfd ttl eq 255
       40 permit udp any any eq bfd-echo ttl eq 254
       50 permit udp any any eq multihop-bfd micro-bfd sbfd
       60 permit udp any eq sbfd any eq sbfd-initiator
       70 permit ospf any any
       80 permit tcp any any eq ssh telnet www snmp bgp https msdp ldp netconf-ssh gnmi [match 3 packets, 0:39:06 ago]
       90 permit udp any any eq bootps bootpc snmp rip ntp ldp ptp-event ptp-general
       100 permit tcp any any eq mlag ttl eq 255
       110 permit udp any any eq mlag ttl eq 255
       120 permit vrrp any any
       130 permit ahp any any
       140 permit pim any any
       150 permit igmp any any
       160 permit tcp any any range 5900 5910
       170 permit tcp any any range 50000 50100
       180 permit udp any any range 51000 51100
       190 permit tcp any any eq 3333
       200 permit tcp any any eq nat ttl eq 255
       210 permit tcp any eq bgp any
       220 permit rsvp any any
       230 permit tcp any any eq 6040
       240 permit tcp any any eq 5541 ttl eq 255
       250 permit tcp any any eq 5542 ttl eq 255
       260 permit tcp any any eq 9559
```

The output above can be turned into a new ACL like this one. We can also add the required command to open the RPC port:

```
ip access-list rpc-enabled
counters per-entry
10 permit icmp any any
20 permit ip any any tracked
30 permit udp any any eq bfd ttl eq 255
40 permit udp any any eq bfd-echo ttl eq 254
50 permit udp any any eq multihop-bfd micro-bfd sbfd
60 permit udp any eq sbfd any eq sbfd-initiator
70 permit ospf any any
80 permit tcp any any eq ssh telnet www snmp bgp https msdp ldp netconf-ssh gnmi
90 permit udp any any eq bootps bootpc snmp rip ntp ldp ptp-event ptp-general
100 permit tcp any any eq mlag ttl eq 255
110 permit udp any any eq mlag ttl eq 255
120 permit vrrp any any
130 permit ahp any any
140 permit pim any any
150 permit igmp any any
160 permit tcp any any range 5900 5910
170 permit tcp any any range 50000 50100
180 permit udp any any range 51000 51100
190 permit tcp any any eq 3333
200 permit tcp any any eq nat ttl eq 255
210 permit tcp any eq bgp any
220 permit rsvp any any
230 permit tcp any any eq 6040
240 permit tcp any any eq 5541 ttl eq 255
250 permit tcp any any eq 5542 ttl eq 255
260 permit tcp any any eq 9559
270 permit tcp any any eq 9543
exit
```

The new list like this one can be pasted directly into the command prompt.

To apply the ACL, we need to run:

```
system control-plane
ip access-group rpc-enabled in
```

Reference: https://eos.arista.com/default-control-plane-acl-explained/

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

## Error handling

The original EOS SDK communicates errors with exceptions by default. The RPC SDK has been designed to behave similarly. For functions that are not bulk calls, the SDK exceptions are translated into gRPC errors and the original error messages are also sent back to the client. gRPC’s framework may also translate these into exceptions back in the client. Here is a list of the SDK exception classes and their gRPC error counterparts:

| EOS SDK exception class     | Error code equivalent |
|-----------------------------|-----------------------|
| eos::invalid_range_error    | OUT_OF_RANGE          |
| eos::invalid_argument_error | INVALID_ARGUMENT      |
| eos::configuration_error    | FAILED_PRECONDITION   |
| eos::unsupported_error      | UNIMPLEMENTED         |
| eos::error                  | INTERNAL              |
| std::exception              | UNKNOWN               |

For the bulk RPC calls, the return structures share the same fields: one counter called processed and a structure called `status`. The works here are pretty similar to the standard C library: processed means the number of successful calls (like the return value for a call) and `status` is much like `errno`. If something went wrong, it holds the cause for the failure.

## Simple C++ client

One key benefit of the modularized API is that the client does not need to generate every possible interface if it is just going to use one. Here is how to create a simple C++ client that uses the EAPI interface to run the command “show version”. For the purposes of this demonstration, the requirements are gRPC and Protobuf development packages plus CMake for building.

First thing we need to do is to obtain the current proto files. Since they are present in the router, we can just scp them:

```sh
mkdir EosRpcClient
cd EosRpcClient
scp -Cr root@<router>:/usr/share/EosSdkRpc/proto/ .
```

This will result in a directory proto being created under our root. Now we have to compile the proto files that we are interested in. We’ll just use `eapi.proto` and `eapi_types.proto`. The first file contains messages and rpc definitions so it needs to be processed by protobuf and grpc generators. The second file only contains structures so protobuf is enough.

CMake has a good integration with Protobuf and already provides a convenient way to generate C++ files and headers. Unfortunately there is no official solution for gRPC yet. The file described below is a helper module to allow generation of gRPC C++ files with the same convenience as protobuf.

```cmake title="gRPC.cmake"
## A convenient gRPC proto file generator for CMake

find_library( grpc_LIBRARY grpc REQUIRED )
find_library( grpcpp_LIBRARY grpc++ REQUIRED )
find_program( grpc_PROTOC_CPP grpc_cpp_plugin )
set( grpc_LIBRARIES ${grpc_LIBRARY} ${grpcpp_LIBRARY} )

function( grpc_generate_cpp GRPC_CC GRPC_H )
  find_program( PROTOC protoc )
  foreach(ARG IN ITEMS ${ARGN})
     string( REGEX REPLACE "(.*/)?.*\.proto" "\\1"  PROTO_DIR ${ARG} )
     string( REPLACE ${PROTO_DIR} "" NAME ${ARG} )
     string( REGEX REPLACE "(.*)\.proto" "\\1"  NAME ${NAME} )
     string( CONCAT FULL_ARG ${CMAKE_SOURCE_DIR} "/" ${ARG})
     list( APPEND PROTO_files ${FULL_ARG} )
     list(APPEND CC_files
        "${CMAKE_CURRENT_BINARY_DIR}/${NAME}.grpc.pb.cc"
     )
     list(APPEND H_files
        "${CMAKE_CURRENT_BINARY_DIR}/${NAME}.grpc.pb.h"
     )
  endforeach()
  string( CONCAT PROTO_DIR ${CMAKE_SOURCE_DIR} "/" ${PROTO_DIR} )
  set( ${GRPC_CC} ${CC_files} PARENT_SCOPE )
  set( ${GRPC_H} ${H_files} PARENT_SCOPE )
  add_custom_command( OUTPUT ${CC_files} ${H_files}
     COMMAND ${PROTOC}
        --grpc_out "${CMAKE_CURRENT_BINARY_DIR}"
        -I "${PROTO_DIR}"
        --plugin=protoc-gen-grpc="${grpc_PROTOC_CPP}"
        ${PROTO_files}
        DEPENDS ${PROTO_files}
  )
endfunction()
```

Now we can start our own `CMakeLists.txt`:

```cmake title="CMakeLists.txt"
cmake_minimum_required( VERSION 3.6 )
project( eosrpcclient )

set( CMAKE_CXX_STANDARD 17 )
set( CMAKE_EXPORT_COMPILE_COMMANDS TRUE )

# include_directories for the generated headers.
include_directories( ${CMAKE_CURRENT_BINARY_DIR} )

# add cmake dependencies.
find_package( Protobuf )
include( grpc.cmake )

# this variable contains the RPC proto files
set( GRPC_FILES
  proto/eapi.proto
)

# this variable contains protobuf files.
set( PROTO_FILES
  proto/eapi_types.proto
)

# generate the files
protobuf_generate_cpp( PROTO_CC PROTO_H ${GRPC_FILES} ${PROTO_FILES} )
grpc_generate_cpp( GRPC_CC GRPC_H ${GRPC_FILES} )

# add the generated artifacts to the executable
add_executable( eosrpcclient
  client.cc
  ${GRPC_CC}
  ${GRPC_H}
  ${PROTO_CC}
  ${PROTO_H}
)

# set the required libraries
target_link_libraries( eosrpcclient
  ${grpc_LIBRARIES}
  ${Protobuf_LIBRARIES}
)
```

We can now add the client code (update the address on `CreateChannel`):

```c++ title="client.cc"
#include <grpc/grpc.h>
#include <grpcpp/grpcpp.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>

#include <eapi.grpc.pb.h>
#include <eapi.pb.h>
#include <eapi_types.pb.h>

#include <iostream>

int main() {
  try {
     // set up client side API
     auto channel {grpc::CreateChannel("<router-addr>:9543", grpc::InsecureChannelCredentials())};
     auto eapi {eos::remote::EapiMgrService::Stub(channel)};

     // prepare for the RPC call.
     // context allows us to set up metadata, compression or authentication on a per-call basis.
     // see https://grpc.github.io/grpc/cpp/classgrpc_1_1_client_context.html
     grpc::ClientContext context;
     // generated request and response objects
     eos::remote::RunShowCmdRequest request;
     eos::remote::RunShowCmdResponse response;
     request.set_command("show version");

     // make the call.
     eapi.run_show_cmd(&context, request, &response);
     auto & eapiResponse {response.response()};

     // This particular check is part of the eAPI module
     // see http://aristanetworks.github.io/EosSdk/docs/2.2.0/ref/eapi.html
     if(!eapiResponse.success()) {
        throw std::logic_error( eapiResponse.error_message() );
     }

     // For a successful show command, responses[0] holds the output as JSON.
     std::cout << "Response to \"show version\": " << eapiResponse.responses()[0] << '\n';

  } catch ( const std::exception & e ) {
     std::cerr << "call failed: " << e.what() << '\n';
  }
}
```

With this, we can build and test the project:

```sh
mkdir build
cd build
cmake .. && make
./eosrpcclient
```

And the expected response is something like this:

```
Response to "show version": {"imageFormatVersion": "1.0", "uptime": 1506.9400000000001, "modelName": "DCS-7050QX-32-F", "internalVersion": "4.27.0F-2GB-24596680.eostrunk", "memTotal": 4002848, "mfgName": "Arista", "serialNumber": "JAS12430029", "systemMacAddress": "00:1c:73:00:da:78", "bootupTimestamp": 1634646046.0, "memFree": 2128936, "version": "4.27.0F-2GB-24596680.eostrunk (engineering build)", "configMacAddress": "00:00:00:00:00:00", "isIntlVersion": false, "internalBuildId": "7d37543b-18ae-47f7-afe6-a2d4afc6b9ab", "hardwareRevision": "00.00", "hwMacAddress": "00:1c:73:00:da:78", "architecture": "x86_64"}
```

### Expanding our previous example: creating and removing one EVPN route

Now, let's expand our example to use the SDK (ip_route) to add and remove a single static route. The example below builds on top of the previous.

```cmake title="CMakeLists.txt" hl_lines="12 18 24-27 47"
cmake_minimum_required( VERSION 3.6 )
project( eosrpcclient )

set( CMAKE_CXX_STANDARD 17 )
set( CMAKE_EXPORT_COMPILE_COMMANDS TRUE )

# include_directories for the generated headers.
include_directories( ${CMAKE_CURRENT_BINARY_DIR} )

# add cmake dependencies.
find_package( Protobuf )
find_package( fmt )
include( grpc.cmake )

# this variable contains the RPC proto files
set( GRPC_FILES
  proto/eapi.proto
  proto/ip_route.proto
)

# this variable is set to the list of protobuf only files.
set( PROTO_FILES
  proto/eapi_types.proto
  proto/intf_types.proto
  proto/ip_route_types.proto
  proto/ip_types.proto
  proto/rpc_types.proto
)

# generate the files
protobuf_generate_cpp( PROTO_CC PROTO_H ${GRPC_FILES} ${PROTO_FILES} )
grpc_generate_cpp( GRPC_CC GRPC_H ${GRPC_FILES} )

# add the generated artifacts to the executable
add_executable( eosrpcclient
  client.cc
  ${GRPC_CC}
  ${GRPC_H}
  ${PROTO_CC}
  ${PROTO_H}
)

# set the required libraries
target_link_libraries( eosrpcclient
  ${grpc_LIBRARIES}
  ${Protobuf_LIBRARIES}
  fmt::fmt
)
```

And the updated code, with some added functions:

```c++ title="client.cc"
#include <grpc/grpc.h>
#include <grpcpp/grpcpp.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>

#include <eapi.grpc.pb.h>
#include <eapi.pb.h>
#include <eapi_types.pb.h>

#include <ip_route.grpc.pb.h>
#include <ip_route_types.pb.h>

#include <iostream>
#include <fmt/format.h>

const std::string intfName = "<interface>";
const std::string server = "<router-addr>:9543";

eos::remote::IpRouteKey sampleRouteKey() {
  eos::remote::IpRouteKey rk;
  auto & prefix = *rk.mutable_prefix();
  // IP addresses are specified as binary strings. In the example: 100.0.0.0/8
  prefix.set_ip_addr("\x64\0\0\0", 4);
  prefix.set_length(8);
  return rk;
}

// sets an example EVPN via for a route.
eos::remote::IpRouteVia sampleRouteVia() {
  eos::remote::IpRouteVia via;
  *via.mutable_key() = sampleRouteKey();
  via.set_vni(99);
  // VTEP address 1.0.2.1
  via.set_vtep_addr("\x01\0\x02\x01", 4);
  // virtual mac 00:aa:00:aa:00:bb
  via.set_router_mac_eth_addr("\0\xaa\0\xaa\0\xbb", 6);
  via.mutable_intf_id()->set_name(intfName);
  return via;
}

bool routeExists(eos::remote::IpRouteMgrService::Stub & ipRouteClient,
                const eos::remote::IpRouteKey & key) {
  std::cout << "ip_route_exists\n";
  eos::remote::IpRouteExistsRequest existsRequest;
  eos::remote::IpRouteExistsResponse existsResponse;
  grpc::ClientContext existsContext;
  *existsRequest.mutable_key() = key;
  auto status = ipRouteClient.ip_route_exists(&existsContext, existsRequest,
     &existsResponse);
  if (!status.ok()) {
     throw std::runtime_error(status.error_message());
  }
  return existsResponse.exists();
}

std::ostream& operator <<(std::ostream & os, const eos::remote::IpRoute & route ) {
  auto & key = route.key();
  auto & pfx = key.prefix();
  const u_char * pfxaddr = reinterpret_cast<const u_char*>(pfx.ip_addr().data());
  os << fmt::format( "key:(pfx={}.{}.{}.{}/{},pref={}), tag={}",
     pfxaddr[0], pfxaddr[1], pfxaddr[2], pfxaddr[3], pfx.length(), key.preference(),
     route.tag());
  return os;
}

/// this function lists all configured routes to stdout
void enumerate(eos::remote::IpRouteMgrService::Stub & ipRouteClient) {
  eos::remote::IpRoutesRequest request;
  eos::remote::IpRoutesResponse response;
  grpc::ClientContext context;
  auto responseReader(ipRouteClient.ip_routes(&context, request));
  std::cout << "routes:\n";
  while (responseReader->Read(&response)) {
     std::cout << '\t' << response.response() << '\n';
  }
}

/// This function creates a single EVPN route for prefix 100.0.0.0/8 to vtep 1.0.2.1
void createEvpnRoute(eos::remote::IpRouteMgrService::Stub & ipRouteClient) {
  // create route
  std::cout << "ip_route_set\n";
  eos::remote::IpRouteSetRequest request;
  eos::remote::IpRouteSetResponse response;
  grpc::ClientContext context;
  request.set_action(::eos::remote::IpRouteActions::IP_ROUTE_ACTION_FORWARD);
  auto & route = *request.mutable_route();
  *route.mutable_key() = sampleRouteKey();
  auto status = ipRouteClient.ip_route_set(&context, request, &response);
  if (!status.ok()) {
     throw std::runtime_error(status.error_message());
  }

  // set via for route
  std::cout << "ip_route_via_set\n";
  eos::remote::IpRouteViaSetRequest viaRequest;
  eos::remote::IpRouteViaSetResponse viaResponse;
  grpc::ClientContext viaContext;
  *viaRequest.mutable_via() = sampleRouteVia();
  status = ipRouteClient.ip_route_via_set(&viaContext, viaRequest, &viaResponse);
  if (!status.ok()) {
     throw std::runtime_error(status.error_message());
  }
  if (!routeExists(ipRouteClient, route.key() )) {
     throw std::runtime_error("ip_route_exists - not found");
  }
}

// This function deletes the via and the route created by the previous function.
void removeEvpnRoute(eos::remote::IpRouteMgrService::Stub & ipRouteClient) {
  // deletes a via for our test route.
  std::cout << "ip_route_via_del\n";
  eos::remote::IpRouteViaDelRequest viaRequest;
  eos::remote::IpRouteViaDelResponse viaResponse;
  grpc::ClientContext viaContext;
  *viaRequest.mutable_via() = sampleRouteVia();
  auto status = ipRouteClient.ip_route_via_del(&viaContext, viaRequest, &viaResponse);
  if (!status.ok()) {
     throw std::runtime_error(status.error_message());
  }

  std::cout << "ip_route_del\n";
  eos::remote::IpRouteDelRequest request;
  eos::remote::IpRouteDelResponse response;
  grpc::ClientContext context;
  *request.mutable_key() = sampleRouteKey();
  status = ipRouteClient.ip_route_del(&context, request, &response);
  if (!status.ok()) {
     throw std::runtime_error(status.error_message());
  }

  std::cout << '!';
  if (routeExists(ipRouteClient, request.key())) {
     throw std::runtime_error("ip_route_exists - not deleted");
  }
}

int main() {
  try {
     // set up client side API
     auto channel {grpc::CreateChannel(server, grpc::InsecureChannelCredentials())};
     auto eapi {eos::remote::EapiMgrService::Stub(channel)};
     auto ipRoute {eos::remote::IpRouteMgrService::Stub(channel)};

     // prepare for the RPC call.
     // context allows us to set up metadata, compression or authentication on a
     // per-call basis.
     // see https://grpc.github.io/grpc/cpp/classgrpc_1_1_client_context.html
     grpc::ClientContext context;
     // generated request and response objects
     eos::remote::RunShowCmdRequest request;
     eos::remote::RunShowCmdResponse response;
     request.set_command("show version");

     // make the call.
     eapi.run_show_cmd(&context, request, &response);
     auto & eapiResponse {response.response()};

     // This particular check is part of the eAPI module
     // see http://aristanetworks.github.io/EosSdk/docs/2.2.0/ref/eapi.html
     if(!eapiResponse.success()) {
        throw std::logic_error( eapiResponse.error_message() );
     }

     // for a successful show command, responses[0] holds the JSON output.
     std::cout << "Response to \"show version\": " << eapiResponse.responses()[0]
        << '\n';

     createEvpnRoute(ipRoute);
     enumerate(ipRoute);
     removeEvpnRoute(ipRoute);
     enumerate(ipRoute);
  } catch ( const std::exception & e ) {
     std::cerr << "call failed: " << e.what() << '\n';
  }
}
```

Running the program will yield the output, detailing the steps on creating and deleting a route:

```sh
$ ./eosrpcclient 
Response to "show version": {"mfgName": "Arista", "modelName": "DCS-7060PX4-32-F", "hardwareRevision": "11.00", "serialNumber": "JPE19290418", "systemMacAddress": "fc:bd:67:2b:2d:95", "hwMacAddress": "fc:bd:67:2b:2d:95", "configMacAddress": "00:00:00:00:00:00", "version": "4.28.2F-28045261.eostrunk.1 (engineering build)", "architecture": "x86_64", "internalVersion": "4.28.2F-28045261.eostrunk.1", "internalBuildId": "6505e1eb-b158-4179-9aa0-0b7486239433", "imageFormatVersion": "3.0", "imageOptimization": "Default", "bootupTimestamp": 1658137083.7456691, "uptime": 8067.6000000000004, "memTotal": 8165876, "memFree": 5713744, "isIntlVersion": false}
ip_route_set
ip_route_via_set
ip_route_exists
routes:
        key:(pfx=100.0.0.0/8,pref=0), tag=0
ip_route_via_del
ip_route_del
!ip_route_exists
routes:
$
```

To verify the route creation with CLI, we can debug the program and set a breakpoint before each of the new functions.

```sh
$ gdb eosrpcclient 
GNU gdb (GDB) Fedora 11.2-2.fc35
Copyright (C) 2022 Free Software Foundation, Inc.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Type "show copying" and "show warranty" for details.
This GDB was configured as "x86_64-redhat-linux-gnu".
Type "show configuration" for configuration details.
For bug reporting instructions, please see:
<https://www.gnu.org/software/gdb/bugs/>.
Find the GDB manual and other documentation resources online at:
    <http://www.gnu.org/software/gdb/documentation/>.

For help, type "help".
Type "apropos word" to search for commands related to "word"...
Reading symbols from eosrpcclient...

(gdb) br createEvpnRoute
Breakpoint 1 at 0x4099dc
(gdb) br removeEvpnRoute
Breakpoint 2 at 0x409e6d
(gdb) r
Starting program: /home/paulo/src/EosRpcClient/build/eosrpcclient 
[New Thread 0x7ffff6d16640 (LWP 50219)]
[New Thread 0x7ffff6515640 (LWP 50220)]
[New Thread 0x7ffff5d14640 (LWP 50221)]
Response to "show version": {"imageFormatVersion": "3.0", "uptime": 6693.9300000000003, "modelName": "DCS-7280SR-32C2-F", "internalVersion": "4.28.1F-27290106.eostrunk", "memTotal": 8165212, "mfgName": "Arista", "serialNumber": "JAS17450022", "systemMacAddress": "74:83:ef:01:80:56", "bootupTimestamp": 1652463541.5252528, "memFree": 5481240, "version": "4.28.1F-27290106.eostrunk (engineering build)", "configMacAddress": "00:00:00:00:00:00", "isIntlVersion": false, "imageOptimization": "Default", "internalBuildId": "6d0e8967-f438-4e05-a8d2-176df292e4b6", "hardwareRevision": "20.00", "hwMacAddress": "74:83:ef:01:80:56", "architecture": "x86_64"}

Thread 1 "eosrpcclient" hit Breakpoint 1, 0x00000000004099dc in createEvpnRoute(std::shared_ptr<grpc::Channel> const&) ()
(gdb)
```

At this point, we can verify on the switch there are no EVPN routes:

```
#show vxlan vni
VNI to VLAN Mapping for Vxlan1
VNI            VLAN       Source       Interface       802.1Q Tag
-------------- ---------- ------------ --------------- ----------
14455119       2516       static       Vxlan1          2516      

VNI to dynamic VLAN Mapping for Vxlan1
VNI       VLAN       VRF       Source       
--------- ---------- --------- ------------
```

Continuing the program:

```sh
(gdb) c
Continuing.
[New Thread 0x7ffff5513640 (LWP 50911)]

Thread 1 "eosrpcclient" hit Breakpoint 2, 0x0000000000409e6d in removeEvpnRoute(std::shared_ptr<grpc::Channel> const&) ()
(gdb) 
```

We can see a new VNI 99 created:

```
#show vxlan vni
VNI to VLAN Mapping for Vxlan1
VNI            VLAN       Source       Interface       802.1Q Tag
-------------- ---------- ------------ --------------- ----------
14455119       2516       static       Vxlan1          2516

VNI to dynamic VLAN Mapping for Vxlan1
VNI       VLAN       VRF       Source 
--------- ---------- --------- ------------ 
99        4090                 evpn
```

Continuing once again to remove the route:

```sh
(gdb) c
Continuing.
[Thread 0x7ffff5513640 (LWP 50911) exited]
[Thread 0x7ffff5d14640 (LWP 50221) exited]
[Thread 0x7ffff6515640 (LWP 50220) exited]
[Thread 0x7ffff6d16640 (LWP 50219) exited]
[Inferior 1 (process 49995) exited normally]
(gdb) 
```

And verifying the route has been removed:

```
#show vxlan vni
VNI to VLAN Mapping for Vxlan1
VNI            VLAN       Source       Interface       802.1Q Tag
-------------- ---------- ------------ --------------- ----------
14455119       2516       static       Vxlan1          2516

VNI to dynamic VLAN Mapping for Vxlan1
VNI       VLAN       VRF       Source
--------- ---------- --------- ------------ 
```

## Known Issues and Limitations

### EosSdk default fields

From release  4.29.2F onwards, the fields listed below have been made explicitly optional in the proto files, with the purpose of differentiating between a field that has been explicitly set to zero from an unset field. Unset fields are mapped to EOS SDK default values.

Some of the types in EosSdk have non-zero default values for some of their fields. Most of the time EosSdkRpc uses default values of zero (or the equivalent). Therefore, when using EosSdkRpc if these fields with non-zero default values are not explicitly specified there can be a difference in behavior when setting the same configuration in EosSdk and EosSdkRpc. A list of the supported fields in EosSdkRpc which have non-zero default values in EosSdk is provided. The equivalent to the EosSdk default value is also specified for each field. These values can be manually set when using EosSdkRpc to ensure consistency with what their values in EosSdk would be. Note that if the client is already explicitly setting values for these fields in EosSdk/EosSdkRpc the default values do not matter.

| File                      | Message       | Field                | Equivalent EosSdk Default Value |
|---------------------------|---------------|----------------------|---------------------------------|
| acl_types.proto           | AclTtlSpec    | oper                 | ACL_RANGE_ANY                   |
| acl_types.proto           | AclPortSpec   | oper                 | ACL_RANGE_ANY                   |
| acl_types.proto           | AclRuleBase   | action               | ACL_PERMIT                      |
| acl_types.proto           | AclRuleIp     | vlan_mask            | xFFF                            |
| acl_types.proto           | AclRuleIp     | inner_vlan_mask      | 0xFFF                           |
| acl_types.proto           | AclRuleIp     | ip_type              | ACL_IP_TYPE_ANY                 |
| acl_types.proto           | AclRuleIp     | icmp_type            | ALL_ICMP (65535)                |
| acl_types.proto           | AclRuleIp     | icmp_code            | ALL_ICMP (65535)                |
| acl_types.proto           | AclRuleEth    | vlan_mask            | 0xFFF                           |
| acl_types.proto           | AclRuleEth    | inner_vlan_mask      | 0xFFF                           |
| acl_types.proto           | AclRuleEth    | eth_protocol         | 0xFFFFFFFF                      |
| ip_route_types.proto      | IpRouteKey    | preference           | 1                               |
| macsec_types.proto        | MacsecProfile | key_server_priority  | 16                              |
| macsec_types.proto        | MacsecProfile | mka_life_time*       | 6                               |
| macsec_types.proto        | MacsecProfile | cipher*              | GCM_AES_XPN_128                 |
| macsec_types.proto        | MacsecProfile | traffic_policy       | TRAFFIC_POLICY_ACTIVE_SAK       |
| macsec_types.proto        | MacsecProfile | replay_protection    | True                            |
| nexthop_group_types.proto | NexthopGroup  | ttl                  | 64                              |
| policy_map_types.proto    | PolicyMapRule | policy_map_rule_type | POLICY_RULE_TYPE_CLASSMAP       |

*The default value of 0 in the EosSdkRpc will automatically be replaced by the EosSdk default value. 
