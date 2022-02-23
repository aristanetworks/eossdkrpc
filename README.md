# Adding or updating a protobuf file

Protolock is a simple tool that we use to ensure backwards
compatability for our protobufs. When updating existing .proto files or 
adding new ones, please do the following:

A shell script called `checkprotos` have been created to ensure all steps described
below have been done. The script affects `/src/EosSdkRpcProtos/proto/proto.lock`,
which must have write permissions. Once it is writable, running the script
`/src/EosSdkRpcProtos/checkprotos` should be enough to check compatibility of new
changes and maintain the metadata up to date.

## Manual steps

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
