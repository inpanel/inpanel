#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.
'''文件管理模块'''

import asyncio
import os
import shutil
import stat
from configparser import RawConfigParser
from grp import getgrgid, getgrnam
from mimetypes import guess_type
from pathlib import Path
from pwd import getpwnam, getpwuid
from time import time
from uuid import uuid4
from ..base import kernel_name, filespath_log, os_name, data_path
from . import logs

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


TRASH_DIR_NAME = '.inpanel_trash'
TRASH_META_DIR = str(Path(data_path) / 'trash')


def _get_trash_meta_dir():
    """获取并创建元信息目录"""
    meta_dir = Path(TRASH_META_DIR)
    meta_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    return meta_dir


# ========== 回收站核心函数 ==========


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
        # 从 filespath_log 读取全部浏览记录，提取最近30条去重路径
        paths = []
        if Path(filespath_log).exists():
            with open(filespath_log, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            # 格式: "时间 | 路径"，倒序读取，去重保留最新
            seen = set()
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                parts = line.split('|', 1)
                p = parts[1].strip() if len(parts) == 2 else line
                if p and p not in seen:
                    seen.add(p)
                    paths.append(p)
                    if len(paths) >= 30:
                        break
        context.write({'code': 0, 'msg': '', 'data': paths})

    elif action == 'add_history':
        path = context.get_argument('path', '')
        if not path:
            context.write({'code': -1, 'msg': '路径不能为空！'})
            return
        
        # 写入文件访问路径日志（记录所有历史）
        logs.write_file_access_log(path)
        
        # 返回最近30条去重路径
        paths = []
        if Path(filespath_log).exists():
            with open(filespath_log, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            seen = set()
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                parts = line.split('|', 1)
                p = parts[1].strip() if len(parts) == 2 else line
                if p and p not in seen:
                    seen.add(p)
                    paths.append(p)
                    if len(paths) >= 30:
                        break
        
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
                logs.write_file_operation_log('查看', path, '失败')
                context.write({'code': -1, 'msg': '不可识别的文件编码 ！'})
                return
            logs.write_file_operation_log('查看', path, '成功')
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
            logs.write_file_operation_log('修改', path, '成功')
            context.write({'code': 0, 'msg': '文件保存成功！'})
        else:
            logs.write_file_operation_log('修改', path, '失败')
            context.write({'code': -1, 'msg': '文件保存失败！'})

    elif action == 'createfolder':
        path = context.get_argument('path', '')
        name = context.get_argument('name', '')

        if context.config.get('runtime', 'mode') == 'demo':
            if not path.startswith('/var/www') and not path.startswith(context.settings['package_path']):
                context.write({'code': -1, 'msg': '演示模式不允许修改除 /var/www 以外的目录！'})
                return

        fullpath = str(Path(path) / name)
        if dadd(path, name):
            logs.write_file_operation_log('创建', fullpath, '成功')
            context.write({'code': 0, 'msg': '文件夹创建成功！'})
        else:
            logs.write_file_operation_log('创建', fullpath, '失败')
            context.write({'code': -1, 'msg': '文件夹创建失败！'})

    elif action == 'createfile':
        path = context.get_argument('path', '')
        name = context.get_argument('name', '')

        if context.config.get('runtime', 'mode') == 'demo':
            if not path.startswith('/var/www'):
                context.write({'code': -1, 'msg': '演示模式不允许修改除 /var/www 以外的目录！'})
                return

        fullpath = str(Path(path) / name)
        if fadd(path, name):
            logs.write_file_operation_log('创建', fullpath, '成功')
            context.write({'code': 0, 'msg': '文件创建成功！'})
        else:
            logs.write_file_operation_log('创建', fullpath, '失败')
            context.write({'code': -1, 'msg': '文件创建失败！'})

    elif action == 'rename':
        path = context.get_argument('path', '')
        name = context.get_argument('name', '')

        if context.config.get('runtime', 'mode') == 'demo':
            if not path.startswith('/var/www'):
                context.write({'code': -1, 'msg': '演示模式不允许修改除 /var/www 以外的目录！'})
                return

        if rename(path, name):
            old_name = str(Path(path).name)
            new_path = str(Path(path).parent / name)
            logs.write_file_operation_log('重命名', path, '成功', f'{old_name} → {name}')
            context.write({'code': 0, 'msg': '重命名成功！'})
        else:
            logs.write_file_operation_log('重命名', path, '失败')
            context.write({'code': -1, 'msg': '重命名失败！'})

    elif action == 'exist':
        path = context.get_argument('path', '')
        name = context.get_argument('name', '')
        fullpath = Path(path) / name
        if fullpath.exists():
            context.write({'code': 0, 'msg': '', 'data': str(fullpath)})
        else:
            context.write({'code': 0, 'msg': '', 'data': ''})

    elif action == 'link':
        srcpath = context.get_argument('srcpath', '')
        despath = context.get_argument('despath', '')

        if context.config.get('runtime', 'mode') == 'demo':
            if not despath.startswith('/var/www') and not despath.startswith(context.settings['package_path']):
                context.write({'code': -1, 'msg': '演示模式不允许在除 /var/www 以外的目录下创建链接！'})
                return

        if link(srcpath, despath):
            logs.write_file_operation_log('创建链接', despath, '成功')
            context.write({'code': 0, 'msg': f'链接 {despath} 创建成功 ！'})
        else:
            logs.write_file_operation_log('创建链接', despath, '失败')
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
                logs.write_file_operation_log('删除', path, '成功')
                context.write({'code': 0, 'msg': f'已将 {path} 移入回收站'})
            else:
                logs.write_file_operation_log('删除', path, '失败')
                context.write({'code': -1, 'msg': f'将 {path} 移入回收站失败'})
        else:
            for path in paths:
                if not delete(path):
                    logs.write_file_operation_log('删除', path, '失败')
                    context.write({'code': -1, 'msg': f'将 {path} 移入回收站失败'})
                    return
                logs.write_file_operation_log('删除', path, '成功')
            context.write({'code': 0, 'msg': '批量移入回收站成功！'})

    elif action == 'tlist':
        context.write({'code': 0, 'msg': '', 'data': tlist()})

    elif action == 'titem':
        uuid = context.get_argument('uuid', '')
        info = titem(uuid)
        if info:
            context.write({'code': 0, 'msg': '', 'data': info})
        else:
            context.write({'code': -1, 'msg': '获取项目信息失败！'})

    elif action == 'trestore':
        uuid = context.get_argument('uuid', '')
        info = titem(uuid)
        if info and trestore(uuid):
            logs.write_file_operation_log('还原', info['path'], '成功')
            context.write({'code': 0, 'msg': f'已还原 {info["name"]} 到 {info["path"]} ！'})
        else:
            if info:
                logs.write_file_operation_log('还原', info['path'], '失败')
            context.write({'code': -1, 'msg': '还原失败！'})

    elif action == 'tdelete':
        uuid = context.get_argument('uuid', '')
        info = titem(uuid)
        if info and tdelete(uuid):
            logs.write_file_operation_log('彻底删除', info['path'], '成功')
            context.write({'code': 0, 'msg': f'已删除 {info["name"]} ！'})
        else:
            if info:
                logs.write_file_operation_log('彻底删除', info['path'], '失败')
            context.write({'code': -1, 'msg': '删除失败！'})


def listdir(path, showdotfiles=False, onlydir=None):
    '''list folders (and files)'''
    path = str(Path(path))
    if not Path(path).exists() or not Path(path).is_dir():
        return False
    items = sorted(p.name for p in Path(path).iterdir())
    if not showdotfiles:
        items = [item for item in items if not item.startswith('.')]
    for i, item in enumerate(items):
        items[i] = getitem(str(Path(path) / item))
    # 过滤掉 getitem 返回 False 的项（文件不存在或无权限）
    items = [item for item in items if item is not False]
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
    items = sorted(p.name for p in Path(d).iterdir())
    return items if len(items) > 0 else []


def getitem(path):
    '''get file stat'''
    if not Path(path).exists() and not Path(path).is_symlink():
        return False
    name = Path(path).name
    basepath = str(Path(path).parent)
    l_stat = Path(path).lstat()
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
            mode = Path(linkfile).stat().st_mode
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
        Path(oldpath).rename(newpath)
        return True
    except:
        return False


def link(srcpath, despath):
    try:
        Path(despath).symlink_to(srcpath)
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
    return Path(filepath).lstat().st_size


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
            filename = f'.{Path(path).name}.bak'
            Path(path).rename(str(Path(dname) / filename))
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
    '''Move files to the Recycle Bin

    流程：
    1. 获取文件所属挂载点 mount
    2. 尝试在 mount 下创建 .inpanel_trash/ 目录（同盘 rename，速度快）
    3. 若 mount 下无写权限，fallback 到 data/trash/files/ 目录（跨盘复制）
    4. 生成 uuid，移动文件到回收站目录
    5. 写元信息到 data/trash/{uuid}.ini
    '''
    path = str(Path(path))
    if not Path(path).exists():
        return False

    mount = _get_mount_for_path(path)
    if not mount:
        return False

    trash_dir = _ensure_trash_dir(mount)

    if trash_dir is not None:
        # 同盘 rename，速度最快
        uuid = str(uuid4())
        target = trash_dir / uuid
        try:
            Path(path).rename(target)
        except OSError:
            return False
        used_fallback = False
    else:
        # mount 下无写权限（如根目录 /），fallback 到 data/trash/files/
        fallback_dir = _get_trash_meta_dir() / 'files'
        try:
            fallback_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            return False

        uuid = str(uuid4())
        target = fallback_dir / uuid
        try:
            if Path(path).is_dir():
                shutil.move(path, str(target))
            else:
                shutil.move(path, str(target))
        except OSError:
            return False
        # 更新 mount 为 data_path，方便还原时定位
        mount = data_path
        used_fallback = True

    _write_meta(uuid, {
        'uuid': uuid,
        'name': Path(path).name,
        'path': path,
        'mount': mount,
        'time': str(int(time())),
        'isdir': str(target.is_dir()),
        'size': str(_get_file_size(target)),
    })

    # 清理备份文件
    dname = str(Path(path).parent)
    bakfilepath = str(Path(dname) / (f'.{Path(path).name}.bak'))
    if Path(bakfilepath).exists():
        return delete(bakfilepath)
    return True


def _getmounts():
    '''获取系统挂载点列表（按路径长度降序，用于最长前缀匹配）。

    Linux:   从 /proc/mounts 读取，过滤 ext/xfs/btrfs 等文件系统
    macOS:   返回 [用户主目录]
    Windows: 返回可用盘符列表
    '''
    if kernel_name == 'Darwin':
        return [str(Path.home())]
    elif kernel_name == 'Windows':
        return _get_windows_drives()
    else:
        mounts = server.ServerInfo.mounts()
        mounts = [mount['path'] for mount in mounts]
        return sorted(mounts, key=lambda x: len(x), reverse=True)


def _get_windows_drives():
    '''获取 Windows 可用盘符列表'''
    drives = []
    try:
        import string
        from ctypes import windll
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(f'{letter}:\\')
            bitmask >>= 1
    except:
        pass
    return sorted(drives, key=len, reverse=True)


def _get_mount_for_path(path):
    '''匹配文件所属的挂载点（取最长前缀匹配）。'''
    mounts = _getmounts()
    matched = ''
    for m in mounts:
        if path.startswith(m) and len(m) > len(matched):
            matched = m
    return matched


def _ensure_trash_dir(mount):
    '''获取或创建挂载点下的回收站目录。

    Returns:
        Path or None: 成功返回目录路径，无权限则返回 None
    '''
    trash = Path(mount) / TRASH_DIR_NAME
    try:
        trash.mkdir(mode=0o700, exist_ok=True)
    except PermissionError:
        return None
    return trash


def _get_file_size(path):
    '''获取文件/目录大小（字节）'''
    p = Path(path)
    if not p.exists():
        return 0
    if p.is_file() or p.is_symlink():
        return p.stat().st_size
    if p.is_dir():
        total = 0
        try:
            for f in p.rglob('*'):
                if f.is_file() or f.is_symlink():
                    total += f.stat().st_size
        except:
            pass
        return total
    return 0


def _write_meta(uuid, meta_dict):
    '''写元信息 INI 文件到 data/trash/{uuid}.ini'''
    meta_dir = _get_trash_meta_dir()
    meta_path = meta_dir / f'{uuid}.ini'
    cfg = RawConfigParser()
    cfg.add_section('info')
    for key, value in meta_dict.items():
        cfg.set('info', key, value)
    with open(meta_path, 'w', encoding='utf-8') as f:
        cfg.write(f)


def _read_meta(uuid):
    '''读取元信息 INI 文件，返回 dict 或 None'''
    meta_path = _get_trash_meta_dir() / f'{uuid}.ini'
    if not meta_path.exists():
        return None
    try:
        cfg = RawConfigParser()
        cfg.read(str(meta_path), encoding='utf-8')
        return dict(cfg.items('info'))
    except:
        return None


def _remove_meta(uuid):
    '''删除元信息文件'''
    meta_path = _get_trash_meta_dir() / f'{uuid}.ini'
    meta_path.unlink(missing_ok=True)


def tlist():
    '''列出回收站中所有已删除文件。

    只遍历 data/trash/*.ini，读取每个元信息文件。
    同时检查物理文件是否存在，补充 size 和 exists 字段。

    Returns:
        list[dict]: 已删除文件列表，按删除时间倒序排列
    '''
    meta_dir = _get_trash_meta_dir()
    items = []
    for meta_file in sorted(meta_dir.glob('*.ini')):
        uuid = meta_file.stem
        meta = _read_meta(uuid)
        if meta is None:
            continue

        mount = meta.get('mount', '')
        # 定位物理文件：同盘在 {mount}/.inpanel_trash/，fallback 在 data/trash/files/
        if mount == data_path:
            file_path = _get_trash_meta_dir() / 'files' / uuid
        else:
            file_path = Path(mount) / TRASH_DIR_NAME / uuid

        if file_path.exists():
            meta['exists'] = True
            meta['size'] = str(_get_file_size(file_path))
            meta['isdir'] = str(file_path.is_dir())
        else:
            meta['exists'] = False

        # 时间格式化
        try:
            meta['time'] = ftime(float(meta.get('time', '0')))
        except:
            pass

        items.append(meta)

    items.sort(key=lambda x: x.get('time', ''), reverse=True)
    return items


def titem(uuid):
    '''获取单个回收站项目信息。

    Args:
        uuid: 文件唯一标识

    Returns:
        dict or False
    '''
    meta = _read_meta(uuid)
    if meta is None:
        return False

    mount = meta.get('mount', '')
    # 定位物理文件：同盘在 {mount}/.inpanel_trash/，fallback 在 data/trash/files/
    if mount == data_path:
        originpath = str(_get_trash_meta_dir() / 'files' / uuid)
    else:
        originpath = str(Path(mount) / TRASH_DIR_NAME / uuid)
    meta['originpath'] = originpath

    try:
        meta['time'] = ftime(float(meta.get('time', '0')))
    except:
        pass

    return meta


def trestore(uuid):
    '''从回收站还原文件。

    流程：
    1. 读取 data/trash/{uuid}.ini 获取元信息
    2. 定位物理文件位置（同盘或 fallback）
    3. 尝试 rename 还原，失败则跨盘 copy + delete
    4. 删除元信息文件 data/trash/{uuid}.ini

    Args:
        uuid: 文件唯一标识

    Returns:
        bool
    '''
    meta = _read_meta(uuid)
    if meta is None:
        return False

    mount = meta.get('mount', '')
    original_path = meta.get('path', '')

    # 定位物理文件：同盘在 {mount}/.inpanel_trash/，fallback 在 data/trash/files/
    if mount == data_path:
        src = _get_trash_meta_dir() / 'files' / uuid
    else:
        src = Path(mount) / TRASH_DIR_NAME / uuid

    if not src.exists():
        return False

    # 确保目标父目录存在
    Path(original_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        src.rename(original_path)
        _remove_meta(uuid)
        return True
    except OSError:
        # 跨盘回退到 copy + delete
        try:
            if src.is_dir():
                shutil.copytree(src, original_path, symlinks=True)
                shutil.rmtree(src)
            else:
                shutil.copy2(src, original_path)
                src.unlink()
            _remove_meta(uuid)
            return True
        except:
            return False


def tdelete(uuid):
    '''从回收站彻底删除文件。

    流程：
    1. 读取 data/trash/{uuid}.ini 获取 mount
    2. 定位物理文件位置（同盘或 fallback）
    3. 物理删除文件
    4. 删除元信息文件 data/trash/{uuid}.ini

    Args:
        uuid: 文件唯一标识

    Returns:
        bool
    '''
    meta = _read_meta(uuid)
    if meta is None:
        return False

    mount = meta.get('mount', '')

    # 定位物理文件：同盘在 {mount}/.inpanel_trash/，fallback 在 data/trash/files/
    if mount == data_path:
        file_path = _get_trash_meta_dir() / 'files' / uuid
    else:
        file_path = Path(mount) / TRASH_DIR_NAME / uuid

    # 物理删除
    if file_path.is_dir():
        shutil.rmtree(file_path, ignore_errors=True)
    elif file_path.is_file() or file_path.is_symlink():
        file_path.unlink(missing_ok=True)

    _remove_meta(uuid)
    return True


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
                    Path(tpath).chmod(perms)
                for momo in files:
                    tpath = str(Path(root) / momo)
                    if not Path(tpath).exists():
                        continue
                    Path(tpath).chmod(perms)
        Path(path).chmod(perms)
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
        logs.write_file_operation_log('复制', srcpath, '成功', f'{srcpath} → {despath}')
        tm._finish_job(jobname, 0, f'复制 {srcpath} 到 {despath} 完成！')
    else:
        logs.write_file_operation_log('复制', srcpath, '失败')
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

    logs.write_file_operation_log('移动', srcpath, '成功' if code == 0 else '失败', f'{srcpath} → {despath}')
    tm._finish_job(jobname, code, msg, data=data)


async def file_remove(tm, paths):
    """删除文件/目录（异步任务）"""
    if isinstance(paths, str):
        paths = paths.split(',')
    jobname = f'file.remove_{",".join(paths)}'
    if not tm._start_job(jobname):
        return
    code, msg, data = 0, '', None
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
        if not Path('/usr/bin/zip').exists() and not shutil.which('zip'):
            tm._update_job(jobname, 2, '正在安装 zip...')
            from .package import get_package_manager
            pm = get_package_manager()
            if pm is None:
                tm._finish_job(jobname, -1, '未检测到可用的包管理器，无法安装 zip！')
                return
            loop = asyncio.get_event_loop()
            ok, output = await loop.run_in_executor(None, pm.install, ['zip', 'unzip'])
            if not ok:
                if 'Permission denied' in output or 'are you root' in output.lower():
                    tm._finish_job(jobname, -1, '安装 zip 失败：当前运行权限不足，无法执行包管理器的安装操作，请以 root 用户运行 InPanel，或手动安装 zip 后再试')
                else:
                    tm._finish_job(jobname, -1, f'zip 安装失败：{output}')
                return
        cmd = f'cd {sh_quote(basepath)}; zip -rq9 {sh_quote(zippath)} {path}'
    elif zippath.endswith('.gz'):
        path = ' '.join([sh_quote(item) for item in paths])
        cmd = f'gzip -f {path}'
        # import shutil
        # # .gz 为单文件压缩，需先复制源文件到目标路径（去掉 .gz 后缀），再 gzip
        # src_path = paths[0]
        # tmp_path = zippath[:-3]  # 去掉 .gz 后缀
        # shutil.copy2(src_path, tmp_path)
        # cmd = f'gzip -f {sh_quote(tmp_path)}'
    else:
        tm._finish_job(jobname, -1, '不支持的类型！')
        return

    result, output = await shell.async_command(cmd)
    if result == 0:
        logs.write_file_operation_log('压缩', zippath, '成功')
        tm._finish_job(jobname, 0, f'压缩到 {zippath} 成功！')
    else:
        logs.write_file_operation_log('压缩', zippath, '失败')
        tm._finish_job(jobname, -1, '压缩失败！',
                       data=output.strip().replace('\n', '<br>'))


async def file_decompress(tm, zippath, despath=''):
    """解压文件（异步任务）"""
    jobname = f'file.decompress_{zippath}_{despath}' if despath else f'file.decompress_{zippath}'
    if not tm._start_job(jobname):
        return
    tm._update_job(jobname, 2, f'正在解压 {zippath}...')

    if zippath.endswith('.tar.gz') or zippath.endswith('.tgz'):
        cmd = f'tar zxf {sh_quote(zippath)} -C {sh_quote(despath)}'
    elif zippath.endswith('.tar.bz2'):
        cmd = f'tar jxf {sh_quote(zippath)} -C {sh_quote(despath)}'
    elif zippath.endswith('.zip'):
        if not Path('/usr/bin/unzip').is_file() and not shutil.which('unzip'):
            tm._update_job(jobname, 2, '正在安装 unzip...')
            from .package import get_package_manager
            pm = get_package_manager()
            if pm is None:
                tm._finish_job(jobname, -1, '未检测到可用的包管理器，无法安装 unzip！')
                return
            loop = asyncio.get_event_loop()
            ok, output = await loop.run_in_executor(None, pm.install, ['unzip'])
            if not ok:
                if 'Permission denied' in output or 'are you root' in output.lower():
                    tm._finish_job(jobname, -1, '安装 unzip 失败：当前运行权限不足，无法执行包管理器的安装操作，请以 root 用户运行 InPanel，或手动安装 unzip 后再试')
                else:
                    tm._finish_job(jobname, -1, f'unzip 安装失败：{output}')
                return
        cmd = f'unzip -q -o {sh_quote(zippath)} -d {sh_quote(despath)}'
    elif zippath.endswith('.gz'):
        cmd = f'gunzip -f {sh_quote(zippath)}'
    else:
        tm._finish_job(jobname, -1, '不支持的类型！')
        return

    result, output = await shell.async_command(cmd)
    if result == 0:
        logs.write_file_operation_log('解压', zippath, '成功', f'解压到 {despath}' if despath else '')
        tm._finish_job(jobname, 0, f'解压 {zippath} 成功！')
    else:
        logs.write_file_operation_log('解压', zippath, '失败')
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

    code, msg = 0, ''
    for path in paths:
        old_item = getitem(path)
        old_uname = old_item['uname'] if old_item else ''
        old_gname = old_item['gname'] if old_item else ''
        result = await shell.async_task(chown, path, user, group, recursively == 'on')
        if result:
            code = 0
            msg = '设置用户和用户组成功！'
            detail = f'{old_uname}:{old_gname} → {user}:{group}'
            logs.write_file_operation_log('修改权限', path, '成功', detail)
        else:
            code = -1
            msg = f'设置 {path} 的用户和用户组时失败！'
            logs.write_file_operation_log('修改权限', path, '失败')
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

    code, msg = 0, ''
    for path in paths:
        old_item = getitem(path)
        old_perms = old_item['perms'] if old_item else ''
        result = await shell.async_task(chmod, path, perms_int, recursively == 'on')
        if result:
            code = 0
            msg = '权限修改成功！'
            detail = f'{old_perms} → {perms}'
            logs.write_file_operation_log('修改权限', path, '成功', detail)
        else:
            code = -1
            msg = f'修改 {path} 的权限时失败！'
            logs.write_file_operation_log('修改权限', path, '失败')
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
        cmd = f'wget -q {sh_quote(url)} --directory-prefix={sh_quote(path)}'
    else:
        cmd = f'wget -q {sh_quote(url)} -O {sh_quote(path)}'
    result, output = await shell.async_command(cmd)
    if result == 0:
        logs.write_file_operation_log('下载', path, '成功', f'来源: {url}')
        tm._finish_job(jobname, 0, '下载成功！')
    else:
        logs.write_file_operation_log('下载', path, '失败')
        tm._finish_job(jobname, -1, '下载失败！',
                       data=output.strip().replace('\n', '<br>'))


if __name__ == '__main__':
    print('* List directory of /Users:')
    path = '/Users'
    items = listdir(path)
    if items is not False:
        for item in items:
            print(f"  name: {item['name']}")
            print(f"  isdir: {item['isdir']!s}")
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
            print(f'  istext: {istext(f)!s}')
            # print('  mimetype: %s' % mimetype(f))
