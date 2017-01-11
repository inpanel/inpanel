#-*- coding: utf-8 -*-
#
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# VPSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE.txt'.

"""Package for mysql operations.
"""

import os

if __name__ == '__main__':
    import sys
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, root_path)

import pexpect
import shlex
import re
import time
import utils


def updatepwd(pwd, oldpwd):
    """Update password of root.
    """
    try:
        cmd = shlex.split('mysqladmin -uroot password "%s" -p' % pwd)
    except:
        return False

    child = pexpect.spawn(cmd[0], cmd[1:])
    i = child.expect(['Enter password', pexpect.EOF])
    if i == 1:
        if child.isalive(): child.wait()
        return False

    child.sendline(oldpwd)
    i = child.expect(['error', pexpect.EOF])
    if child.isalive(): return child.wait() == 0
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
    return re.escape(string).replace('\_', '_').replace('\%', '%')
    
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
    filepath = os.path.join(exportpath, filename)
    if not utils.valid_filename(filename): return False
    
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
    if not child: return False

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
    #pp.pprint(export_database('admin', 'abcd', '/root'));
    #pp.pprint(show_users('admin', 'abcd'))
    #pp.pprint(show_users('admin'))
    #pp.pprint(show_user_globalprivs('admin', 'ddyh', 'localhost'))
    #pp.pprint(show_user_dbprivs('admin', 'ddyh', 'localhost'))
    #pp.pprint(revoke_user_privs('admin', 'ddyh', 'localhost', 'abcd'))
    #pp.pprint(update_user_privs('admin', 'hilyjiang', 'localhost', ['SELECT']))
    #pp.pprint(create_user('admin', 'hilyjiang', '%'))
    #pp.pprint(drop_user('admin', 'hilyjiang', 'localhost'))
    #pp.pprint(set_user_password('admin', 'ddyh', 'localhost', 'ddyh'))
