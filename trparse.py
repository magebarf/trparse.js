# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Luis Benitez

Parses the output of a traceroute execution into an AST (Abstract Syntax Tree).
"""

import re

RE_HEADER = re.compile(r'^traceroute to (\S+)\s+\((?:(\d+\.\d+\.\d+\.\d+)|([0-9a-fA-F:]+))\)')
RE_HOP = re.compile(r'^\s*(\d+)\s+([\s\S]+?(?=^\s*\d+\s+|^_EOS_))', re.M)

RE_PROBE_ASN = re.compile(r'^\[AS(\d+)\]$')
RE_PROBE_NAME = re.compile(r'^([a-zA-z0-9\.-]+)$|^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$|^([0-9a-fA-F:]+)$')
RE_PROBE_IP = re.compile(r'^\((\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[0-9a-fA-F:]+)\)$')
RE_PROBE_RTT = re.compile(r'^(\d+(?:\.?\d+)?)$')
RE_PROBE_ANNOTATION = re.compile(r'^(!\w*)$')
RE_PROBE_TIMEOUT = re.compile(r'^(\*)$')


class Traceroute(object):
    """
    Abstraction of a traceroute result.
    """
    def __init__(self, dest_name, dest_ip):
        self.dest_name = dest_name
        self.dest_ip = dest_ip
        self.hops = []

    def add_hop(self, hop):
        self.hops.append(hop)

    def __str__(self):
        text = "Traceroute for {0:s} ({1:s})\n\n".format(self.dest_name, self.dest_ip)
        for hop in self.hops:
            text += str(hop)
        return text


class Hop(object):
    """
    Abstraction of a hop in a traceroute.
    """
    def __init__(self, idx):
        self.idx = idx # Hop count, starting at 1 most of the times
        self.probes = [] # Series of Probe instances

    def add_probe(self, probe):
        """Adds a Probe instance to this hop's results."""
        if self.probes:
            probe_last = self.probes[-1]
            if not probe.ip and probe.rtt != None:
                probe.asn = probe_last.asn
                probe.ip = probe_last.ip
                probe.name = probe_last.name
        self.probes.append(probe)

    def __str__(self):
        text = "{0:>3d} ".format(self.idx)
        text_len = len(text)
        for n, probe in enumerate(self.probes):
            text_probe = str(probe)
            if n:
                text += (text_len*" ")+text_probe
            else:
                text += text_probe
        text += "\n"
        return text


class Probe(object):
    """
    Abstraction of a probe in a traceroute.
    """
    def __init__(self, asn=None, name=None, ip=None, rtt=None, anno=''):
        self.asn = asn # Autonomous System number
        self.name = name
        self.ip = ip
        self.rtt = rtt # RTT in ms
        self.anno = anno # Annotation, such as !H, !N, !X, etc

    def __str__(self):
        if self.rtt != None:
            text = ""
            if self.asn != None:
                text += "[AS{0:d}] ".format(self.asn)
            if self.name:
                text += "{0:s} ({1:s}) ".format(self.name, self.ip)
            else:
                text += "{0:s} ".format(self.ip)
            text += "{0:1.3f} ms".format(self.rtt)
            if self.anno:
                text += " {0:s}".format(self.anno)
            text += "\n"
        else:
            text = "*\n"
        return text


def loads(data):
    """Parser entry point. Parses the output of a traceroute execution"""
    data += "\n_EOS_" # Append EOS token. Helps to match last RE_HOP

    # Get header
    header_line = data.splitlines()[0]
    match_dest = RE_HEADER.match(header_line)
    if match_dest:
        dest_name = match_dest.group(1)
        dest_ip = match_dest.group(2)
    else:
        ext = "header_line: {0:s}".format(header_line)
        raise ParseError("Parse error \n{0:s}".format(ext))

    # The Traceroute is the root of the tree.
    traceroute = Traceroute(dest_name, dest_ip)

    # Get hops
    matches_hop = RE_HOP.findall(data)

    for match_hop in matches_hop:
        # Initialize a hop
        idx = int(match_hop[0])
        hop = Hop(idx)

        # For each hop parse probes
        # For this, iterate over all probe lines. Each line represents probes of the same
        # host (asn/name/ip).
        for probes_line in match_hop[1].splitlines():
            asn = None
            name = None
            ip = None

            # Parse probes data: [<asn>] | <name> | <(IP)> | <rtt> | 'ms' | '*'
            probes_data = probes_line.split()
            # Get rid of 'ms': [<asn>] | <name> | <(IP)> | <rtt> | '*'
            probes_data = list(filter(lambda s: s.lower() != 'ms', probes_data))

            i = 0
            while i < len(probes_data):
                rtt = None
                anno = ''

                # RTT check comes first because RE_PROBE_NAME can confuse rtt with an IP as name
                # The regex RE_PROBE_NAME can be improved
                if RE_PROBE_RTT.match(probes_data[i]):
                    # Matched rtt, so asn, name and IP have been parsed before
                    rtt = float(probes_data[i])
                    i += 1
                elif RE_PROBE_ASN.match(probes_data[i]):
                    # Matched a ASN, so next elements is name
                    asn = int(RE_PROBE_ASN.match(probes_data[i]).group(1))
                    print(asn)
                    i += 1
                    continue
                elif RE_PROBE_NAME.match(probes_data[i]):
                    # Matched a name, so next elements is expected to be an IP
                    name = probes_data[i]
                    i += 1
                    if RE_PROBE_IP.match(probes_data[i]):
                        ip = RE_PROBE_IP.match(probes_data[i]).group(1)
                        i += 1
                    else:
                        # Next element is not an IP. So 'name' actually is the IP.
                        ip = name
                        name = None
                    continue
                elif RE_PROBE_TIMEOUT.match(probes_data[i]):
                    # Its a timeout, so maybe asn, name and IP have been parsed before
                    # or maybe not. But it's Hop job to deal with it.
                    i += 1
                else:
                    ext = "i: {0:d}\nprobes_data: {1:s}\nasn: {2:s}\nname: {3:s}\nip: {4:s}\nrtt: {5:s}\nanno: {6:s}".format(
                            i, probes_data, asn, name, ip, rtt, anno)
                    raise ParseError("Parse error \n{0:s}".format(ext))
                # Check for annotation
                try:
                    if RE_PROBE_ANNOTATION.match(probes_data[i]):
                        anno = probes_data[i]
                        i += 1
                except IndexError:
                    pass

                probe = Probe(asn, name, ip, rtt, anno)
                hop.add_probe(probe)

        traceroute.add_hop(hop)

    return traceroute


def load(data):
    return loads(data.read())


class ParseError(Exception):
    pass
