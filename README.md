Adding or updating a protobuf file
---
Protolock is a simple tool that we use to ensure backwards
compatability for our protobufs. When updating existing .proto files or 
adding new ones, please do the following:

To ensure no compatibility breaking changes have been made run the following command:
```
   $ protolock status -lockdir /src/EosSdkRpcProtos/proto -protoroot 
     /src/EosSdkRpcProtos/proto
```

If there are exists any `CONFLICTS` in the output, you have made an incompatible
change and this must be resolved.

Otherwise:
Update the proto.lock file with the new proto changes:
```
   $ a p4 edit /src/EosSdkRpcProtos/proto/proto.lock
   $ protolock commit -lockdir /src/EosSdkRpcProtos/proto -protoroot 
     /src/EosSdkRpcProtos/proto
```

You should then submit the updated proto.lock file along with your .proto changes.
