


def parse_line(line : str):

    # divide the line into ip, prefix length and next hop
    # '0.0.0.0/8\t1\n' ->  0.0.0.0 , 8, 1

    ip_plen, nhop = line.split()
    ip, plen = ip_plen.split('/')

    ip_parts = [int(x) for x in ip.split('.')]
    ip = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]

    return ip, int(plen), int(nhop)