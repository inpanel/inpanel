#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.
'''Module for file Management'''

import os.path
import shelve
import stat
from grp import getgrgid, getgrnam
from mimetypes import guess_type
from os import chmod as oschmod
from os import chown as oschown
from os import listdir as oslistdir
from os import lstat, mkdir, readlink
from os import rename as osrename
from os import stat as ostat
from os import symlink, walk
from pwd import getpwnam, getpwuid
from time import time
from uuid import uuid4

from server import ServerInfo
from utils import b2h, ftime

charsets = ('utf-8', 'gb2312', 'gbk', 'gb18030', 'big5', 'euc-jp', 'euc-kr',
            'iso-8859-2', 'shift_jis')


def listdir(path, showdotfiles=False, onlydir=None):
    path = os.path.abspath(path)
    if not os.path.exists(path) or not os.path.isdir(path):
        return False
    items = sorted(oslistdir(path))
    if not showdotfiles:
        items = [item for item in items if not item.startswith('.')]
    for i, item in enumerate(items):
        items[i] = getitem(os.path.join(path, item))
    # let folders list before files
    rt = []
    for i in range(len(items) - 1, -1, -1):
        if items[i]['isdir'] or items[i]['islnk'] and not items[i][
                'link_broken'] and items[i]['link_isdir']:
            rt.insert(0, items.pop(i))
    # check if only list directories
    if not onlydir:
        rt.extend(items)
    return rt


def listfile(directory):
    '''only list files of directory'''
    d = os.path.abspath(directory)
    if not os.path.exists(d) or not os.path.isdir(d):
        return None
    items = sorted(oslistdir(d))
    return items if len(items) > 0 else []


def getitem(path):
    if not os.path.exists(path) and not os.path.islink(path):
        return False
    name = os.path.basename(path)
    basepath = os.path.dirname(path)
    l_stat = lstat(path)
    mode = l_stat.st_mode
    try:
        uname = getpwuid(l_stat.st_uid).pw_name
    except:
        uname = ''
    try:
        gname = getgrgid(l_stat.st_gid).gr_name
    except:
        gname = ''
    item = {
        'name': name,
        'isdir': stat.S_ISDIR(mode),
        'ischr': stat.S_ISCHR(mode),
        'isblk': stat.S_ISBLK(mode),
        'isreg': stat.S_ISREG(mode),
        'isfifo': stat.S_ISFIFO(mode),
        'islnk': stat.S_ISLNK(mode),
        'issock': stat.S_ISSOCK(mode),
        'perms': oct(l_stat.st_mode)[-3:],  # '0100777' 最后三位
        'mode': mode,
        'filemode': stat.filemode(mode),
        'uid': l_stat.st_uid,
        'gid': l_stat.st_gid,
        'uname': uname,
        'gname': gname,
        'inode': l_stat.st_ino,
        'dev': l_stat.st_dev,
        'size': b2h(l_stat.st_size),
        'atime': ftime(l_stat.st_atime),
        'mtime': ftime(l_stat.st_mtime),
        'ctime': ftime(l_stat.st_ctime),
    }
    if item['islnk']:
        linkfile = readlink(path)
        item['linkto'] = linkfile
        if not linkfile.startswith('/'):
            linkfile = os.path.abspath(os.path.join(basepath, linkfile))
        try:
            mode = ostat(linkfile).st_mode
            item['link_isdir'] = stat.S_ISDIR(mode)
            item['link_isreg'] = stat.S_ISREG(mode)
            item['link_broken'] = False
        except:
            item['link_broken'] = True
    return item


def rename(oldpath, newname):
    # path = os.path.abspath(oldpath)
    if not os.path.exists(oldpath):
        return False
    try:
        basepath = os.path.dirname(oldpath)
        newpath = os.path.join(basepath, newname)
        osrename(oldpath, newpath)
        return True
    except:
        return False


def link(srcpath, despath):
    try:
        symlink(srcpath, despath)
        return True
    except:
        return False


def dadd(path, name):
    path = os.path.abspath(path)
    if not os.path.exists(path) or not os.path.isdir(path):
        return False
    dpath = os.path.join(path, name)
    if os.path.exists(dpath):
        return False
    try:
        mkdir(dpath)
        return True
    except:
        return False


def istext(filepath):
    mime = guess_type(filepath)[0]
    print('mime', mime)
    if mime is not None:
        return mime.startswith('text/') or mime.endswith(
            '/xml') or mime.endswith('json') or mime in (
                'application/javascript', 'application/vnd.apple.mpegurl',
                'application/x-x509-ca-cert', '.conf')
    if mime is None:
        suffix = os.path.splitext(filepath)[-1]
        print('suffix', suffix)
        return suffix in ('.txt', '.ini', '.js', '.mjs', '.json', '.m3u',
                          '.m3u8', '.tcl', '.eml', '.mht', '.mhtml', '.key')
    return False


def mimetype(filepath):
    if not os.path.exists(filepath):
        return False
    if os.path.islink(filepath):
        linkfile = readlink(filepath)
        if linkfile.startswith('/'):
            filepath = linkfile
        else:
            basepath = os.path.dirname(filepath)
            filepath = os.path.abspath(os.path.join(basepath, linkfile))
        if not os.path.exists(filepath):
            return False
    # mime = magic.from_file(filepath, mime=True)
    # # sometimes it still return like "text/plain; charset=us-ascii"
    # if ';' in mime:
    #     mime = mime.split(';', 1)[0]
    # if mime == 'text/plain':
    tmime = guess_type(filepath)[0]
    if tmime:
        return tmime
    # return mime


def fsize(filepath):
    if not os.path.exists(filepath):
        return None
    return lstat(filepath).st_size


def fadd(path, name):
    path = os.path.abspath(path)
    if not os.path.exists(path) or not os.path.isdir(path):
        return False
    fpath = os.path.join(path, name)
    if os.path.exists(fpath):
        return False
    try:
        with open(fpath, 'w', encoding='utf-8'):
            pass
        return True
    except:
        return False


def fsave(path, content, bakup=True):
    if not os.path.exists(path):
        return False
    try:
        if bakup:
            dname = os.path.dirname(path)
            filename = '.%s.bak' % os.path.basename(path)
            osrename(path, os.path.join(dname, filename))
        with open(path, 'wb') as f:
            f.write(content)
        return True
    except:
        return False


def decode(filepath):
    """Detect charset of content and decode it.
    """
    with open(filepath, 'rb') as file:
        content = file.read()
        for charset in charsets:
            try:
                return (charset, content.decode(charset))
            except:
                continue
    return (None, content)


def encode(content, charset):
    """Encode content using specified charset.
    """
    try:
        return content.encode(charset)
    except:
        return False


def delete(path):
    if not os.path.exists(path) and not os.path.islink(path):
        return False
    path = os.path.abspath(path)
    mounts = _getmounts()
    mount = ''
    for m in mounts:
        if path.startswith(m):
            mount = m
            break
    if not mount:
        return False
    trashpath = os.path.join(mount, '.deleted_files')
    _inittrash(mounts)
    try:
        uuid = str(uuid4())
        filename = os.path.basename(path)
        db = shelve.open(os.path.join(trashpath, '.fileinfo'), 'c')
        db[uuid] = '\t'.join([filename, path, str(int(time()))])

        osrename(path, os.path.join(trashpath, uuid))
        # deal with the .filename.bak
        dname = os.path.dirname(path)
        bakfilepath = os.path.join(dname, '.%s.bak' % filename)
        if os.path.exists(bakfilepath):
            return delete(bakfilepath)
        return True
    except:
        return False
    finally:
        db.close()


def _getmounts():
    mounts = ServerInfo.mounts()
    mounts = [mount['path'] for mount in mounts]
    # let the longest path at the first
    # mounts.sort(lambda x, y: cmp(len(y), len(x)))
    return sorted(mounts, key=lambda x: len(x), reverse=False)
    # return mounts


def _inittrash(mounts=None):
    # initialize the trash
    if not mounts:
        mounts = _getmounts()
    for mount in mounts:
        trashpath = os.path.join(mount, '.deleted_files')
        if not os.path.exists(trashpath):
            mkdir(trashpath)
            metafile = os.path.join(trashpath, '.fileinfo')
            shelve.open(metafile, 'c').close()


def trashs():
    """Return trash path list.
    """
    mounts = _getmounts()
    return [os.path.join(mount, '.deleted_files') for mount in mounts]


def tlist():
    mounts = _getmounts()
    _inittrash(mounts)
    # gather informations in each mount point's trash
    items = []
    for mount in mounts:
        trashfile = os.path.join(mount, '.deleted_files', '.fileinfo')
        with shelve.open(trashfile, 'c') as db:
            for uuid, info in db.items():
                fields = info.split('\t')
                item = {
                    'uuid': uuid,
                    'name': fields[0],
                    'path': fields[1],
                    'time': ftime(float(fields[2])),
                    'mount': mount
                }
                filepath = os.path.join(mount, '.deleted_files', uuid)
                if os.path.exists(filepath):
                    mode = ostat(filepath).st_mode
                    item['isdir'] = stat.S_ISDIR(mode)
                    item['isreg'] = stat.S_ISREG(mode)
                    item['islnk'] = stat.S_ISLNK(mode)
                items.append(item)
    # items.sort(lambda x, y: cmp(y['time'], x['time']))
    return items


def titem(mount, uuid):
    # _inittrash()
    try:
        trashpath = os.path.join(mount, '.deleted_files')
        db = shelve.open(os.path.join(trashpath, '.fileinfo'), 'c')
        info = db[uuid]
        db.close()
        fields = info.split('\t')
        info = {
            'uuid': uuid,
            'name': fields[0],
            'path': fields[1],
            'time': ftime(float(fields[2])),
            'mount': mount
        }
        info['originpath'] = os.path.join(trashpath, uuid)
        return info
    except:
        return False


def trestore(mount, uuid):
    # _inittrash()
    try:
        info = titem(mount, uuid)
        trashpath = os.path.join(mount, '.deleted_files')
        osrename(os.path.join(trashpath, uuid), info['path'])
        db = shelve.open(os.path.join(trashpath, '.fileinfo'), 'c')
        del db[uuid]
        db.close()
        return True
    except:
        return False


def tdelete(mount, uuid):
    # the real file or directory should be deleted external
    # _inittrash()
    try:
        db = shelve.open(os.path.join(mount, '.deleted_files', '.fileinfo'),
                         'c')
        del db[uuid]
        db.close()
        return True
    except:
        return False


def chown(path, user, group, recursively=False):
    if not os.path.exists(path) and not os.path.islink(path):
        return False
    try:
        userid = groupid = -1
        if user:
            userid = getpwnam(user).pw_uid
        if group:
            groupid = getgrnam(group).gr_gid
        if os.path.isdir(path) and recursively:
            for root, dirs, files in walk(path):
                for momo in dirs:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath):
                        continue  # maybe broken link
                    oschown(tpath, userid, groupid)
                for momo in files:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath):
                        continue
                    oschown(tpath, userid, groupid)
        oschown(path, userid, groupid)
    except:
        return False
    return True


def chmod(path, perms, recursively=False):
    if not os.path.exists(path) and not os.path.islink(path):
        return False
    try:
        if os.path.isdir(path) and recursively:
            for root, dirs, files in walk(path):
                for momo in dirs:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath):
                        continue  # maybe broken link
                    oschmod(tpath, perms)
                for momo in files:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath):
                        continue
                    oschmod(tpath, perms)
        oschmod(path, perms)
    except:
        return False
    return True


if __name__ == '__main__':
    print('* List directory of /Users:')
    path = '/Users'
    items = listdir(path)
    if items is not False:
        for item in items:
            print('  name: %s' % item['name'])
            print('  isdir: %s' % str(item['isdir']))
            # print('  isreg: %s' % str(item['isreg']))
            # print('  islnk: %s' % str(item['islnk']))
            # print('  perms: %s' % str(item['perms']))
            # print('  uname: %s' % item['uname'])
            # print('  gname: %s' % item['gname'])
            # print('  size: %s' % item['size'])
            # print('  atime: %s' % item['atime'])
            # print('  mtime: %s' % item['mtime'])
            # print('  ctime: %s' % item['ctime'])
            f = os.path.join(path, item['name'])
            # print(f)
            # # if mime == 'text/plain':
            # t = guess_type(f)[0]
            # print(t)
            # print(t.startswith('text'))
            print('  istext: %s' % str(istext(f)))
            # print('  mimetype: %s' % mimetype(f))
