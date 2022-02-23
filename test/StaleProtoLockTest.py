#!/usr/bin/env arista-python
# Copyright (c) 2021 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

'''
This test ensures that any .proto files within /src/EosSdkRpcProtos/proto
have been modified without updating the proto.lock file.
The proto.lock file is used to ensure, no compatibility breaking changes are
made to the proto files.

A new proto.lock file, created in a temporary directory, to be matched against
the provided (committed) proto.lock in the directory proto. Both must contain
the same information.

To prevent against ordering issues, `DeepDiff` of the parsed
json objects is used instead of plain diff between the files.
'''
from __future__ import absolute_import, division, print_function

import Assert
from deepdiff import DeepDiff
import json
import os
import tempfile

excludedFiles = []
sourceDir = '/src/EosSdkRpcProtos/proto/'

def createLockFile():
   tempDir = tempfile.mkdtemp()
   lockFile = tempDir + '/proto.lock'
   print( 'Creating temporary lock file {}'.format( lockFile ) )
   Assert.assertEqual(
      os.system( 'protolock init --protoroot {} --lockdir {}'.format(
         sourceDir, tempDir ) ), 0 )
   return lockFile

def verifyProtolock():
   refFile = createLockFile()
   sourceFile = sourceDir + 'proto.lock'
   testData = json.load( open( sourceFile, 'r' ) )
   referenceData = json.load( open( refFile, 'r' ) )
   diff = DeepDiff( testData, referenceData, ignore_order=True,
      report_repetition=True )
   if diff:
      os.system( 'diff -u {} {}'.format( sourceFile, refFile ) )
      Assert.fail( "Some errors occurred. Please run the script "
      "/src/EosSdkRpcProtos/checkprotos to verify and maintain the protolock "
      "metadata up to date.\n"
      "See README.md for more details" )

if __name__ == '__main__':
   verifyProtolock()
