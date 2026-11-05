#!/usr/bin/env python3
"""CSC6410 Experiment 2: reproducible Mininet/Open vSwitch tests.
Purpose: build three hosts, install manual flow rules, show counters before/after pings.
Logic: run baseline, priority-200 block, priority-50 comparison, and table-miss drop.
Assumptions: WSL/Linux with Mininet, OVS, root privileges, and system datapath.
Testing: compare each printed ping result with dump-flows and ofproto/trace.
Limitations: kernel/OVS behavior and counters vary; ARP/background traffic affects counts.
Fallback: if interface creation fails, exit and run 'sudo mn -c' before retrying.
Run: sudo python3 flowlab_revised.py
"""
import subprocess
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.topo import Topo

class ThreeHosts(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        for n in range(1, 4):
            h = self.addHost(f'h{n}', ip=f'10.0.0.{n}/8')
            self.addLink(h, s1)

def ovs(*args):
    command = ['ovs-ofctl', *args]
    print('$ ' + ' '.join(command), flush=True)
    result = subprocess.run(command, text=True, capture_output=True)
    print(result.stdout, end='')
    if result.returncode:
        print(result.stderr, end='')
        raise RuntimeError(f'Command failed: {command}')

def trace():
    command = ['ovs-appctl', 'ofproto/trace', 's1',
               'in_port=3,ip,nw_src=10.0.0.3,nw_dst=10.0.0.1']
    print('$ ' + ' '.join(command))
    result = subprocess.run(command, text=True, capture_output=True)
    print(result.stdout, end='')
    if result.returncode:
        print(result.stderr, end='')

def ping(host, target):
    print(f'$ {host.name} ping -c 3 {target.name}', flush=True)
    print(host.cmd(f'ping -c 3 {target.IP()}'), end='', flush=True)

def main():
    net = Mininet(topo=ThreeHosts(), controller=None, switch=OVSSwitch,
                  autoSetMacs=True, autoStaticArp=False)
    try:
        net.start()
        subprocess.run(['ovs-vsctl', 'set-fail-mode', 's1', 'secure'], check=True)
        h1, h2, h3 = (net.get(f'h{n}') for n in (1, 2, 3))
        print('\n=== Empty table / secure mode ===')
        ovs('del-flows', 's1')
        ovs('dump-flows', 's1')
        net.pingAll()
        print('\n=== Priority-100 forwarding ===')
        ovs('add-flow', 's1', 'priority=100,arp,actions=FLOOD')
        for n in range(1, 4):
            ovs('add-flow', 's1', f'priority=100,ip,nw_dst=10.0.0.{n},actions=output:{n}')
        ovs('dump-flows', 's1')
        net.pingAll()
        ovs('dump-flows', 's1')
        print('\n=== Priority-200 block ===')
        rule = 'ip,nw_src=10.0.0.3,nw_dst=10.0.0.1'
        ovs('add-flow', 's1', f'priority=200,{rule},actions=drop')
        ping(h3, h1)
        ping(h2, h1)
        ovs('dump-flows', 's1')
        trace()
        print('\n=== Priority-50 comparison ===')
        ovs('--strict', 'del-flows', 's1', f'priority=200,{rule}')
        ovs('add-flow', 's1', f'priority=50,{rule},actions=drop')
        ping(h3, h1)
        ovs('dump-flows', 's1')
        trace()
        print('\n=== Table-miss / catch-all ===')
        ovs('del-flows', 's1', 'arp')
        for h in (h1, h2, h3):
            h.cmd('ip neigh flush all')
        ovs('add-flow', 's1', 'priority=0,actions=drop')
        ovs('dump-flows', 's1')
        net.pingAll()
        ovs('dump-flows', 's1')
        print('\n=== Standalone after clearing flows ===')
        ovs('del-flows', 's1')
        subprocess.run(['ovs-vsctl', 'set-fail-mode', 's1', 'standalone'], check=True)
        ovs('dump-flows', 's1')
        net.pingAll()
        ovs('dump-flows', 's1')
    finally:
        net.stop()

if __name__ == '__main__':
    main()
