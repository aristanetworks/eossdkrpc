# Error handling

## EOS SDK errors
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

## Other Errors
If AAA authentication is enabled and fails for a given RPC call to that transport, an error message is returned to the client.
Example error message:
```
grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
        status = StatusCode.UNAUTHENTICATED
        details = "Username and password authentication failed."
        …
```

