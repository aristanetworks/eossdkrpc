# Simple C++ client

One key benefit of the modularized API is that the client does not need to generate every possible interface if it is just going to use one. Here is how to create a simple C++ client that uses the EAPI interface to run the command “show version”. For the purposes of this demonstration, the requirements are gRPC and Protobuf development packages plus CMake for building.

## Obtaining the EosSdkRpc proto files

First thing we need to do is to obtain the current proto files (either from the github, or the EOS device itself). Since they are present in the router, we can just scp them:

```sh
mkdir EosRpcClient
cd EosRpcClient
scp -Cr root@<router>:/usr/share/EosSdkRpc/proto/ .
```

## Generating C++ from the proto files

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

## Creating the client

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

## Build and test

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

## Further examples
### Creating and removing one EVPN route

Now, let's expand our simple client to use the SDK (ip_route) to add and remove a single static route. The example below builds on top of the previous.

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
