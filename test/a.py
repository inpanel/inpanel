# -*- coding: utf-8 -*-
# 获取进程列表

# import psutil
import re
# for proc in psutil.process_iter():
#     try:
#         pinfo = proc.as_dict(attrs=['pid', 'name'])
#     except psutil.NoSuchProcess:
#         pass
#     else:
#         print(pinfo)

f = open('/Users/douzhenjiang/Projects/intranet-panel/test/a.py')
print f.readline()

a = '7878 (asdfsdf)'
b = 7
# c = a and b

ll = a.split()[1]
# print(ll[0])
# lll = ll.replace('(','').replace(')','')
print ll
# name = ''
if ll[-1] == ')':
    ll = ll[:-1]
    print ll
if ll[0] == '(':
    ll = ll[1:]
    print ll


# print a.split()
# if not a:
#     print 'c'