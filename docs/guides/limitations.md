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

### IpRouteService

Only the EosSdkRpc transport which creates the routes may modify them.
