#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#
# Copyright (c) 2017-2026 Jackson Dou
# All rights reserved.
#
# InPanel is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE'.

"""MySQL 数据库管理模块"""

import os
import re
import shlex
import time
from pathlib import Path

import pexpect
from ..utils import valid_filename


def updatepwd(pwd, oldpwd):
    """Update password of root.
    """
    try:
        cmd = shlex.split(f'mysqladmin -uroot password "{pwd}" -p')
    except:
        return False

    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['Enter password', pexpect.EOF])
    if i == 1:
        if child.isalive():
            child.wait()
        return False

    child.sendline(oldpwd)
    i = child.expect(['error', pexpect.EOF])
    if child.isalive():
        return child.wait() == 0
    return i != 0

def shutdown(pwd):
    """Shutdown mysql server.
    """
    try:
        cmd = shlex.split('mysqladmin -uroot shutdown -p')
    except:
        return False

    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['Enter password', pexpect.EOF])
    if i == 1:
        if child.isalive(): child.wait()
        return False

    child.sendline(pwd)
    i = child.expect(['error', pexpect.EOF])
    if child.isalive(): return child.wait() == 0
    return i != 0

def _mysql(pwd):
    """Open a mysql client and auth login.
    """
    cmd = shlex.split('mysql -uroot -p -A')
    child = pexpect.spawn(cmd[0], cmd[1:])
    if not _auth(child, pwd): return False
    return child

def _auth(child, pwd):
    """Auth a mysql client login.
    """
    i = child.expect(['Enter password', pexpect.EOF])
    if i == 1:
        if child.isalive(): child.wait()
        return False

    child.sendline(pwd)
    i = child.expect(['mysql>', pexpect.EOF])
    if i == 1:
        if child.isalive(): child.wait()
        return False
    return True

def _exit(child):
    """Exit a mysql client.
    """
    child.sendline('exit')
    child.expect([pexpect.EOF])
    if child.isalive(): child.wait()

def _parse_result(output, includefields=True):
    """Parse result into a list.
    """
    lines = output.split('\n')[1:]
    if lines[0].startswith('Empty set'): return []
    if lines[0].startswith('Query OK'): return True
    if lines[0].startswith('+'):
        if includefields:
            fields = [f.strip() for f in lines[1].strip().strip('|').split('|')]
        datalines = lines[3:]
        rows = []
        for dline in datalines:
            if dline.startswith('|'):
                rows.append([v.strip() for v in dline.strip().strip('|').split('|')])
            else:
                break
        if includefields:
            return [dict(zip(fields, row)) for row in rows]
        else:
            return rows
    return True

def _sql(child, sql, returnresult=True, includefields=True):
    """Execute SQL statement in interactive mode.
    """
    sql = sql.strip()
    if '\n' in sql:
        sql = ' '.join([line.strip() for line in sql.split('\n')])
    if not sql.endswith(';'):
        sql += ';'

    child.sendline(sql)
    i = child.expect(['ERROR', 'mysql>', pexpect.EOF])
    if i == 0: 
        # skip old lines
        i = child.expect(['mysql>', pexpect.EOF])
        if i != 0: _exit(child)
        return False
    elif i == 2:
        _exit(child)
        return False

    if returnresult:
        return _parse_result(child.before, includefields=includefields)
    else:
        return True

def _escape(string):
    """Escape a string.
    """
    return re.escape(string).replace(r'\_', '_').replace(r'\%', '%')

def fupdatepwd(pwd):
    """Force update password of root.

    MySQL server should first enter rescue mode.
    """
    child = pexpect.spawn('mysql -A')
    i = child.expect(['mysql>', pexpect.EOF])
    if i == 1:
        if child.isalive(): child.wait()
        return False
    
    try:
        if not _sql(child, 'UPDATE mysql.user SET Password=PASSWORD("%s") WHERE User="root"' % _escape(pwd)): raise Exception()
        if not _sql(child, 'FLUSH PRIVILEGES'): raise Exception()
    except:
        _exit(child)
        return False
    else:
        _exit(child)

    return True

def checkpwd(pwd):
    """Validate password of root.
    """
    child = _mysql(pwd)
    if not child: return False
    _exit(child)
    return True

def show_databases(pwd, fullinfo=True):
    """Show database list.
    """
    child = _mysql(pwd)
    if not child: return False

    ignore_tables = ('information_schema', 'performance_schema', 'mysql')
    
    if not fullinfo:
        dbs = _sql(child, 'SHOW DATABASES', includefields=False)
        if not dbs:
            _exit(child)
            return False
        dbs = [db[0] for db in dbs if db[0] not in ignore_tables]
    else:
        # REF: http://stackoverflow.com/questions/184560/how-to-monitor-mysql-space
        sql = '''
SELECT schema_name name, charset, collation,
IFNULL(tables, 0) tables,
IFNULL(datsum, 0) datasize,
IFNULL(ndxsum, 0) indexsize,
IFNULL(totsum, 0) totalsize
FROM (
	SELECT schema_name, default_character_set_name charset, default_collation_name collation
	FROM information_schema.SCHEMATA
	WHERE schema_name NOT IN %s
) A LEFT JOIN (
	SELECT db, COUNT(1) tables, SUM(dat) datsum, SUM(ndx) ndxsum, SUM(dat+ndx) totsum
	FROM (
		SELECT table_schema db, data_length dat, index_length ndx
		FROM information_schema.tables WHERE engine IS NOT NULL
		AND table_schema NOT IN %s
	) AA
	GROUP BY db
) B ON A.schema_name=B.db''' % (repr(ignore_tables), repr(ignore_tables))
        dbs = _sql(child, sql)

    _exit(child)
    return dbs

def show_database(pwd, dbname):
    """Show a database info.
    """
    child = _mysql(pwd)
    if not child: return False
    
    sql = '''
SELECT schema_name name, charset, collation,
IFNULL(tables, 0) tables,
IFNULL(datsum, 0) datasize,
IFNULL(ndxsum, 0) indexsize,
IFNULL(totsum, 0) totalsize
FROM (
	SELECT schema_name, default_character_set_name charset, default_collation_name collation
	FROM information_schema.SCHEMATA
	WHERE schema_name='%s'
) A LEFT JOIN (
	SELECT db, COUNT(1) tables, SUM(dat) datsum, SUM(ndx) ndxsum, SUM(dat+ndx) totsum
	FROM (
		SELECT table_schema db, data_length dat, index_length ndx
		FROM information_schema.tables WHERE engine IS NOT NULL
		AND table_schema='%s'
	) AA
	GROUP BY db
) B ON A.schema_name=B.db''' % (_escape(dbname), _escape(dbname))
    dbinfo = _sql(child, sql)
    if dbinfo: dbinfo = dbinfo[0]

    _exit(child)
    return dbinfo

def create_database(pwd, dbname, charset='utf8', collation='utf8_general_ci'):
    """Create a new database.
    """
    child = _mysql(pwd)
    if not child: return False
    sql = 'CREATE DATABASE %s CHARACTER SET %s COLLATE %s' % \
          (_escape(dbname), _escape(charset), _escape(collation))
    if not _sql(child, sql):
        _exit(child)
        return False
    _exit(child)
    return True

def alter_database(pwd, dbname, charset='utf8', collation='utf8_general_ci'):
    """Alter database.
    """
    child = _mysql(pwd)
    if not child: return False
    sql = 'ALTER DATABASE %s CHARACTER SET %s COLLATE %s' % \
          (_escape(dbname), _escape(charset), _escape(collation))
    if not _sql(child, sql):
        _exit(child)
        return False
    _exit(child)
    return True

def rename_database(pwd, dbname, newname):
    """Rename a database.
    """
    child =  _mysql(pwd)
    if not child: return False
    
    try:
        create_sql = _sql(child, 'SHOW CREATE DATABASE %s' % _escape(dbname), includefields=False)
        if not create_sql: raise Exception()
        create_sql = create_sql[0][1]
        if not _sql(child, 'USE %s' % _escape(dbname)): raise Exception()
        tables = _sql(child, 'SHOW TABLES', includefields=False)
        if tables == False: raise Exception()
        
        if not _sql(child, create_sql.replace(dbname, newname)): raise Exception()
        for table in tables:
            table = table[0]
            sql = 'RENAME TABLE `%s`.`%s` TO `%s`.`%s`' % (_escape(dbname), table, _escape(newname), table)
            if not _sql(child, sql): raise Exception()
        if not _sql(child, 'DROP DATABASE %s' % _escape(dbname)): raise Exception()
    except:
        _exit(child)
        return False
    else:
        _exit(child)
    return True

def drop_database(pwd, dbname):
    """Drop a database.
    """
    child = _mysql(pwd)
    if not child: return False
    if not _sql(child, 'DROP DATABASE %s' % _escape(dbname)):
        _exit(child)
        return False
    _exit(child)
    return True

def export_database(pwd, dbname, exportpath):
    """Export database to a file.
    """
    filename = '%s_%s.sql' % (dbname, time.strftime('%Y%m%d_%H%M%S'))
    filepath = str(Path(exportpath) / filename)
    if not valid_filename(filename): return False

    cmd = 'mysqldump -uroot -p %s' % dbname
    cmd = '/bin/bash -c "%s > %s"' % (cmd, filepath)
    child = pexpect.spawn(cmd)

    i = child.expect(['Enter password', pexpect.EOF])
    if i == 1:
        if child.isalive(): child.wait()
        return False

    child.sendline(pwd)
    i = child.expect(['error', pexpect.EOF])
    if child.isalive():
        w = child.wait()
        return w == 0

    return i != 0

def show_users(pwd, dbname=None):
    """Show all user list, or user list of specified database.
    """
    child = _mysql(pwd)
    if not child: return False

    if not dbname:
        sql = "SELECT *, IF(`Password` = _latin1 '', 'N', 'Y') AS 'Password' FROM `mysql`.`user` ORDER BY `User` ASC, `Host` ASC"
    else:
        sql = '''
(SELECT `User`, `Host`, `Select_priv`, `Insert_priv`, `Update_priv`, `Delete_priv`, `Create_priv`, `Drop_priv`,
`Grant_priv`, `Index_priv`, `Alter_priv`, `References_priv`, `Create_tmp_table_priv`, `Lock_tables_priv`,
`Create_view_priv`, `Show_view_priv`, `Create_routine_priv`, `Alter_routine_priv`, `Execute_priv`, `Event_priv`, `Trigger_priv`, `Db`
FROM `mysql`.`db` WHERE '%s' LIKE `Db` AND NOT (
	`Select_priv` = 'N' AND `Insert_priv` = 'N' AND `Update_priv` = 'N' AND `Delete_priv` = 'N' AND `Create_priv` = 'N' AND `Drop_priv` = 'N'
	AND `Grant_priv` = 'N' AND `References_priv` = 'N' AND `Create_tmp_table_priv` = 'N' AND `Lock_tables_priv` = 'N' AND `Create_view_priv` = 'N'
	AND `Show_view_priv` = 'N' AND `Create_routine_priv` = 'N' AND `Alter_routine_priv` = 'N' AND `Execute_priv` = 'N' AND `Event_priv` = 'N'
	AND `Trigger_priv` = 'N'
)) UNION (
SELECT `User`, `Host`, `Select_priv`, `Insert_priv`, `Update_priv`, `Delete_priv`, `Create_priv`, `Drop_priv`,
`Grant_priv`, `Index_priv`, `Alter_priv`, `References_priv`, `Create_tmp_table_priv`, `Lock_tables_priv`,
`Create_view_priv`, `Show_view_priv`, `Create_routine_priv`, `Alter_routine_priv`, `Execute_priv`, `Event_priv`, `Trigger_priv`, '*' AS `Db`
FROM `mysql`.`user` WHERE NOT (
	`Select_priv` = 'N' AND `Insert_priv` = 'N' AND `Update_priv` = 'N' AND `Delete_priv` = 'N' AND `Create_priv` = 'N' AND `Drop_priv` = 'N'
	AND `Grant_priv` = 'N' AND `References_priv` = 'N' AND `Create_tmp_table_priv` = 'N' AND `Lock_tables_priv` = 'N' AND `Create_view_priv` = 'N'
	AND `Show_view_priv` = 'N' AND `Create_routine_priv` = 'N' AND `Alter_routine_priv` = 'N' AND `Execute_priv` = 'N' AND `Event_priv` = 'N'
	AND `Trigger_priv` = 'N'
)) ORDER BY `User` ASC, `Host` ASC, `Db` ASC''' % _escape(dbname)

    privs = _sql(child, sql)

    _exit(child)
    return privs

def show_user_globalprivs(pwd, user, host):
    """Show user global privileges.
    """
    child = _mysql(pwd)
    if not child: return False

    sql = "SELECT * FROM `mysql`.`user` WHERE `User` = '%s' AND `Host` = '%s'" % (_escape(user), _escape(host))
    privs = _sql(child, sql)
    privs = privs and privs[0] or False

    _exit(child)
    return privs

def show_user_dbprivs(pwd, user, host, dbname=None):
    """Show user privileges in database.
    """
    child = _mysql(pwd)
    if not child: return False

    if not dbname:
        sql = "SELECT * FROM `mysql`.`db` WHERE `User` = '%s' AND `Host` = '%s' ORDER BY `Db` ASC" % (_escape(user), _escape(host))
    else:
        sql = "SELECT * FROM `mysql`.`db` WHERE `User` = '%s' AND `Host` = '%s' AND '%s' LIKE `Db`" % (_escape(user), _escape(host), _escape(dbname))

    privs = _sql(child, sql)
    if privs and dbname: privs = privs[0]

    _exit(child)
    return privs

def revoke_user_privs(pwd, user, host, dbname=None):
    """Revoke user's privileges.
    """
    child =  _mysql(pwd)
    if not child: return False
    
    if not dbname:
        dbexpr = '*.*'
    else:
        dbexpr = '`%s`.*' % _escape(dbname)

    try:
        sql = "REVOKE ALL PRIVILEGES ON %s FROM '%s'@'%s'" % (dbexpr, _escape(user), _escape(host))
        if not _sql(child, sql, False): raise Exception()
        sql = "REVOKE GRANT OPTION ON %s FROM '%s'@'%s'" % (dbexpr, _escape(user), _escape(host))
        if not _sql(child, sql, False): raise Exception()
        if not dbname:
            sql = "GRANT USAGE ON *.* TO '%s'@'%s' " \
                  "WITH MAX_QUERIES_PER_HOUR 0 " \
                  "MAX_CONNECTIONS_PER_HOUR 0 " \
                  "MAX_UPDATES_PER_HOUR 0 " \
                  "MAX_USER_CONNECTIONS 0" % (_escape(user), _escape(host))
            if not _sql(child, sql, False): raise Exception()
    except:
        _exit(child)
        return False
    else:
        _exit(child)
    return True

def update_user_privs(pwd, user, host, privs, dbname=None):
    """Update user's privileges.
    """
    child =  _mysql(pwd)
    if not child: return False
    
    allprivs = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE',
        'CREATE', 'ALTER', 'INDEX', 'DROP', 'CREATE TEMPORARY TABLES',
        'SHOW VIEW', 'CREATE ROUTINE', 'ALTER ROUTINE', 'EXECUTE',
        'CREATE VIEW', 'EVENT', 'TRIGGER',
        'GRANT', 'LOCK TABLES', 'REFERENCES'
    ]
    
    if not dbname:
        allprivs.extend([
            'FILE', 'SUPER', 'PROCESS', 'RELOAD', 'SHUTDOWN', 'SHOW DATABASES',
            'REPLICATION CLIENT', 'REPLICATION SLAVE', 'CREATE USER'
        ])
        dbexpr = '*.*'
    else:
        dbexpr = '`%s`.*' % _escape(dbname)

    privs = filter(lambda a: a in allprivs, privs)
    
    # revoke privileges
    if len(privs) == 0:
        _exit(child)
        return revoke_user_privs(pwd, user, host, dbname)

    if 'GRANT' in privs:
        grant_option = 'WITH GRANT OPTION'
        privs = filter(lambda a: a != 'GRANT', privs)
    else:
        grant_option = ''
    if len(privs) == len(allprivs)-1:
        grant_sql = "GRANT ALL PRIVILEGES ON %s TO '%s'@'%s' %s" % (dbexpr, _escape(user), _escape(host), grant_option)
    else:
        grant_sql = "GRANT %s ON %s TO '%s'@'%s' %s" % (','.join(privs), dbexpr, _escape(user), _escape(host), grant_option)

    try:
        # don't check revoke result, the user may not exists
        sql = "REVOKE ALL PRIVILEGES ON %s FROM '%s'@'%s'" % (dbexpr, _escape(user), _escape(host))
        _sql(child, sql, False)
        sql = "REVOKE GRANT OPTION ON %s FROM '%s'@'%s'" % (dbexpr, _escape(user), _escape(host))
        _sql(child, sql, False)
        if not _sql(child, grant_sql, False): raise Exception()
    except:
        _exit(child)
        return False
    else:
        _exit(child)
    return True

def create_user(pwd, user, host, password=None):
    """Create a user.
    """
    child =  _mysql(pwd)
    if not child: return False

    if password:
        sql = "CREATE USER '%s'@'%s' IDENTIFIED BY '%s'" % (_escape(user), _escape(host), _escape(password))
    else:
        sql = "CREATE USER '%s'@'%s'" % (_escape(user), _escape(host))
    rs = _sql(child, sql, False)

    _exit(child)
    return rs

def drop_user(pwd, user, host):
    """Drop a user.
    """
    child = _mysql(pwd)
    if not child:
        return False

    rs = _sql(child, "DROP USER '%s'@'%s'" % (_escape(user), _escape(host)), False)

    _exit(child)
    return rs

def set_user_password(pwd, user, host, password=None):
    """Set password for user.
    """
    child = _mysql(pwd)
    if not child: return False

    if password:
        sql = "SET PASSWORD FOR '%s'@'%s' = PASSWORD('%s')" % (_escape(user), _escape(host), _escape(password))
    else:
        sql = "SET PASSWORD FOR '%s'@'%s' = ''" % (_escape(user), _escape(host))
    rs = _sql(child, sql, False)

    _exit(child)
    return rs


def web_handler(context):
    action = context.get_argument('action', '')
    password = context.get_argument('password', '')

    if action == 'updatepwd':
        newpassword = context.get_argument('newpassword', '')
        newpasswordc = context.get_argument('newpasswordc', '')

        if newpassword != newpasswordc:
            context.write({'code': -1, 'msg': '两次密码输入不一致！'})
            return

        if updatepwd(newpassword, password):
            context.write({'code': 0, 'msg': '密码设置成功！'})
        else:
            context.write({'code': -1, 'msg': '密码设置失败！'})

    elif action == 'checkpwd':
        if checkpwd(password):
            context.write({'code': 0, 'msg': '密码验证成功！'})
        else:
            context.write({'code': -1, 'msg': '密码验证失败！（密码不正确，或 MySQL 服务未启动）'})

    elif action == 'alter_database':
        dbname = context.get_argument('dbname', '')
        collation = context.get_argument('collation', '')
        rt = alter_database(password, dbname, collation=collation)
        if rt:
            context.write({'code': 0, 'msg': '数据库编码保存成功！'})
        else:
            context.write({'code': -1, 'msg': '数据库编码保存失败！'})


if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    
    #pp.pprint(checkpwd('admin'))
    #pp.pprint(show_databases('admin'))
    #pp.pprint(show_database('admin', 'abcd'))
    #pp.pprint(create_database('admin', 'abcd'))
    #pp.pprint(alter_database('admin', 'abcd', 'latin1', 'latin1_swedish_ci'))
    #pp.pprint(drop_database('admin', 'abcd'))
    #pp.pprint(rename_database('admin', 'abcd', 'test'))
    #pp.pprint(export_database('admin', 'abcd', '/root'))
    #pp.pprint(show_users('admin', 'abcd'))
    #pp.pprint(show_users('admin'))
    #pp.pprint(show_user_globalprivs('admin', 'ddyh', 'localhost'))
    #pp.pprint(show_user_dbprivs('admin', 'ddyh', 'localhost'))
    #pp.pprint(revoke_user_privs('admin', 'ddyh', 'localhost', 'abcd'))
    #pp.pprint(update_user_privs('admin', 'hilyjiang', 'localhost', ['SELECT']))
    #pp.pprint(create_user('admin', 'hilyjiang', '%'))
    #pp.pprint(drop_user('admin', 'hilyjiang', 'localhost'))
    #pp.pprint(set_user_password('admin', 'ddyh', 'localhost', 'ddyh'))


# ==========================================================================
# 异步任务函数（供 web.py _dispatch_task 调用，第一个参数 tm 为 TaskManager）
# ==========================================================================

import asyncio
import time
from subprocess import PIPE, Popen


async def mysql_fupdatepwd(tm, password):
    """强制重置 MySQL root 密码（异步任务）"""
    jobname = 'mysql.fupdatepwd'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, '正在检测 MySQL 服务状态...')
    cmd = 'service mysqld status'
    result, output = await shell.async_command(cmd)
    isstopped = 'stopped' in output

    if not isstopped:
        tm._update_job(jobname, 2, '正在停止 MySQL 服务...')
        cmd = 'service mysqld stop'
        result, output = await shell.async_command(cmd)
        if result != 0:
            tm._finish_job(jobname, -1, '停止 MySQL 服务时出错！',
                           data=output.strip().replace(' ', '<br>'))
            return

    tm._update_job(jobname, 2, '正在启用 MySQL 恢复模式...')
    manually = False
    cmd = 'service mysqld startsos'
    result, output = await shell.async_command(cmd)
    if result != 0:
        manually = True
        cmd = 'mysqld_safe --skip-grant-tables --skip-networking'
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, close_fds=True, shell=True)
        if not p:
            tm._finish_job(jobname, -1, '启用 MySQL 恢复模式时出错！',
                           data=output.strip().replace('\n', '<br>'))
            return

    if manually:
        time.sleep(2)

    error = False
    tm._update_job(jobname, 2, '正在强制重置 root 密码...')
    if not fupdatepwd(password):
        error = True

    if manually:
        result = await shell.async_task(shutdown, password)
        if result:
            tm._update_job(jobname, 0, '成功停止 MySQL 服务！')
        else:
            tm._update_job(jobname, -1, '停止 MySQL 服务失败！')
        p.terminate()
        p.wait()

    msg = ''
    if not isstopped:
        if error:
            msg = '重置 root 密码时发生错误！正在重启 MySQL 服务...'
            tm._update_job(jobname, -1, msg)
        else:
            tm._update_job(jobname, 2, '正在重启 MySQL 服务...')
        if manually:
            cmd = 'service mysqld start'
        else:
            cmd = 'service mysqld restart'
    else:
        if error:
            msg = '重置 root 密码时发生错误！正在停止 MySQL 服务...'
            tm._update_job(jobname, -1, msg)
        else:
            tm._update_job(jobname, 2, '正在停止 MySQL 服务...')
        if manually:
            cmd = ''
        else:
            cmd = 'service mysqld stop'

    if not cmd:
        if error:
            code = -1
            msg = '%sOK' % msg
        else:
            code = 0
            msg = 'root 密码重置成功！'
    else:
        result, output = await shell.async_command(cmd)
        if result == 0:
            if error:
                code = -1
                msg = '%sOK' % msg
            else:
                code = 0
                msg = 'root 密码重置成功！'
        else:
            if error:
                code = -1
                msg = '%sOK' % msg
            else:
                code = -1
                msg = 'root 密码重置成功，但在操作服务时出错！'
                data = output.strip().replace('\n', '<br>')

    tm._finish_job(jobname, code, msg, data=data)


async def mysql_databases(tm, password):
    """获取数据库列表（异步任务）"""
    jobname = 'mysql.databases'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, '正在获取数据库列表...')
    dbs = []
    dbs = await shell.async_task(show_databases, password)
    if dbs:
        code = 0
        msg = '获取数据库列表成功！'
    else:
        code = -1
        msg = '获取数据库列表失败！'

    tm._finish_job(jobname, code, msg, dbs)


async def mysql_users(tm, password, dbname=None):
    """获取用户列表（异步任务）"""
    if not dbname:
        jobname = 'mysql.users'
    else:
        jobname = f'mysql.users_{dbname}'
    if not tm._start_job(jobname):
        return

    from . import shell

    if not dbname:
        tm._update_job(jobname, 2, '正在获取用户列表...')
    else:
        tm._update_job(jobname, 2, f'正在获取数据库 {dbname} 的用户列表...')

    users = []
    users = await shell.async_task(show_users, password, dbname)
    if users:
        code = 0
        msg = '获取用户列表成功！'
    else:
        code = -1
        msg = '获取用户列表失败！'

    tm._finish_job(jobname, code, msg, users)


async def mysql_dbinfo(tm, password, dbname):
    """获取数据库详情（异步任务）"""
    jobname = f'mysql.dbinfo_{dbname}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, '正在获取数据库 %s 的信息...' % dbname)
    dbinfo = False
    dbinfo = await shell.async_task(show_database, password, dbname)
    if dbinfo:
        code = 0
        msg = '获取数据库 %s 的信息成功！' % dbname
    else:
        code = -1
        msg = '获取数据库 %s 的信息失败！' % dbname

    tm._finish_job(jobname, code, msg, dbinfo)


async def mysql_rename(tm, password, dbname, newname):
    """重命名数据库（异步任务）"""
    jobname = f'mysql.rename_{dbname}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在重命名 {dbname}...')
    result = await shell.async_task(rename_database, password, dbname, newname)
    if result == True:
        code = 0
        msg = f'{dbname} 重命名成功！'
    else:
        code = -1
        msg = f'{dbname} 重命名失败！'

    tm._finish_job(jobname, code, msg)


async def mysql_create(tm, password, dbname, collation):
    """创建数据库（异步任务）"""
    jobname = f'mysql.create_{dbname}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在创建 {dbname}...')
    result = await shell.async_task(create_database, password, dbname, collation=collation)
    if result == True:
        code = 0
        msg = f'{dbname} 创建成功！'
    else:
        code = -1
        msg = f'{dbname} 创建失败！'

    tm._finish_job(jobname, code, msg)


async def mysql_export(tm, password, dbname, path):
    """导出数据库（异步任务）"""
    jobname = f'mysql.export_{dbname}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在导出 {dbname}...')
    result = await shell.async_task(export_database, password, dbname, path)
    if result == True:
        code = 0
        msg = f'{dbname} 导出成功！'
    else:
        code = -1
        msg = f'{dbname} 导出失败！'

    tm._finish_job(jobname, code, msg)


async def mysql_drop(tm, password, dbname):
    """删除数据库（异步任务）"""
    jobname = f'mysql.drop_{dbname}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在删除 {dbname}...')
    result = await shell.async_task(drop_database, password, dbname)
    if result == True:
        code = 0
        msg = f'{dbname} 删除成功！'
    else:
        code = -1
        msg = f'{dbname} 删除失败！'

    tm._finish_job(jobname, code, msg)


async def mysql_createuser(tm, password, user, host, pwd=None):
    """创建用户（异步任务）"""
    username = f'{user}@{host}'
    jobname = f'mysql.createuser_{username}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在添加用户 {username}...')
    result = await shell.async_task(create_user, password, user, host, pwd)
    if result is True:
        code = 0
        msg = f'用户 {username} 添加成功！'
    else:
        code = -1
        msg = f'用户 {username} 添加失败！'

    tm._finish_job(jobname, code, msg)


async def mysql_userprivs(tm, password, user, host):
    """获取用户权限（异步任务）"""
    username = f'{user}@{host}'
    jobname = f'mysql.userprivs_{username}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在获取用户 {username} 的权限...')

    privs = {'global': {}, 'bydb': {}}
    globalprivs = await shell.async_task(show_user_globalprivs, password, user, host)
    if globalprivs != False:
        code = 0
        msg = f'获取用户 {username} 的全局权限成功！'
        privs['global'] = globalprivs
    else:
        code = -1
        msg = f'获取用户 {username} 的全局权限失败！'
        privs = False

    if privs:
        dbprivs = await shell.async_task(show_user_dbprivs, password, user, host)
        if dbprivs != False:
            code = 0
            msg = f'获取用户 {username} 的数据库权限成功！'
            privs['bydb'] = dbprivs
        else:
            code = -1
            msg = f'获取用户 {username} 的数据库权限失败！'
            privs = False

    tm._finish_job(jobname, code, msg, privs)


async def mysql_updateuserprivs(tm, password, user, host, privs, dbname=None):
    """更新用户权限（异步任务）"""
    username = f'{user}@{host}'
    if dbname:
        jobname = f'mysql.updateuserprivs_{username}_{dbname}'
    else:
        jobname = f'mysql.updateuserprivs_{username}'
    if not tm._start_job(jobname):
        return

    from . import shell

    if dbname:
        tm._update_job(jobname, 2, f'正在更新用户 {username} 在数据库 {dbname} 中的权限...')
    else:
        tm._update_job(jobname, 2, f'正在更新用户 {username} 的权限...')

    rt = await shell.async_task(update_user_privs, password, user, host, privs, dbname)
    if rt != False:
        code = 0
        msg = f'用户 {username} 的权限更新成功！'
    else:
        code = -1
        msg = f'用户 {username} 的权限更新失败！'

    tm._finish_job(jobname, code, msg)


async def mysql_setuserpassword(tm, password, user, host, pwd):
    """设置用户密码（异步任务）"""
    username = f'{user}@{host}'
    jobname = f'mysql.setuserpassword_{username}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在更新用户 {username} 的密码...')

    rt = await shell.async_task(set_user_password, password, user, host, pwd)
    if rt != False:
        code = 0
        msg = f'用户 {username} 的密码更新成功 ！'
    else:
        code = -1
        msg = f'用户 {username} 的密码更新失败 ！'

    tm._finish_job(jobname, code, msg)


async def mysql_dropuser(tm, password, user, host):
    """删除用户（异步任务）"""
    username = f'{user}@{host}'
    jobname = f'mysql.dropuser_{username}'
    if not tm._start_job(jobname):
        return

    from . import shell

    tm._update_job(jobname, 2, f'正在删除用户 {username}...')

    rt = await shell.async_task(drop_user, password, user, host)
    if rt != False:
        code = 0
        msg = f'用户 {username} 删除成功 ！'
    else:
        code = -1
        msg = f'用户 {username} 删除失败 ！'

    tm._finish_job(jobname, code, msg)
