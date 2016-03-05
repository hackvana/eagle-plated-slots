#! /bin/env python

from __future__ import print_function

import sys
import re

def parse_pair(s):
    # Is there a - in there?  (- is interval marker)
    matcher = re.match('(.*)-(.*)', s)
    if matcher:
        # Yes, so try to parse the left and the right part as floats.
        lhs_s = matcher.group(1)
        rhs_s = matcher.group(2)
        # print('lhs_s=', lhs_s, 'rhs_s=', rhs_s)
        lhs = float(lhs_s)
        rhs = float(rhs_s)
        # print('lhs=', lhs, 'rhs=', rhs)
        return (lhs, rhs)
    lhs = float(s)
    return (lhs, lhs)

def main():
    # print("args=", sys.argv)
    # print("len=", len(sys.argv))

    # Get args without command name
    args = sys.argv[1:]

    if len(args) != 1:
        print("{}: convert certain holes in eagle-generated gerbers to slots".format(sys.argv[0]), file=sys.stderr)
        print("usage: {} diam".format(sys.argv[0]), file=sys.stderr)
        print("usage: {} diam,diam,diam1-diam2".format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    diam_pairs_s = args[0].split(',')
    assert len(diam_pairs_s) > 0
    diam_pairs = tuple(parse_pair(s) for s in diam_pairs_s)
    # print("diam_pairs=", diam_pairs)
    special_tools = {}
    slot_coords = []

    state = 'pretooldefs'
    for line in sys.stdin.readlines():
        line = line.strip()
        # print("state=", state, "line=", line)
        if line == "":
            continue
        if state == 'pretooldefs':
            if line[0] == '%' or line == "M48":
                state = 'intooldefs'
                # print("-> intooldefs")
        elif state == 'intooldefs':
            # print("line[0]=", line[0])
            if line[0] == 'T':
                # matcher = re.match('T([0-9]+)C([0-9.]+)', line)
                matcher = re.match('T([0-9]+)C([0-9.]+)', line)
                assert matcher, "Tool line '%s' didn't match a format we can accept" % line
                toolnum = matcher.group(1)
                tooldiam = matcher.group(2)
                # print("toolnum=", toolnum, "tooldiam=", tooldiam)
                tooldiam = float(tooldiam)
                # FIXME: Might need to tolerance this test for floating point error
                if any((p[0] <= tooldiam <= p[1] for p in diam_pairs)):
                    # print("this tool is special")
                    special_tools[toolnum] = tooldiam
            elif line[0] == '%':
                state = 'aftertooldefs'
                # print("-> aftertooldefs")
                toolnum = None
                saved_coord = None
                # print("special_tools=", special_tools)
        elif state == 'aftertooldefs':
            if line[0] == 'T':
                toolnum = line[1:]
                # print("toolnum=", toolnum)
            else:
                if line[0] != 'X':
                    # Non-coord line, such as M30 (end of program)
                    toolnum = None
                elif 'G85' in line:
                    pass # This line is already a G85 slot, so leave it alone.
                elif toolnum in special_tools:
                    # print("in special tool, saved_coord=", saved_coord)
                    if saved_coord is not None:
                        print("{}G85{}".format(saved_coord, line))
                        slot_coords.append((saved_coord, line))
                        saved_coord = None
                    else:
                        saved_coord = line
                    continue
        else:
            assert False, 'In unknown state %s' % state
        print(line)

    # print("slot_coords=", slot_coords)

if __name__ == "__main__":
    main()

