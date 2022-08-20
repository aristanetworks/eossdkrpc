# Adding or updating a protobuf file

Before the proto file gets implemented, it must be added to the `upcoming_proto` directory
so that it won't be distributed as part of EOS until it is completed. This directory
is not checked by protolock (described below).

If the proto file is a new module, it should be started in `upcoming_proto` to be later
moved to the `proto` directory. Once a file merges in the `proto` directory, it will
be distributed with future versions of EOS.

When we are updating a proto file, it is ok to update the production version of the proto
file as long as the change is also guaranteed to be supported in the same MUT. The
purpose here is to avoid publishing unsupported proto files.

If an update to a proto file is rather big for a single MUT, a copy of the original
should be made into `upcoming_proto`, preferrably in the form `module_feature.proto`
where the changes should be made. When the feature is implemented, it is possible to
copy back the updated file into protos because protolock will kick in and check if
the proposed changes break compatibility with the production version. A manual merge
could be required.

Upcoming files are compiled slightly differently than production ones. Production files
do not need to specifiy directory while importing. They can simply import `foo.proto`
but upcoming protos must specifiy the immediate source directory they are importing
from. This facilitates importing from unchanged production files.

Protolock is a simple tool that we use to ensure backwards
compatability for our protobufs. When updating existing .proto files or 
adding new ones, please do the following:

A shell script called `checkprotos` has been created to ensure all steps described
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
