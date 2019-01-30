# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 - 2019, doudoudzj
# Copyright (c) 2012 - 2016, VPSMate development team
# All rights reserved.
#
# Intranet is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

"""Module for reading and writing config file."""

import os


def raw_loadconfig(filepath, return_sort=False, delimiter='=', quoter=' "\'', overwrite=True):
    """Read config from file.
    """
    if not os.path.exists(filepath):
        return None
    config = {}
    if return_sort:
        sortlist = []
    with open(filepath) as f:
        for line in f:
            pair = line.strip().split(delimiter)
            if len(pair) != 2:
                continue
            k, v = [x.strip(quoter) for x in pair]
            if return_sort:
                sortlist.append(k)
            if overwrite:
                config[k] = v
            else:
                if not config.has_key(k):
                    config[k] = []
                config[k].append(v)
    if return_sort:
        return (config, sortlist)
    else:
        return config


def raw_saveconfig(filepath, config, sortlist=[], delimiter='=', quoter='"'):
    """Write config to file.
    """
    if not os.path.exists(filepath):
        return False
    lines = []

    # write the item in sortlist first
    if len(sortlist) > 0:
        for k in sortlist:
            if config.has_key(k):
                line = '%s%s%s%s%s\n' % (k, delimiter, quoter, config[k], quoter)
                del config[k]
                lines.append(line)

    # then write the rest items
    for k, v in config.iteritems():
        if isinstance(v, list):
            for vv in v:
                line = '%s%s%s%s%s\n' % (k, delimiter, quoter, vv, quoter)
                lines.append(line)
        else:
            line = '%s%s%s%s%s\n' % (k, delimiter, quoter, v, quoter)
            lines.append(line)

    with open(filepath, 'w') as f:
        f.writelines(lines)
    return True


def loadconfig(filepath, keymap=None, delimiter='=', quoter=' "\''):
    """Load config from file and parse it to dict.
    """
    raw_config = raw_loadconfig(filepath)
    # print(raw_config)
    if raw_config == None:
        return None
    if keymap == None:
        # return raw_config
        config = dict((k, v) for k, v in raw_config.iteritems())
    else:
        config = dict((keymap[k], v) for k, v in raw_config.iteritems() if keymap.has_key(k))
    return config


def saveconfig(filepath, config, keymap=None, delimiter='=', read_quoter=' "\'', write_quoter='"'):
    """Save config to file."""
    # current config
    raw_config, sortlist = raw_loadconfig(filepath, return_sort=True, delimiter=delimiter, quoter=read_quoter)
    if raw_config == None:
        return False
    for k, v in config.iteritems():
        if keymap == None:
            # Unspecified range of key-value pairs
            # Modify the specified field
            raw_config[k] = v
        else:
            # Specify a range of key-value pairs
            if keymap.has_key(k):
                raw_config[keymap[k]] = v
            else:
                return False
    return raw_saveconfig(filepath, raw_config, sortlist, delimiter=delimiter, quoter=write_quoter)


def readconfig(filepath, readfunc, **params):
    """Read config from file.
    """
    with open(filepath) as f:
        for line in f:
            rt = readfunc(line.strip(), **params)
            if rt != None:
                return rt


def writeconfig(filepath, readfunc, writefunc, **params):
    """Write config to file.
    """
    lines = []
    linemeet = False
    with open(filepath) as f:
        for line in f:
            rt = readfunc(line.strip(), **params)
            if rt != None:
                linemeet = True
                line = writefunc(line, **params)
                if line != None:
                    lines.append(line+'\n')
            else:
                lines.append(line)

    # generate a new line if no line meet
    if not linemeet:
        line = writefunc(None, **params)
        if line != None:
            lines.append(line+'\n')

    with open(filepath, 'w') as f:
        f.writelines(lines)
    return True
