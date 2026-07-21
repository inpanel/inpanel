#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.
'''文件管理模块'''

import os
import shelve
import stat
from grp import getgrgid, getgrnam
from mimetypes import guess_type
from pathlib import Path
from pwd import getpwnam, getpwuid
from time import time
from uuid import uuid4
from ..base import kernel_name, history_path, os_name

try:
    import imghdr
except ImportError:
    class imghdr:
        @staticmethod
        def what(filepath):
            try:
                from PIL import Image
                with Image.open(filepath) as img:
                    return img.format.lower()
            except ImportError:
                pass
            return None

from . import server
from ..utils import b2h, ftime

charsets = ('utf-8', 'gb2312', 'gbk', 'gb18030', 'big5', 'euc-jp', 'euc-kr',
            'iso-8859-2', 'shift_jis')


def safe_shelve_open(filename, flag='c'):
    try:
        return shelve.open(filename, flag)
    except Exception:
        from dbm import error as dbm_error
        try:
            Path(filename).unlink(missing_ok=True)
            db_files = Path(filename).parent.glob(filename + '.*')
            for f in db_files:
                f.unlink(missing_ok=True)
        except:
            pass
        return shelve.open(filename, 'n')


def get_default_bookmarks():
    '''Return system-specific default bookmarks'''
    bookmarks = []
    if kernel_name == 'Darwin':
        bookmarks = [
            {'type': 'dir', 'path': '/Users', 'desc': '用户目录'},
            {'type': 'dir', 'path': '/Applications', 'desc': '应用程序目录'},
            {'type': 'dir', 'path': '/etc', 'desc': '系统配置目录'},
            {'type': 'dir', 'path': '/usr/local/etc', 'desc': '本地配置目录'},
            {'type': 'dir', 'path': '/etc/inpanel', 'desc': 'InPanel配置'},
        ]
    elif kernel_name == 'Linux':
        bookmarks = [
            {'type': 'dir', 'path': '/home', 'desc': '用户目录'},
            {'type': 'dir', 'path': '/var/www', 'desc': '站点目录'},
            {'type': 'dir', 'path': '/etc', 'desc': '配置目录'},
            {'type': 'dir', 'path': '/etc/nginx', 'desc': 'Nginx配置'},
            {'type': 'dir', 'path': '/etc/inpanel', 'desc': 'InPanel配置'},
        ]
    else:
        bookmarks = [
            {'type': 'dir', 'path': str(Path.home()), 'desc': '用户目录'},
            {'type': 'dir', 'path': '/etc', 'desc': '配置目录'},
            {'type': 'dir', 'path': '/etc/inpanel', 'desc': 'InPanel配置'},
        ]
    return bookmarks


def web_handler(context):
    '''handler for web server'''
    action = context.get_argument('action', '')

    if action == 'last':
        lastdir = context.lastfile.get('file', 'lastdir')
        lastfile = context.lastfile.get('file', 'lastfile')
        context.write({'code': 0, 'msg': '', 'data': {'lastdir': lastdir, 'lastfile': lastfile}})

    elif action == 'bookmarks':
        from .config import bookmarks_config
        bookmarks_cfg = bookmarks_config()
        sections = bookmarks_cfg.get_section_list()
        if sections:
            bookmarks = []
            for section in sections:
                bookmarks.append({
                    'type': bookmarks_cfg.get(section, 'type', 'dir'),
                    'path': section,
                    'desc': bookmarks_cfg.get(section, 'desc', ''),
                })
            context.write({'code': 0, 'msg': '', 'data': bookmarks})
        else:
            context.write({'code': 0, 'msg': '', 'data': get_default_bookmarks()})

    elif action == 'save_bookmarks':
        from .config import bookmarks_config
        bookmarks = context.get_argument('bookmarks', '')
        try:
            import json
            bookmarks = json.loads(bookmarks)
            bookmarks_cfg = bookmarks_config()
            for section in bookmarks_cfg.get_section_list():
                bookmarks_cfg.remove_section(section)
            for item in bookmarks:
                bookmarks_cfg.addsection(item['path'], {
                    'type': item.get('type', 'dir'),
                    'desc': item.get('desc', ''),
                })
            context.write({'code': 0, 'msg': '常用目录保存成功！'})
        except:
            context.write({'code': -1, 'msg': '常用目录保存失败！'})

    elif action == 'add_bookmark':
        from .config import bookmarks_config
        path = context.get_argument('path', '')
        desc = context.get_argument('desc', '')
        item_type = context.get_argument('type', 'dir')
        if not path:
            context.write({'code': -1, 'msg': '路径不能为空！'})
            return
        try:
            bookmarks_cfg = bookmarks_config()
            bookmarks_cfg.addsection(path, {
                'type': item_type,
                'desc': desc if desc else path.split('/')[-1] if path != '/' else '根目录',
            })
            context.write({'code': 0, 'msg': '已添加到常用目录！'})
        except:
            context.write({'code': -1, 'msg': '添加常用目录失败！'})

    elif action == 'remove_bookmark':
        from .config import bookmarks_config
        path = context.get_argument('path', '')
        if not path:
            context.write({'code': -1, 'msg': '路径不能为空！'})
            return
        try:
            bookmarks_cfg = bookmarks_config()
            bookmarks_cfg.remove_section(path)
            bookmarks_cfg.update()
            context.write({'code': 0, 'msg': '已从常用目录移除！'})
        except:
            context.write({'code': -1, 'msg': '移除常用目录失败！'})

    elif action == 'history':
        paths = []
        if Path(history_path).exists():
            with open(history_path, 'r', encoding='utf-8') as f:
                paths = [line.strip() for line in f.readlines() if line.strip()]
        context.write({'code': 0, 'msg': '', 'data': paths})

    elif action == 'add_history':
        path = context.get_argument('path', '')
        if not path:
            context.write({'code': -1, 'msg': '路径不能为空！'})
            return
        
        paths = []
        if Path(history_path).exists():
            with open(history_path, 'r', encoding='utf-8') as f:
                paths = [line.strip() for line in f.readlines() if line.strip()]
        
        if path in paths:
            paths.remove(path)
        paths.insert(0, path)
        
        if len(paths) > 30:
            paths = paths[:30]
        
        Path(history_path).parent.mkdir(parents=True, exist_ok=True)
        with open(history_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(paths))
        
        context.write({'code': 0, 'msg': '', 'data': paths})

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
                context.lastfile.set('file', 'lastdir', path)
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
                context.lastfile.set('file', 'lastfile', path)
            charset, content = decode(path)
            if not charset:
                context.write({'code': -1, 'msg': '不可识别的文件编码 ！'})
                return
            data = {
                'filename': str(Path(path).name),
                'filepath': path,
                'mimetype': mimetype(path),
                'charset': charset,
                'content': content,
            }
            context.write({'code': 0, 'msg': '成功读取文件内容 ！', 'data': data})

    elif action == 'fclose':
        context.lastfile.set('file', 'lastfile', '')
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
        context.write({'code': 0, 'msg': '', 'data': str(Path(path) / name)})

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
                context.write({'code': 0, 'msg': f'已将 {path} 移入回收站'})
            else:
                context.write({'code': -1, 'msg': f'将 {path} 移入回收站失败'})
        else:
            for path in paths:
                if not delete(path):
                    context.write({'code': -1, 'msg': f'将 {path} 移入回收站失败'})
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
    path = str(Path(path))
    if not Path(path).exists() or not Path(path).is_dir():
        return False
    items = sorted(os.listdir(path))
    if not showdotfiles:
        items = [item for item in items if not item.startswith('.')]
    for i, item in enumerate(items):
        items[i] = getitem(str(Path(path) / item))
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
    d = str(Path(directory))
    if not Path(d).exists() or not Path(d).is_dir():
        return None
    items = sorted(os.listdir(d))
    return items if len(items) > 0 else []


def getitem(path):
    '''get file stat'''
    if not Path(path).exists() and not Path(path).is_symlink():
        return False
    name = Path(path).name
    basepath = str(Path(path).parent)
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
            linkfile = str(Path(basepath) / linkfile)
        try:
            mode = os.stat(linkfile).st_mode
            item['link_isdir'] = stat.S_ISDIR(mode)
            item['link_isreg'] = stat.S_ISREG(mode)
            item['link_broken'] = False
        except:
            item['link_broken'] = True
    return item


def rename(oldpath, newname):
    # path = str(Path(oldpath)
    if not Path(oldpath).exists():
        return False
    try:
        basepath = str(Path(oldpath).parent)
        newpath = str(Path(basepath) / newname)
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
    path = str(Path(path))
    if not Path(path).exists() or not Path(path).is_dir():
        return False
    dpath = str(Path(path) / name)
    if Path(dpath).exists():
        return False
    try:
        Path(dpath).mkdir(parents=True, exist_ok=True)
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
        suffix = Path(filepath).suffix
        print('suffix', suffix)
        return suffix in ('.txt', '.ini', '.js', '.mjs', '.json', '.m3u',
                          '.m3u8', '.tcl', '.eml', '.mht', '.mhtml', '.key')
    return False

def is_image(filepath):
    if not Path(filepath).exists():
        return False
    if Path(filepath).is_dir():
        return False
    suffix = imghdr.what(filepath)
    return suffix in ('rgb', 'gif', 'jpg', 'jpeg', 'png', 'bmp', 'webp')


def mimetype(filepath):
    if not Path(filepath).exists():
        return False
    if Path(filepath).is_symlink():
        linkfile = os.readlink(filepath)
        if linkfile.startswith('/'):
            filepath = linkfile
        else:
            basepath = str(Path(filepath).parent)
            filepath = str(Path(basepath) / linkfile)
        if not Path(filepath).exists():
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
    if not Path(filepath).is_file():
        return None
    return os.lstat(filepath).st_size


def fadd(path, name):
    path = str(Path(path))
    if not Path(path).exists() or not Path(path).is_dir():
        return False
    fpath = str(Path(path) / name)
    if Path(fpath).exists():
        return False
    try:
        with open(fpath, 'w', encoding='utf-8'):
            pass
        return True
    except:
        return False


def fsave(path, content, bakup=True):
    if not Path(path).exists():
        return False
    try:
        if bakup:
            dname = str(Path(path).parent)
            filename = '.%s.bak' % Path(path).name
            os.rename(path, str(Path(dname) / filename))
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
    if not Path(path).exists():
        return False
    path = str(Path(path))
    mounts = _getmounts()
    if kernel_name == 'Darwin':
        trashpath = str(Path.home() / '.deleted_files')
    else:
        mount = ''
        for m in mounts:
            if path.startswith(m):
                mount = m
                break
        if not mount:
            return False
        trashpath = str(Path(mount) / '.deleted_files')
    _inittrash(mounts)
    try:
        uuid = str(uuid4())
        filename = Path(path).name
        with safe_shelve_open(str(Path(trashpath) / '.fileinfo'), 'c') as db:
            db[uuid] = '\t'.join([filename, path, str(int(time()))])

        os.rename(path, str(Path(trashpath) / uuid))
        dname = str(Path(path).parent)
        bakfilepath = str(Path(dname) / ('.%s.bak' % filename))
        if Path(bakfilepath).exists():
            return delete(bakfilepath)
        return True
    except:
        return False


def _getmounts():
    if kernel_name == 'Darwin':
        return [str(Path.home())]
    else:
        mounts = server.ServerInfo.mounts()
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
        trashpath = str(Path(mount) / '.deleted_files')
        if not Path(trashpath).exists():
            Path(trashpath).mkdir(parents=True, exist_ok=True)
            metafile = str(Path(trashpath) / '.fileinfo')
            safe_shelve_open(metafile, 'c').close()


def trashs():
    """Return trash path list.
    """
    mounts = _getmounts()
    return [str(Path(mount) / '.deleted_files') for mount in mounts]


def tlist():
    mounts = _getmounts()
    _inittrash(mounts)
    # gather informations in each mount point's trash
    items = []
    for mount in mounts:
        trashfile = str(Path(mount) / '.deleted_files' / '.fileinfo')
        with safe_shelve_open(trashfile, 'c') as db:
            for uuid, info in db.items():
                fields = info.split('\t')
                item = {
                    'uuid': uuid,
                    'name': fields[0],
                    'path': fields[1],
                    'time': ftime(float(fields[2])),
                    'mount': mount
                }
                filepath = str(Path(mount) / '.deleted_files' / uuid)
                if Path(filepath).exists():
                    mode = os.stat(filepath).st_mode
                    item['isdir'] = stat.S_ISDIR(mode)
                    item['isreg'] = stat.S_ISREG(mode)
                    item['islnk'] = stat.S_ISLNK(mode)
                items.append(item)
    # items.sort(lambda x, y: cmp(y['time'], x['time']))
    return items


def titem(mount, uuid):
    try:
        trashpath = str(Path(mount) / '.deleted_files')
        with safe_shelve_open(str(Path(trashpath) / '.fileinfo'), 'c') as db:
            info = db[uuid]
        fields = info.split('\t')
        info = {
            'uuid': uuid,
            'name': fields[0],
            'path': fields[1],
            'time': ftime(float(fields[2])),
            'mount': mount
        }
        info['originpath'] = str(Path(trashpath) / uuid)
        return info
    except:
        return False


def trestore(mount, uuid):
    try:
        info = titem(mount, uuid)
        trashpath = str(Path(mount) / '.deleted_files')
        os.rename(str(Path(trashpath) / uuid), info['path'])
        with safe_shelve_open(str(Path(trashpath) / '.fileinfo'), 'c') as db:
            del db[uuid]
        return True
    except:
        return False


def tdelete(mount, uuid):
    try:
        with safe_shelve_open(str(Path(mount) / '.deleted_files' / '.fileinfo'), 'c') as db:
            del db[uuid]
        return True
    except:
        return False


def chown(path, user, group, recursively=False):
    if not Path(path).exists():
        return False
    try:
        userid = groupid = -1
        if user:
            userid = getpwnam(user).pw_uid
        if group:
            groupid = getgrnam(group).gr_gid
        if Path(path).exists() and recursively:
                for root, dirs, files in os.walk(path):
                    for momo in dirs:
                        tpath = str(Path(root) / momo)
                        if not Path(tpath).exists():
                            continue  # maybe broken link
                        os.chown(tpath, userid, groupid)
                    for momo in files:
                        tpath = str(Path(root) / momo)
                        if not Path(tpath).exists():
                            continue
                        os.chown(tpath, userid, groupid)
        os.chown(path, userid, groupid)
    except:
        return False
    return True


def chmod(path, perms, recursively=False):
    if not Path(path).exists():
        return False
    try:
        if Path(path).exists() and recursively:
            for root, dirs, files in os.walk(path):
                for momo in dirs:
                    tpath = str(Path(root) / momo)
                    if not Path(tpath).exists():
                        continue  # maybe broken link
                    os.chmod(tpath, perms)
                for momo in files:
                    tpath = str(Path(root) / momo)
                    if not Path(tpath).exists():
                        continue
                    os.chmod(tpath, perms)
        os.chmod(path, perms)
    except:
        return False
    return True


# ------------------------------------------------------------------
# 异步任务函数（由 web.py 的 _dispatch_task 调用）
# 命名规则：file_<method>，对应 jobname 中的 file_<method>_...
# ------------------------------------------------------------------

from shlex import quote as sh_quote
from . import shell


async def file_copy(tm, srcpath, despath):
    """复制文件/目录（异步任务）"""
    jobname = f'file.copy_{srcpath}_{despath}'
    if not tm._start_job(jobname):
        return
    tm._update_job(jobname, 2, f'正在复制 {srcpath} 到 {despath}...')

    cmd = f'cp -rf {sh_quote(srcpath)} {sh_quote(despath)}'
    result, output = await shell.async_command(cmd)

    if result == 0:
        tm._finish_job(jobname, 0, f'复制 {srcpath} 到 {despath} 完成！')
    else:
        tm._finish_job(jobname, -1,
                       f'复制 {srcpath} 到 {despath} 失败！',
                       data=output.strip().replace('\n', '<br>'))


async def file_move(tm, srcpath, despath):
    """移动文件/目录（异步任务）"""
    jobname = f'file.move_{srcpath}_{despath}'
    if not tm._start_job(jobname):
        return
    tm._update_job(jobname, 2, f'正在移动 {srcpath} 到 {despath}...')

    despath_exists = Path(despath).exists()
    if despath_exists:
        if not Path(srcpath).exists():
            tm._finish_job(jobname, -1, '不可识别的源！')
            return
        cmd = f'cp -rf {sh_quote(srcpath)}/* {sh_quote(despath)}'
    else:
        cmd = f'mv {sh_quote(srcpath)} {sh_quote(despath)}'

    result, output = await shell.async_command(cmd)
    data = None
    if result == 0:
        code = 0
        msg = f'移动 {srcpath} 到 {despath} 完成！'
    else:
        code = -1
        msg = f'移动 {srcpath} 到 {despath} 失败！'
        data = output.strip().replace('\n', '<br>')

    if despath_exists and code == 0:
        result2, output2 = await shell.async_command(f'rm -rf {sh_quote(srcpath)}')
        if result2 != 0:
            code = -1
            msg = f'移动 {srcpath} 到 {despath} 失败！'
            data = output2.strip().replace('\n', '<br>')

    tm._finish_job(jobname, code, msg, data=data)


async def file_remove(tm, paths):
    """删除文件/目录（异步任务）"""
    if isinstance(paths, str):
        paths = paths.split(',')
    jobname = f'file.remove_{",".join(paths)}'
    if not tm._start_job(jobname):
        return
    data = None
    for path in paths:
        tm._update_job(jobname, 2, f'正在删除 {path}...')
        cmd = f'rm -rf {sh_quote(path)}'
        result, output = await shell.async_command(cmd)
        if result == 0:
            code = 0
            msg = f'删除 {path} 成功！'
        else:
            code = -1
            msg = f'删除 {path} 失败！'
            data = output.strip().replace('\n', '<br>')
    tm._finish_job(jobname, code, msg, data=data)


async def file_compress(tm, zippath, paths):
    """压缩文件/目录（异步任务）"""
    if isinstance(paths, str):
        paths = paths.split(',')
    jobname = f'file.compress_{zippath}_{",".join(paths)}'
    if not tm._start_job(jobname):
        return
    tm._update_job(jobname, 2, f'正在压缩生成 {zippath}...')

    basepath = str(Path(zippath).parent) + '/'
    path = ' '.join([sh_quote(item.replace(basepath, '')) for item in paths])
    if zippath.endswith('.tar.gz') or zippath.endswith('.tgz'):
        cmd = f'tar zcf {sh_quote(zippath)} -C {sh_quote(basepath)} {path}'
    elif zippath.endswith('.tar.bz2'):
        cmd = f'tar jcf {sh_quote(zippath)} -C {sh_quote(basepath)} {path}'
    elif zippath.endswith('.zip'):
        if not Path('/usr/bin/zip').exists():
            tm._update_job(jobname, 2, '正在安装 zip...')
            result, _ = await shell.async_command('yum install -y zip unzip')
            if result != 0:
                tm._finish_job(jobname, -1, 'zip 安装失败！')
                return
        cmd = f'cd {sh_quote(basepath)}; zip -rq9 {sh_quote(zippath)} {path}'
    elif zippath.endswith('.gz'):
        path = ' '.join([sh_quote(item) for item in paths])
        cmd = f'gzip -f {path}'
    else:
        tm._finish_job(jobname, -1, '不支持的类型！')
        return

    result, output = await shell.async_command(cmd)
    if result == 0:
        tm._finish_job(jobname, 0, f'压缩到 {zippath} 成功！')
    else:
        tm._finish_job(jobname, -1, '压缩失败！',
                       data=output.strip().replace('\n', '<br>'))


async def file_decompress(tm, zippath, despath=''):
    """解压文件（异步任务）"""
    jobname = f'file.decompress_{zippath}_{despath}'
    if not tm._start_job(jobname):
        return
    tm._update_job(jobname, 2, f'正在解压 {zippath}...')

    if zippath.endswith('.tar.gz') or zippath.endswith('.tgz'):
        cmd = f'tar zxf {sh_quote(zippath)} -C {sh_quote(despath)}'
    elif zippath.endswith('.tar.bz2'):
        cmd = f'tar jxf {sh_quote(zippath)} -C {sh_quote(despath)}'
    elif zippath.endswith('.zip'):
        if not Path('/usr/bin/unzip').is_file():
            tm._update_job(jobname, 2, '正在安装 unzip...')
            result, _ = await shell.async_command('yum install -y zip unzip')
            if result != 0:
                tm._finish_job(jobname, -1, 'unzip 安装失败！')
                return
        cmd = f'unzip -q -o {sh_quote(zippath)} -d {sh_quote(despath)}'
    elif zippath.endswith('.gz'):
        cmd = f'gunzip -f {sh_quote(zippath)}'
    else:
        tm._finish_job(jobname, -1, '不支持的类型！')
        return

    result, output = await shell.async_command(cmd)
    if result == 0:
        tm._finish_job(jobname, 0, f'解压 {zippath} 成功！')
    else:
        tm._finish_job(jobname, -1, f'解压 {zippath} 失败！',
                       data=output.strip().replace('\n', '<br>'))


async def file_chown(tm, paths, user, group, recursively=''):
    """设置文件/目录所有者（异步任务）"""
    if isinstance(paths, str):
        paths = paths.split(',')
    jobname = f'file.chown_{",".join(paths)}'
    if not tm._start_job(jobname):
        return
    tm._update_job(jobname, 2, '正在设置用户和用户组...')

    for path in paths:
        result = await shell.async_task(chown, path, user, group, recursively == 'on')
        if result:
            code = 0
            msg = '设置用户和用户组成功！'
        else:
            code = -1
            msg = f'设置 {path} 的用户和用户组时失败！'
            break
    tm._finish_job(jobname, code, msg)


async def file_chmod(tm, paths, perms, recursively=''):
    """设置文件/目录权限（异步任务）"""
    if isinstance(paths, str):
        paths = paths.split(',')
    jobname = f'file.chmod_{",".join(paths)}'
    if not tm._start_job(jobname):
        return
    tm._update_job(jobname, 2, '正在设置权限...')

    try:
        perms_int = int(perms, 8)
    except (ValueError, TypeError):
        tm._finish_job(jobname, -1, '权限值输入有误！')
        return

    for path in paths:
        result = await shell.async_task(chmod, path, perms_int, recursively == 'on')
        if result:
            code = 0
            msg = '权限修改成功！'
        else:
            code = -1
            msg = f'修改 {path} 的权限时失败！'
            break
    tm._finish_job(jobname, code, msg)


async def file_wget(tm, url, path):
    """下载文件（异步任务）"""
    import tornado.escape
    jobname = f'file.wget_{tornado.escape.url_escape(url)}'
    if not tm._start_job(jobname):
        return
    tm._update_job(jobname, 2, f'正在下载 {url}...')

    if Path(path).is_dir():
        cmd = f'wget -q "{sh_quote(url)}" --directory-prefix={sh_quote(path)}'
    else:
        cmd = f'wget -q "{sh_quote(url)}" -O {sh_quote(path)}'
    result, output = await shell.async_command(cmd)
    if result == 0:
        tm._finish_job(jobname, 0, '下载成功！')
    else:
        tm._finish_job(jobname, -1, '下载失败！',
                       data=output.strip().replace('\n', '<br>'))


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
            f = str(Path(path) / item['name'])
            # print(f)
            # # if mime == 'text/plain':
            # t = guess_type(f)[0]
            # print(t)
            # print(t.startswith('text'))
            print('  istext: %s' % str(istext(f)))
            # print('  mimetype: %s' % mimetype(f))
