#!/usr/bin/env python3
"""
Is extracting PCAPs to a CSV-like representation used to import data into Postgresql
"""
import argparse
import cProfile
import logging
import sys

from pypacker import ppcap
from pypacker.layer12 import ethernet
from pypacker.layer3 import ip, ip6
from pypacker.layer3 import icmp as icmpP
from pypacker.layer3 import icmp6 as icmp6P
from pypacker.layer4 import udp as udpPCAP
from pypacker.layer4 import tcp as tcpP

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def extract_l4_protocols(buf):
    ipv4 = 0
    ipv6 = 0
    other = 0

    ipv4_no_header = 0
    tcp = 0
    udp = 0
    icmp = 0
    icmp6 = 0
    other_l4 = 0

    eth = ethernet.Ethernet(buf)

    if eth is not None:
        if eth[ip.IP] is not None:
            ipv4 = 1
        elif eth[ip6.IP6] is not None:
            ipv6 = 1
        else:
            other = 1

        if ipv4 == 1 or ipv6 == 1:

            if eth[udpPCAP.UDP]:
                udp = 1
            elif eth[tcpP.TCP]:
                tcp = 1
            elif eth[icmpP.ICMP]:
                icmp = 1
            elif eth[icmp6P.ICMP6]:
                icmp6 = 1
            else:
                other_l4 = 1
                logging.debug("Detected unknown IPv4 payload")

    return buf, ipv4, ipv6, other, ipv4_no_header, tcp, udp, icmp, icmp6, other_l4


def extract_eth_data(eth):
    """
    Extracting general Ethernet data such as
    :param eth:
    :return:
    """
    if eth is None:
        return {}
    return dict(src_mac=eth.src_s, dst_mac=eth.dst_s, length=len(eth))


def extract_ipv4_data(eth):
    """
    Extracting general IPv4 data
    :param eth:
    :return:
    """
    ip_data = eth[ip.IP]
    if ip_data is None:
        return {}
    return dict(src=ip_data.src_s, dst=ip_data.dst_s, id=ip_data.id, qos=ip_data.tos)


def extract_ipv6_data(eth):
    """
    Extracting general IPv6 data
    :param eth:
    :return:
    """
    ip_data = eth[ip6.IP6]
    if ip_data is None:
        return {}
    return dict(src=ip_data.src_s, dst=ip_data.dst_s, id="0", qos="0")


def extract_icmp_data(eth):
    """
    Extracting general ICMP data
    :param eth:
    :return:
    """
    icmp_data = eth[icmpP.ICMP]
    if icmp_data is None:
        return {}
    return dict(src=icmp_data.type, dst=icmp_data.code)


def extract_icmp6_data(eth):
    """
    Extracting general ICMP data
    :param eth:
    :return:
    """
    icmp_data = eth[icmp6P.ICMP6]
    if icmp_data is None:
        return {}
    return dict(src=icmp_data.type, dst=icmp_data.code)


def extract_tcp_data(eth):
    """
    Extracting general TCP data from the TCP packet submitted through
    :param eth:
    :return:
    """
    tcp_packet = eth[tcpP.TCP]
    if tcp_packet is None:
        return {}
    push_flag = tcp_packet.flags & 0b1000 > 0
    return dict(header_len=tcp_packet.header_len, src=tcp_packet.sport, dst=tcp_packet.dport, seq=tcp_packet.seq,
                ack=tcp_packet.ack, flags=tcp_packet.flags_t if tcp_packet.flags_t != "" else "None",
                flags_i=tcp_packet.flags, push_flag=push_flag, body=tcp_packet.body_bytes,
                body_len=len(tcp_packet.body_bytes))


def extract_udp_data(eth):
    """
    Extracting general UDP data from the UDP packet submitted through
    :param eth:
    :return:
    """
    udp_data = eth[udpPCAP.UDP]
    if udp_data is None:
        return {}
    return dict(src=udp_data.sport, dst=udp_data.dport, id=int.from_bytes(udp_data.body_bytes[:4], "little"))


def main():
    """
    The main function to export PCAPs to CSV-based output
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("pcap")
    parser.add_argument("--profile")

    args = parser.parse_args()

    pcap = ppcap.Reader(args.pcap)

    stats = dict(stats_ipv4=0, stats_ipv6=0, stats_other=0, stats_ipv4_no_header=0, stats_tcp=0,
                 stats_udp=0, stats_icmp=0, stats_other_l4=0)

    if args.profile:
        stats["profile"] = cProfile.Profile()
        stats["profile"].enable()

    try:
        for timestamp, buf in pcap:
            xbuf, ipv4, ipv6, other, ipv4_no_header, tcp, udp, icmp, icmp6, other_l4 = extract_l4_protocols(buf)

            stats["stats_ipv4"] += ipv4
            stats["stats_ipv6"] += ipv6
            stats["stats_other"] += other
            stats["stats_ipv4_no_header"] += ipv4_no_header
            stats["stats_tcp"] += tcp
            stats["stats_udp"] += udp
            stats["stats_icmp"] += icmp
            stats["stats_other_l4"] += other_l4

            try:
                eth = ethernet.Ethernet(buf)
                if eth:
                    eth_data = extract_eth_data(eth)
                    ip_data = {}
                    if ipv4 == 1:
                        ip_data = extract_ipv4_data(eth)
                    elif ipv6 == 1:
                        ip_data = extract_ipv6_data(eth)

                    l4_data = {}
                    if tcp == 1:
                        l4_data = extract_tcp_data(eth)
                    elif udp == 1:
                        l4_data = extract_udp_data(eth)
                        ip_data["id"] = l4_data.get("id")
                    elif icmp == 1:
                        l4_data = extract_icmp_data(eth)
                    elif icmp6 == 1:
                        l4_data = extract_icmp6_data(eth)

                # pylint: disable=no-member
                # remove mac, since they cannot match in the VM setup
                eth = ethernet.Ethernet(buf)
                if "dst" in ip_data and "dst" in l4_data and udp == 1:
                    sys.stdout.buffer.write(b"%d\t\\\\%s\t\\\\%d\t\\\\%s\t\\\\%d\t\\\\%d\n" %
                                            (timestamp, bytes(str(ip_data.get("src")), encoding='utf8'),
                                             l4_data.get("src"), bytes(str(ip_data.get("dst")), encoding='utf8'),
                                             l4_data.get("dst"), ip_data.get("id")))
            except BrokenPipeError:
                logging.info("Broken Pipe (reader died?), exiting")
                break
    # suppress error when executing in python 3.7
    # changed behavior of StopIteration
    except RuntimeError:
        pass

    if stats.get("profile", None):
        stats["profile"].disable()
        stats["profile"].dump_stats(args.profile)

    logging.info("IPv4: %i [!options: %i] (TCP: %i, UDP: %i, ICMP: %i, other: %i), IPv6: %i, other: %i",
                 stats["stats_ipv4"], stats["stats_ipv4_no_header"], stats["stats_tcp"], stats["stats_udp"],
                 stats["stats_icmp"], stats["stats_other_l4"], stats["stats_ipv6"], stats["stats_other"])


if __name__ == "__main__":
    main()
