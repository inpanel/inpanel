#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.
'''Module for file Management'''

import imghdr
import os
import shelve
import stat
from grp import getgrgid, getgrnam
from mimetypes import guess_type
from pwd import getpwnam, getpwuid
from time import time
from uuid import uuid4
from base import kernel_name

from server import ServerInfo
from utils import b2h, ftime

charsets = ('utf-8', 'gb2312', 'gbk', 'gb18030', 'big5', 'euc-jp', 'euc-kr',
            'iso-8859-2', 'shift_jis')


def web_handler(context):
    '''handler for web server'''
    action = context.get_argument('action', '')

    if action == 'last':
        lastdir = context.runlogs.get('file', 'lastdir')
        lastfile = context.runlogs.get('file', 'lastfile')
        context.write({'code': 0, 'msg': '', 'data': {'lastdir': lastdir, 'lastfile': lastfile}})

    elif action == 'listdir':
        path = context.get_argument('path', '')
        showhidden = context.get_argument('showhidden', 'off')
        remember = context.get_argument('remember', 'on')
        onlydir = context.get_argument('onlydir', 'off')
        items = listdir(path, showhidden=='on', onlydir=='on')
        if items is False:
            context.write({'code': -1, 'msg': f'目录 {path} 不存在！'})
        else:
            if remember == 'on':
                context.runlogs.set('file', 'lastdir', path)
            context.write({'code': 0, 'msg': '成功获取文件列表！', 'data': items})

    elif action == 'getitem':
        path = context.get_argument('path', '')
        item = getitem(path)
        if item is False:
            context.write({'code': -1, 'msg': f'{path} 不存在！'})
        else:
            context.write({'code': 0, 'msg': f'成功获取 {path} 的信息！', 'data': item})

    elif action == 'fread':
        path = context.get_argument('path', '')
        remember = context.get_argument('remember', 'on')
        size = fsize(path)
        if size is None:
            context.write({'code': -1, 'msg': f'文件 {path} 不存在！'})
        elif size > 1024*1024*2: # support 1MB of file at max
            context.write({'code': -1, 'msg': f'读取 {path} 失败！不允许在线编辑超过2MB的文件！'})
        # elif not mod_file.istext(path):
        #     context.write({'code': -1, 'msg': f'读取 {path} 失败！无法识别文件类型 ！'})
        else:
            if remember == 'on':
                context.runlogs.set('file', 'lastfile', path)
            charset, content = decode(path)
            if not charset:
                context.write({'code': -1, 'msg': '不可识别的文件编码 ！'})
                return
            data = {
                'filename': os.path.basename(path),
                'filepath': path,
                'mimetype': mimetype(path),
                'charset': charset,
                'content': content,
            }
            context.write({'code': 0, 'msg': '成功读取文件内容 ！', 'data': data})

    elif action == 'fclose':
        context.runlogs.set('file', 'lastfile', '')
        context.write({'code': 0, 'msg': ''})

    elif action == 'fwrite':
        path = context.get_argument('path', '')
        charset = context.get_argument('charset', '')
        content = context.get_argument('content', '')

        if context.config.get('runtime', 'mode') == 'demo':
            if not path.startswith('/var/www'):
                context.write({'code': -1, 'msg': '演示模式不允许修改除 /var/www 以外的目录！'})
                return

        if not charset in charsets:
            context.write({'code': -1, 'msg': '不可识别的文件编码！'})
            return
        content = encode(content, charset)
        if not content:
            context.write({'code': -1, 'msg': '文件编码转换出错，保存失败！'})
            return
        if fsave(path, content):
            context.write({'code': 0, 'msg': '文件保存成功！'})
        else:
            context.write({'code': -1, 'msg': '文件保存失败！'})

    elif action == 'createfolder':
        path = context.get_argument('path', '')
        name = context.get_argument('name', '')

        if context.config.get('runtime', 'mode') == 'demo':
            if not path.startswith('/var/www') and not path.startswith(context.settings['package_path']):
                context.write({'code': -1, 'msg': '演示模式不允许修改除 /var/www 以外的目录！'})
                return

        if dadd(path, name):
            context.write({'code': 0, 'msg': '文件夹创建成功！'})
        else:
            context.write({'code': -1, 'msg': '文件夹创建失败！'})

    elif action == 'createfile':
        path = context.get_argument('path', '')
        name = context.get_argument('name', '')

        if context.config.get('runtime', 'mode') == 'demo':
            if not path.startswith('/var/www'):
                context.write({'code': -1, 'msg': '演示模式不允许修改除 /var/www 以外的目录！'})
                return

        if fadd(path, name):
            context.write({'code': 0, 'msg': '文件创建成功！'})
        else:
            context.write({'code': -1, 'msg': '文件创建失败！'})

    elif action == 'rename':
        path = context.get_argument('path', '')
        name = context.get_argument('name', '')

        if context.config.get('runtime', 'mode') == 'demo':
            if not path.startswith('/var/www'):
                context.write({'code': -1, 'msg': '演示模式不允许修改除 /var/www 以外的目录！'})
                return

        if rename(path, name):
            context.write({'code': 0, 'msg': '重命名成功！'})
        else:
            context.write({'code': -1, 'msg': '重命名失败！'})

    elif action == 'exist':
        path = context.get_argument('path', '')
        name = context.get_argument('name', '')
        context.write({'code': 0, 'msg': '', 'data': os.path.exists(os.path.join(path, name))})

    elif action == 'link':
        srcpath = context.get_argument('srcpath', '')
        despath = context.get_argument('despath', '')

        if context.config.get('runtime', 'mode') == 'demo':
            if not despath.startswith('/var/www') and not despath.startswith(context.settings['package_path']):
                context.write({'code': -1, 'msg': '演示模式不允许在除 /var/www 以外的目录下创建链接！'})
                return

        if link(srcpath, despath):
            context.write({'code': 0, 'msg': f'链接 {despath} 创建成功 ！'})
        else:
            context.write({'code': -1, 'msg': f'链接 {despath} 创建失败 ！'})

    elif action == 'delete':
        paths = context.get_argument('paths', '')
        paths = paths.split(',')

        if context.config.get('runtime', 'mode') == 'demo':
            for path in paths:
                if not path.startswith('/var/www') and not path.startswith(context.settings['package_path']):
                    context.write({'code': -1, 'msg': '演示模式不允许在除 /var/www 以外的目录执行删除操作！'})
                    return

        if len(paths) == 1:
            path = paths[0]
            if delete(path):
                context.write({'code': 0, 'msg': f'已将 {path} 移入回收站 ！'})
            else:
                context.write({'code': -1, 'msg': f'将 {path} 移入回收站失败 ！'})
        else:
            for path in paths:
                if not delete(path):
                    context.write({'code': -1, 'msg': f'将 {path} 移入回收站失败 ！'})
                    return
            context.write({'code': 0, 'msg': '批量移入回收站成功！'})

    elif action == 'tlist':
        context.write({'code': 0, 'msg': '', 'data': tlist()})

    elif action == 'trashs':
        context.write({'code': 0, 'msg': '', 'data': trashs()})

    elif action == 'titem':
        mount = context.get_argument('mount', '')
        uuid = context.get_argument('uuid', '')
        info = titem(mount, uuid)
        if info:
            context.write({'code': 0, 'msg': '', 'data': info})
        else:
            context.write({'code': -1, 'msg': '获取项目信息失败！'})

    elif action == 'trestore':
        mount = context.get_argument('mount', '')
        uuid = context.get_argument('uuid', '')
        info = titem(mount, uuid)
        if info and trestore(mount, uuid):
            context.write({'code': 0, 'msg': f'已还原 {info["name"]} 到 {info["path"]} ！'})
        else:
            context.write({'code': -1, 'msg': '还原失败！'})

    elif action == 'tdelete':
        mount = context.get_argument('mount', '')
        uuid = context.get_argument('uuid', '')
        info = titem(mount, uuid)
        if info and tdelete(mount, uuid):
            context.write({'code': 0, 'msg': f'已删除 {info["name"]} ！'})
        else:
            context.write({'code': -1, 'msg': '删除失败！'})


def listdir(path, showdotfiles=False, onlydir=None):
    '''list folders (and files)'''
    path = os.path.abspath(path)
    if not os.path.exists(path) or not os.path.isdir(path):
        return False
    items = sorted(os.listdir(path))
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
    items = sorted(os.listdir(d))
    return items if len(items) > 0 else []


def getitem(path):
    '''get file stat'''
    if not os.path.exists(path) and not os.path.islink(path):
        return False
    name = os.path.basename(path)
    basepath = os.path.dirname(path)
    l_stat = os.lstat(path)
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
    if not item['isdir']:
        item['is_image'] = is_image(path)
    if item['islnk']:
        linkfile = os.readlink(path)
        item['linkto'] = linkfile
        if not linkfile.startswith('/'):
            linkfile = os.path.abspath(os.path.join(basepath, linkfile))
        try:
            mode = os.stat(linkfile).st_mode
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
        os.rename(oldpath, newpath)
        return True
    except:
        return False


def link(srcpath, despath):
    try:
        os.symlink(srcpath, despath)
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
        os.mkdir(dpath)
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

def is_image(filepath):
    if not os.path.exists(filepath):
        return False
    if os.path.isdir(filepath):
        return False
    suffix = imghdr.what(filepath)
    return suffix in ('rgb', 'gif', 'jpg', 'jpeg', 'png', 'bmp', 'webp')


def mimetype(filepath):
    if not os.path.exists(filepath):
        return False
    if os.path.islink(filepath):
        linkfile = os.readlink(filepath)
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
    return os.lstat(filepath).st_size


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
            os.rename(path, os.path.join(dname, filename))
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
    '''Move files to the Recycle Bin'''
    if not os.path.exists(path) and not os.path.islink(path):
        return False
    path = os.path.abspath(path)
    mounts = _getmounts()
    if kernel_name == 'Darwin':
        trashpath = os.path.join(os.path.expanduser('~'), '.deleted_files')
    else:
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

        os.rename(path, os.path.join(trashpath, uuid))
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
    if kernel_name == 'Darwin':
        return [os.path.expanduser('~')]
    else:
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
            os.mkdir(trashpath)
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
                    mode = os.stat(filepath).st_mode
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
        os.rename(os.path.join(trashpath, uuid), info['path'])
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
        db = shelve.open(os.path.join(mount, '.deleted_files', '.fileinfo'), 'c')
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
            for root, dirs, files in os.walk(path):
                for momo in dirs:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath):
                        continue  # maybe broken link
                    os.chown(tpath, userid, groupid)
                for momo in files:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath):
                        continue
                    os.chown(tpath, userid, groupid)
        os.chown(path, userid, groupid)
    except:
        return False
    return True


def chmod(path, perms, recursively=False):
    if not os.path.exists(path) and not os.path.islink(path):
        return False
    try:
        if os.path.isdir(path) and recursively:
            for root, dirs, files in os.walk(path):
                for momo in dirs:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath):
                        continue  # maybe broken link
                    os.chmod(tpath, perms)
                for momo in files:
                    tpath = os.path.join(root, momo)
                    if not os.path.exists(tpath):
                        continue
                    os.chmod(tpath, perms)
        os.chmod(path, perms)
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
