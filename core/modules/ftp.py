# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, doudoudzj
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

'''Module for FTP'''

import os
from ftplib import FTP


class FTPClient():
    '''FTP Module'''

    def __init__(self, host, user, pswd):
        self.ftp = None
        self.host = host
        self.user = user
        self.pswd = pswd
        self.init_client()

    def __delete__(self, instance):
        self.quit()

    def init_client(self):
        '''init instance'''
        try:
            self.ftp = FTP(self.host)
            self.ftp.login(self.user, self.pswd)
            print('connected: "%s"' % self.host)
            return self.ftp
        except:
            print('connect failed.')
            print('Please check if the host, user and password is correct.')
            return False

    def reconnect(self):
        '''reconnect to ftp'''
        try:
            self.ftp.login(self.user, self.pswd)
            print('reconnected: "%s"' % self.host)
        except:
            print('reconnect failed')
            return False
        return True

    def disconnect(self):
        '''close connection'''
        try:
            self.ftp.close()
            print('disconnect successful')
        except:
            print('disconnect failed')
            return False
        return True

    def quit(self):
        '''quit and close connection'''
        try:
            self.ftp.quit()
            print('quit successful')
        except:
            print('quit failed')
            return False
        return True

    def cd(self, path):
        '''change directory'''
        if not path:
            return False
        try:
            return self.ftp.cwd(path)
        except:
            print('change directory failed: "%s"' % path)
            return False

    def pwd(self):
        '''get current path'''
        try:
            return self.ftp.pwd()
        except:
            print('get path failed')
            return None

    def ls(self, path='', onlyname=False):
        '''get list of files and directories'''
        try:
            if onlyname is True:
                return self.ftp.nlst()
            return self.ftp.dir(path)
        except:
            print('get list failed: "%s"' % path)
            return None

    def mkd(self, path):
        '''create a directory, return its full pathname.
        '''
        if not path:
            return False
        try:
            return self.ftp.mkd(path)
        except:
            print('create failed: "%s"' % path)
            return False

    def rename(self, oldname, newname):
        '''rename a file or directory.'''
        try:
            self.ftp.rename(oldname, newname)
            print('rename successful: from "%s" to "%s"' % (oldname, newname))
        except:
            print('rename failed: from "%s" to "%s"' % (oldname, newname))
            return False
        return True

    def rm(self, filename):
        '''delete a file or directory.'''
        try:
            if self.ftp.delete(filename):
                print('delete successful: "%s"' % filename)
                return True
            else:
                print('delete failed: "%s"' % filename)
                return False
        except:
            print('delete error: "%s"' % filename)
            return False

    def rmd(self, filename):
        '''delete a file or directory.'''
        try:
            if self.ftp.delete(filename):
                print('delete successful: "%s"' % filename)
                return True
            else:
                print('delete failed: "%s"' % filename)
                return False
        except:
            print('delete failed: "%s"' % filename)
            return False

    def upload(self, filepath):
        '''upload local file to FTP'''
        try:
            with open(filepath, 'rb') as source:
                target = os.path.basename(filepath)
                self.ftp.storbinary('STOR %s' % target, source)
        except:
            print('upload failed: "%s"' % filepath)
            return False
        print('upload successful: "%s"' % filepath)
        return True

    def download(self, filename, localfile=''):
        '''download FTP file to local'''
        localfile = os.path.abspath(filename if not localfile else localfile)
        try:
            with open(localfile, 'wb') as target:
                self.ftp.retrbinary("RETR %s" % filename, target.write)
        except:
            print('download failed: from "%s" to "%s"' % (filename, localfile))
            return False
        print('download successful: from "%s" to "%s"' % (filename, localfile))
        return True

    def find(self, filename):
        '''find file on FTP'''
        files = self.ftp.nlst()
        if filename in files:
            return True
        else:
            return False

def transtoftp(address, account, password, source, target):
    try:
        ftp = FTPClient(address, account, password)
        # print('1')
        ftp.cd(os.path.abspath(target))
        # print('2')
        ftp.upload(source)
        # print('3')
        ftp.quit()
        # print('4')
        return True
    except:
        return False

def transtoftpa(*args, **kwds):
    import time
    time.sleep(5)
    return True

def test():
    host = ''
    user = ''
    pswd = ''
    ftp = FTPClient(host, user, pswd)
    # ftp.ls()
    ftp.cd('/Backup')
    # print(ftp.pwd())
    # ftp.ls()
    # ftp.rename('1234567/cc.txt', 'ccaa.txt')
    # ftp.rename('ccaa.txt', '1234567/afasff.txt')
    # ftp.mkd('abc/aaa/ccc')  # 创建文件夹
    # ftp.mkd('ccc')  # 创建文件夹
    # ftp.upload('./app.icns')  # 上传文件
    # ftp.upload('./bbb.txt')  # 上传文件

    # ftp.upload('111.txt')  # 上传文件
    # ftp.upload('222.txt')  # 上传文件
    # ftp.upload('bbb.txt')  # 上传文件
    # ftp.download('111.txt', '111aaa.txt')  # 下载文件重命名
    # ftp.download('222.txt', '222aaa.txt')  # 下载文件重命名
    # ftp.download('111.txt')  # 下载文件覆盖
    # ftp.download('222.txt')  # 下载文件覆盖
    # ftp.download('bbb.txt')  # 下载文件覆盖

    # ftp.rm('bbb.txt')  # 删除文件
    # ftp.rmd("ccc")  # 删除目录

    print(ftp.find('aaa.txt'))


    ftp.quit()  # 退出


if __name__ == '__main__':
    test()
