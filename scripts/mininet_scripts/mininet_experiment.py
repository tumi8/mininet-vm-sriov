#!/usr/bin/env python3
import sys
import subprocess
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import Intf, Link, HwPair
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.node import VMHost, Host
from mininet.nodelib import LinuxBridge, VMLinuxBridge

DEFAULT_CMDLINE = "boot=live BOOTIF=01-52-54-00-12-34-56 noeject net.ifnames=0"

class TestTopo(Topo):
    def __init__(self, optimized):
        self.optimized = optimized
        Topo.__init__(self)

    def build(self):
        cmdline = DEFAULT_CMDLINE
        if self.optimized:
            cmdline = "idle=poll intel_idle.max_cstate=0 intel_pstate=disable amd_pstate=disable tsc=reliable mce=ignore_ce audit=0 nmi_watchdog=0 skew_tick=1 irqaffinity=0 nosoftlockup " + cmdline

        hosts = []
        for i in range(7):
            cpupin = 24 if i % 2 == 0 else 8
            cpupin += (i // 2) * 2
            h = self.addHost(f"h{i+1}", ip=None, cmdline=cmdline, cpus=2, cpupin=[cpupin,cpupin+1], memory="4G")
            hosts.append(h)

        for i in range(6):
            params1={"ip": f"10.0.3.1{i:02}/24"}
            params2={"ip": f"10.0.3.2{i:02}/32"}
            # alternate order of hosts to fully use duplex link
            if i % 2 == 0:
                h1 = hosts[i]
                h2 = hosts[i+1]
                h1params = params1
                h2params = params2
            else:
                h2 = hosts[i]
                h1 = hosts[i+1]
                h2params = params1
                h1params = params2
            self.addLink(h1, h2, params1=h1params, params2=h2params)


    def add_routes(net):
        for i in range(6):
            h = net.get(f"h{i+1}")
            h.cmd(f"ip route add 10.0.2.20/32 via 10.0.3.2{i:02}")

    def add_hw_intfs(net):
        h1 = net.get("h1")
        _ = Intf("enp100s0f1v0", node=h1, ip="10.0.0.101/24")
        h1.cmd('ip l set dev enp100s0f1v0 address "3e:e5:a8:40:0d:00"')
        h7 = net.get("h7")
        _ = Intf("enp33s0f1v0", node=h7, ip="10.0.2.101/24")
        h7.cmd("arp -s 10.0.2.20 56:54:00:00:00:01")


if __name__ == "__main__":
    hosts_name = sys.argv[1]
    if hosts_name == "namespace":
        hosts_cls = Host
        switch_cls = LinuxBridge
        topo = TestTopo(False)
    elif hosts_name == "vm":
        hosts_cls = VMHost
        switch_cls = VMLinuxBridge
        topo = TestTopo(False)
    elif hosts_name == "vm_opt":
        hosts_cls = VMHost
        switch_cls = VMLinuxBridge
        topo = TestTopo(True)


    linkpairs = []
    for i in range(14):
        linkpairs.append((f"enp100s0f0v{i}", f"enp33s0f0v{i}"))

    links_name = sys.argv[2]
    if links_name == "veth":
        links_cls = Link
    elif links_name == "hwpair":
        links_cls = HwPair
        HwPair.available_pairs = linkpairs.copy()

    print(f"RUNNING EXPERIMENT WITH {hosts_name} over {links_name}")
    setLogLevel("info")

    net = Mininet(topo, host=hosts_cls, switch=switch_cls, link=links_cls)
    net.start()

    info("Adding hardware interfaces\n")
    TestTopo.add_hw_intfs(net)

    info("Adding routes\n")
    TestTopo.add_routes(net)

    for h in net.hosts:
        h.cmd("sysctl net.ipv4.ip_forward=1")
    #info("Testing network connectivity\n")
    #net.pingAll()
    #CLI(net)
    subprocess.run("pos_sync")
    info("Finished pos sync 1")
    subprocess.run("pos_sync")
    info("Finished pos sync 2")
    subprocess.run("pos_sync")
    info("Finished pos sync 3")
    net.stop()
