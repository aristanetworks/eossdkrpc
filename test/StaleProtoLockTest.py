#!/usr/bin/env arista-python
# Copyright (c) 2021 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from __future__ import absolute_import, division, print_function

import Assert
import glob
from hashlib import sha256
import os

# This test ensures that any .proto files within /src/EosSdkRpcProtos/proto
# have been modified without updating the proto.lock file.
# The proto.lock file is used to ensure, no compatibility breaking changes are
# made to the proto files.

# Remove files after excluded protobufs are finalised.
# Used to prevent build failures due to not updating the lock file
# for template protobufs.
excludedFiles = []
sourceDir = '/src/EosSdkRpcProtos/proto/'

def getHashes():
   with open( sourceDir + 'protolock.shasum', 'r' ) as hashFile:
      hashes = {}
      for line in hashFile:
         hashStr, fileName = line.split()
         if fileName in excludedFiles:
            continue
         hashes[ fileName ] = hashStr
      return hashes

def matchHashes( hashes ):
   fail = False
   for name in hashes:
      expected = hashes[ name ]
      name = sourceDir + name
      with open( name, 'rb' ) as testFile:
         current = sha256( testFile.read() ).hexdigest()
      if current != expected:
         print( "hash check failed for proto file {}".format( name ) )
         fail = True
   protoFiles = glob.glob( sourceDir + "*.proto" )
   for protoFile in protoFiles:
      if not protoFile[ len( sourceDir ): ] in hashes:
         print( "proto file {} not hashed".format( protoFile ) )
         fail = True
   Assert.assertFalse( fail,
      "Some errors occurred. Please run the script "
      "/src/EosSdkRpcProtos/checkprotos to verify and maintain the protolock "
      "metadata and hashes up to date.\n"
      "See README.md for more details" )

if __name__ == '__main__':
   matchHashes( getHashes() )
