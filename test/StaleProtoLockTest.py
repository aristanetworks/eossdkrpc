#!/usr/bin/env arista-python
# Copyright (c) 2021 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from __future__ import absolute_import, division, print_function

import glob
import os

# This test ensures that any .proto files within /src/EosSdkRpcProtos/proto
# have been modified without updating the proto.lock file.
# The proto.lock file is used to ensure, no compatibility breaking changes are
# made to the proto files.

# Remove files after excluded protobufs are finalised.
# Used to prevent build failures due to not updating the lock file
# for template protobufs.
excludedFiles = [
   'ip_route.proto',
   'defs.proto',
   'intf.proto',
   'macsec.proto',
   'ip_intf.proto',
   ]

def CheckLockFileIsNotStale():
   lockFileModifiedDate = os.path.getmtime( '/src/EosSdkRpcProtos/proto/proto.lock' )
   protoFiles = glob.glob( "/src/EosSdkRpcProtos/proto/*.proto" )
   # Find the latest modified proto file
   protoFilesModifiedDate = max( [ os.path.getmtime( path )
                                   for path in protoFiles
                                   if os.path.basename( path )
                                   not in excludedFiles ] )
   if protoFilesModifiedDate > lockFileModifiedDate:
      raise AssertionError( "Proto.lock has not been updated to include the "
            "changes made to the protobuf files.\n"
            "More protolock info in README.\n"
            "Please run:\n"
            "a4 open /src/EosSdkRpcProtos/proto/proto.lock \n"
            "protolock commit -lockdir /src/EosSdkRpcProtos/proto"
            " -protoroot /src/EosSdkRpcProtos/proto" )

if __name__ == '__main__':
   CheckLockFileIsNotStale()
