# trparse.js
JavaScript version forked from python module trparse: https://github.com/lbenitez000/trparse

Parses the output of a traceroute or traceroute6 execution into an AST
(Abstract Syntax Tree) returned as a object built up from:

-   a Traceroute root
-   Hop inner nodes
-   Probe leaf nodes

Supports the following info. Parsed info in bold:

- Header:
	- **Destination Hostname**
	- **(Destination IP address)**

- Hop
	- **Hop counter**
	- Probe
	    - **[AS\#]**
		- **Hostname**
		- **(IP address)**
		- **RTT**
		- **!Annotation**

The `-a` and `-n` traceroute flags are supported.

# Usage

```python
import trparse
s = "<some_output_from_traceroute>"
# Parse the traceroute output
traceroute = trparse.loads(s)
# You can print the result
print traceroute
# Save it as string
tr_str = str(traceroute) 
# Or travel the tree
hop = traceroute.hops[0]
probe = hop.probes[0]
# And print the IP address
print probe.ip
```

# Data structures - TBD

- Traceroute
	- dest_name :: \<str\>
	- dest_ip :: \<str\>
	- hops :: \<list\<Hop\>\>

- Hop
	- idx :: \<int\>
	- probes :: \<list\<Probe\>\>

- Probe
	- asn :: \<int\>
	- name :: \<str\>
	- ip :: \<str\>
	- rtt :: \<float\>
	- anno :: \<str\>

# Considerations

trparse is based on the output of the `traceroute` command in OSX and
Linux. It parses the text based on regular expressions, so there are
some tokens it expects to find in a specific format. For example:

-   **Destination Hostname** and **(Destination IP Address)** must be in
	the same line separated only by one or more space characters. They
	must be found in the header zone (typically the first two lines),
	before any hop result.
-   **(Destination IP Address)** must be surrounded by parenthesis
-   **Hop counter** must be the first token in its line. There can be
	lines starting with another token, but if there is a **Hop counter**
	in a line, it has to be the first token in that line. (can be
	preceded by space characters).
-   **[AS\#]** must be surrounded by square brackets `[]` and start with
	`AS` (AS numbers are output in `traceroute -a` commands).
-   **Hostname** can be a hostname or its IP address without parenthesis.
-   **(IP address)** either IPv4 or IPv6 must surrounded by parenthesis
	`()`.
    -    Hostname can be ommited (this happens in `traceroute -n`
         commands). In this case, IP address must NOT be surrounded by
         parenthesis.
-   **RTT** must be in integer (without commas or dots) or float format
	(with one (and only one) dot) separated from the `ms` literal by a
	least one space character.
-   **!Annotation** must start with a `!` symbol followed by non-space
	charachters and there can't be more than one per probe.

Windows's `tracert` output does not meet these conditions so it won't
work in a Widows system. Maybe in a future release.
