#! /bin/env python

from __future__ import print_function

import sys
import re

def main():
    # print "args=", sys.argv
    # print "len=", len(sys.argv)

    # Get args without command name
    args = sys.argv[1:]

    if len(args) != 1:
        print("{}: convert certain holes in eagle-generated gerbers to slots".format(sys.argv[0]), file=sys.stderr)
        print("usage: {} diam".format(sys.argv[0]), file=sys.stderr)
        print("usage: {} diam,diam".format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    diams = args[0].split(',')
    assert 1 <= len(diams) <= 2
    special_diams = (float(diams[0]), float(diams[len(diams)-1]))
    # print("special_diams=", special_diams)
    # special_diams = (0.0394, 0.0394)
    special_tools = {}
    slot_coords = []

    state = 'pretooldefs'
    for line in sys.stdin.readlines():
        line = line.strip()
        assert len(line) > 0
        if state == 'pretooldefs':
            if line[0] == '%':
                state = 'intooldefs'
        elif state == 'intooldefs':
            # print("line[0]=", line[0])
            if line[0] == 'T':
                # matcher = re.match('T([0-9]+)C([0-9.]+)', line)
                matcher = re.match('T([0-9]+)C([0-9.]+)', line)
                assert matcher
                toolnum = matcher.group(1)
                tooldiam = matcher.group(2)
                # print("toolnum=", toolnum, "tooldiam=", tooldiam)
                tooldiam = float(tooldiam)
                # FIXME: Might need to tolerance this test for floating point error
                if special_diams[0] <= tooldiam <= special_diams[1]:
                    # print("this tool is special")
                    special_tools[toolnum] = tooldiam
            elif line[0] == '%':
                state = 'aftertooldefs'
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

