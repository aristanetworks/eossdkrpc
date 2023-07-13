# Exposing the RPC port

The default port for EosSdkRpc (9543) is not permitted within the default control-plane ACL. Hence, even though the transport may be listening on an external addresses, we still need to grant access to the port configured for the transport with an ACL. For those who have already set up a custom ACL to the control plane, a rule needs to be added: `permit tcp <source> <dest> eq 9543` (replace `9543` with your configured port for the EosSdkRpc transport).

## Creating a custom control-plane ACL:

To set up a custom ACL for the control plane, we start by obtaining the default ACL:

### Obtain and clean the default control-plane ACL:

We can view the default control-plane ACL via:
```
# sh ip access-lists default-control-plane-acl
IP Access List default-control-plane-acl [readonly]
       counters per-entry
       10 permit icmp any any
       20 permit ip any any tracked [match 482 packets, 0:35:48 ago]
       30 permit udp any any eq bfd ttl eq 255
       40 permit udp any any eq bfd-echo ttl eq 254
       50 permit udp any any eq multihop-bfd micro-bfd sbfd
       60 permit udp any eq sbfd any eq sbfd-initiator
       70 permit ospf any any
       80 permit tcp any any eq ssh telnet www snmp bgp https msdp ldp netconf-ssh gnmi [match 3 packets, 0:39:06 ago]
       90 permit udp any any eq bootps bootpc snmp rip ntp ldp ptp-event ptp-general
       100 permit tcp any any eq mlag ttl eq 255
       110 permit udp any any eq mlag ttl eq 255
       120 permit vrrp any any
       130 permit ahp any any
       140 permit pim any any
       150 permit igmp any any
       160 permit tcp any any range 5900 5910
       170 permit tcp any any range 50000 50100
       180 permit udp any any range 51000 51100
       190 permit tcp any any eq 3333
       200 permit tcp any any eq nat ttl eq 255
       210 permit tcp any eq bgp any
       220 permit rsvp any any
       230 permit tcp any any eq 6040
       240 permit tcp any any eq 5541 ttl eq 255
       250 permit tcp any any eq 5542 ttl eq 255
       260 permit tcp any any eq 9559
```

To quickly copy and modify the above ACL we can make use of `sed` and save the modifications to a new file in '/mnt/flash`:

```
show ip access-lists default-control-plane-acl | redirect flash:cpacl.txt
```

Enter bash:
```
#bash
```

Go to `/mnt/flash` and remove the match outputs:
```
cd /mnt/flash
sudo sed -i  "s/\[.*//g" cpacl.txt
```

The original output should now be clean without any counters information. 

Now we can just copy that ACLs content into a new ACL, add our new rules (in this case `permit tcp any any eq 9543`) and apply it on the control-plane.

### Create a new ACL using the cleaned default control-plane ACL
From config mode:
```
ip access-list custom-cp
<paste the content of the default CP from the file created>
270 permit tcp any any eq 9543
exit
```

### Apply the newly created ACL to the control-plane

Default VRF
```
system control-plane
   ip access-group custom-cp in
```

Non-default VRF:
```
system control-plane
ip access-group custom-cp vrf management in
```

References:

[https://eos.arista.com/default-control-plane-acl-explained/](https://eos.arista.com/default-control-plane-acl-explained/)
[https://aristanetworks.github.io/openmgmt/configuration/security/](https://aristanetworks.github.io/openmgmt/configuration/security/)
