#!/usr/bin/env python3
"""
CSC6410 Experiment 2 — SDN/OpenFlow flow-table lab
Author: Srinesh Goud Bandi

Purpose
-------
Create the three-host, one-switch Mininet topology used in the experiment.

Topology
--------
h1 (10.0.0.1) --\
h2 (10.0.0.2) ---- s1
h3 (10.0.0.3) --/

Logic
-----
- Uses one Open vSwitch bridge and three hosts.
- Starts without a remote controller.
- Sets the switch to standalone fail mode, matching the lab's initial setup.
- Opens the Mininet CLI so the experiment commands can be entered and observed.

Assumptions
-----------
- Mininet and Open vSwitch are installed and working.
- Run this script with sudo/root privileges.
- The default OVS datapath is used (the lab reported system@ovs-system).
- Host IP addresses are assigned by Mininet.

How to run
----------
    sudo python3 flowlab.py

Suggested checks at the mininet> prompt
---------------------------------------
    nodes
    net
    sh ovs-vsctl get-fail-mode s1
    sh ovs-ofctl dump-flows s1

Experiment commands (run manually, capture outputs/screenshots)
----------------------------------------------------------------
1. Baseline standalone switching:
    sh ovs-ofctl del-flows s1
    pingall
    sh ovs-ofctl dump-flows s1

2. Empty table test:
    sh ovs-ofctl del-flows s1
    sh ovs-ofctl dump-flows s1
    pingall
    sh ovs-ofctl dump-flows s1

3. Add three port-forwarding rules:
    sh ovs-ofctl add-flow s1 "priority=100,in_port=1,actions=output:2,output:3"
    sh ovs-ofctl add-flow s1 "priority=100,in_port=2,actions=output:1,output:3"
    sh ovs-ofctl add-flow s1 "priority=100,in_port=3,actions=output:1,output:2"
    sh ovs-ofctl dump-flows s1
    pingall
    sh ovs-ofctl dump-flows s1

4. Priority-200 drop test:
    sh ovs-ofctl add-flow s1 "priority=200,ip,in_port=3,nw_dst=10.0.0.1,actions=drop"
    h3 ping -c 3 h1
    h2 ping -c 3 h1
    sh ovs-appctl ofproto/trace s1 in_port=3,ip,nw_src=10.0.0.3,nw_dst=10.0.0.1
    sh ovs-ofctl dump-flows s1

5. Priority-50 comparison:
    sh ovs-ofctl --strict del-flows s1 "priority=200,ip,in_port=3,nw_dst=10.0.0.1"
    sh ovs-ofctl add-flow s1 "priority=50,ip,in_port=3,nw_dst=10.0.0.1,actions=drop"
    h3 ping -c 3 h1
    sh ovs-ofctl dump-flows s1

6. Priority-0 catch-all drop test:
    sh ovs-ofctl del-flows s1
    sh ovs-ofctl add-flow s1 "priority=0,actions=drop"
    pingall
    sh ovs-ofctl dump-flows s1

Testing
-------
The script itself tests topology startup by creating the network and leaving
the Mininet CLI available. The ping, flow-counter, and trace tests above are
interactive experiment steps; record the actual output from your own run.

Limits and fallback
-------------------
This script does not automatically assert that ping or flow-counter values
match a fixed expected number. Packet counters depend on ARP, ICMP, timing,
and prior traffic. If startup fails, verify Mininet/OVS installation and
permissions, then try:
    sudo mn -c
before rerunning. Do not use cleanup while another Mininet lab is running.
"""

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSSwitch
from mininet.cli import CLI


class FlowLabTopo(Topo):
    """One switch connected to three hosts."""

    def build(self):
        switch = self.addSwitch("s1")
        for host_num in range(1, 4):
            host = self.addHost(
                f"h{host_num}",
                ip=f"10.0.0.{host_num}/8"
            )
            self.addLink(host, switch)


def main():
    topo = FlowLabTopo()

    # No controller is attached: the experiment compares standalone
    # switching with explicitly installed OpenFlow rules.
    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSSwitch,
        autoSetMacs=True,
        autoStaticArp=False
    )

    try:
        net.start()

        # Match the standalone mode used for the initial lab experiment.
        # The command is issued through OVSDB after the bridge is created.
        switch = net.get("s1")
        switch.cmd("ovs-vsctl set-fail-mode s1 standalone")

        print("\nCSC6410 Experiment 2 topology is running.")
        print("Hosts: h1=10.0.0.1, h2=10.0.0.2, h3=10.0.0.3")
        print("Switch: s1 (standalone fail mode)")
        print("Enter 'help' for Mininet CLI commands; enter 'exit' to stop.\n")

        CLI(net)
    finally:
        net.stop()


if __name__ == "__main__":
    main()
