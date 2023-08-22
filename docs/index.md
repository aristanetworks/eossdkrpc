# Arista's EOS SDK RPC

!!! info ""
    This is the official documentation for the gRPC API over Arista's EOS SDK.

---

Sections of interest:

- [API reference](./api-reference/index.md)
- [Guides](./guides/index.md)
- [FAQ](./faq.md)

---

EosSdkRpc is an agent built on top of our EosSdk that uses gRPC as a mechanism to provide remote access to the SDK.

This agent is present EOS, and starting in the 4.29 release is currently enabled via the `management api eos-sdk-rpc` CLI. The gRPC interface that the agent supports closely matches the interface provided by EosSdk, and the intent is that the `.proto` interface can be publicly supported. As well as potentially allowing for remote access, using protobuf to specify the interface isolates customer code from the Linux ABI issues that come with building C++ applications on different compiler, libc, and kernel versions.

The default listen port is `9543` but this can be changed to allow external access. Encrypted access is supported for EosSdkRpc agents configured via the `management api eos-sdk-rpc` CLI. An ACL should be used to limit the hosts that have access to the agent.

The API mirroring is intended to be modular in the same fashion as the SDK itself. Each proto file mirrors one specific SDK module and the RPC definitions and messages also aim to be as close as possible to the original SDK API call, in an attempt to make the learning gap as small as possible.

For performance reasons, “setter” RPC calls also come with bulk versions, which minimizes the RPC overhead. These calls differ from their original counterparts by providing a sequence of individual operations which are performed locally in batches, without requiring a round-trip to the client for each operation.

Multiple clients are supported by EosSdkRpc and most state is shared between these clients. Requests are fulfilled without regard to which client invoked the RPC call.
