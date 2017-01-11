#-*- coding: utf-8 -*-
#
# Copyright (c) 2012, VPSMate development team
# All rights reserved.
#
# VPSMate is distributed under the terms of the (new) BSD License.
# The full license can be found in 'LICENSE.txt'.

"""Package for reading and writing nginx configuration.
"""

import os
import re
import glob
import utils

DEBUG = False

# d stand for directive, and c stand for context
DIRECTIVES = {
    # REF: http://wiki.nginx.org/CoreModule
    'daemon':                       ['_'],
    'env':                          ['_'],
    'debug_points':                 ['_'],
    'error_log':                    ['_', 'http', 'server', 'location'],
    'include':                      ['_', 'http', 'server', 'location'],
    'lock_file':                    ['_'],
    'master_process':               ['_'],
    'pcre_jit':                     ['_'],
    'pid':                          ['_'],
    'ssl_engine':                   ['_'],
    'timer_resolution':             ['_'],
    'user':                         ['_'],
    'worker_cpu_affinity':          ['_'],
    'worker_priority':              ['_'],
    'worker_processes':             ['_'],
    'worker_rlimit_core':           ['_'],
    'worker_rlimit_nofile':         ['_'],
    'worker_rlimit_sigpending':     ['_'],
    'working_directory':            ['_'],

    # REF: http://wiki.nginx.org/EventsModule
    'events':                       ['_'],
    'accept_mutex':                 ['events'],
    'accept_mutex_delay':           ['events'],
    'debug_connection':             ['events'],
    'devpoll_changes':              ['events'],
    'devpoll_events':               ['events'],
    'kqueue_changes':               ['events'],
    'kqueue_events':                ['events'],
    'epoll_events':                 ['events'],
    'multi_accept':                 ['events'],
    'rtsig_signo':                  ['events'],
    'rtsig_overflow_events':        ['events'],
    'rtsig_overflow_test':          ['events'],
    'rtsig_overflow_threshold':     ['events'],
    'use':                          ['events'],
    'worker_connections':           ['events'],

    # REF: http://wiki.nginx.org/HttpCoreModule
    'http':                         ['_'],
    'aio':                          ['http', 'server', 'location'],
    'alias':                        ['location'],
    'chunked_transfer_encoding':    ['http', 'server', 'location'],
    'client_body_in_file_only':     ['http', 'server', 'location'],
    'client_body_in_single_buffer': ['http', 'server', 'location'],
    'client_body_buffer_size':      ['http', 'server', 'location'],
    'client_body_temp_path':        ['http', 'server', 'location'],
    'client_body_timeout':          ['http', 'server', 'location'],
    'client_header_buffer_size':    ['http', 'server'],
    'client_header_timeout':        ['http', 'server'],
    'client_max_body_size':         ['http', 'server', 'location'],
    'connection_pool_size':         ['http', 'server'],
    'default_type':                 ['http', 'server', 'location'],
    'directio':                     ['http', 'server', 'location'],
    'directio_alignment':           ['http', 'server', 'location'],
    'disable_symlinks':             ['http', 'server', 'location'],
    'error_page':                   ['http', 'server', 'location', 'if in location', 'if'], #+if
    'if_modified_since':            ['http', 'server', 'location'],
    'ignore_invalid_headers':       ['http', 'server'],
    'internal':                     ['location'],
    'keepalive_disable':            ['http', 'server', 'location'],
    'keepalive_timeout':            ['http', 'server', 'location'],
    'keepalive_requests':           ['http', 'server', 'location'],
    'large_client_header_buffers':  ['http', 'server'],
    'limit_except':                 ['location'],
    'limit_rate':                   ['http', 'server', 'location', 'if in location', 'if'], #+if
    'limit_rate_after':             ['http', 'server', 'location', 'if in location', 'if'], #+if
    'lingering_close':              ['http', 'server', 'location'],
    'lingering_time':               ['http', 'server', 'location'],
    'lingering_timeout':            ['http', 'server', 'location'],
    'listen':                       ['server'],
    'location':                     ['server', 'location'],
    'log_not_found':                ['http', 'server', 'location'],
    'log_subrequest':               ['http', 'server', 'location'],
    'max_ranges':                   ['http', 'server', 'location'],
    'merge_slashes':                ['http', 'server'],
    'msie_padding':                 ['http', 'server', 'location'],
    'msie_refresh':                 ['http', 'server', 'location'],
    'open_file_cache':              ['http', 'server', 'location'],
    'open_file_cache_errors':       ['http', 'server', 'location'],
    'open_file_cache_min_uses':     ['http', 'server', 'location'],
    'open_file_cache_valid':        ['http', 'server', 'location'],
    'optimize_server_names':        ['http', 'server'],
    'port_in_redirect':             ['http', 'server', 'location'],
    'post_action':                  ['http', 'server', 'location'],
    'postpone_output':              ['http', 'server', 'location'],
    'read_ahead':                   ['http', 'server', 'location'],
    'recursive_error_pages':        ['http', 'server', 'location'],
    'request_pool_size':            ['http', 'server'],
    'reset_timedout_connection':    ['http', 'server', 'location'],
    'resolver':                     ['http', 'server', 'location'],
    'resolver_timeout':             ['http', 'server', 'location'],
    'root':                         ['http', 'server', 'location', 'if in location', 'if'], #+if
    'satisfy':                      ['http', 'server', 'location'],
    'satisfy_any':                  ['http', 'server', 'location'],
    'send_lowat':                   ['http', 'server', 'location'],
    'send_timeout':                 ['http', 'server', 'location'],
    'sendfile':                     ['http', 'server', 'location', 'if in location', 'if'], #+if
    'sendfile_max_chunk':           ['http', 'server', 'location'],
    'server':                       ['http', 'upstream'],
    'server_name':                  ['server'],
    'server_name_in_redirect':      ['http', 'server', 'location'],
    'server_names_hash_max_size':   ['http'],
    'server_names_hash_bucket_size':['http'],
    'server_tokens':                ['http', 'server', 'location'],
    'tcp_nodelay':                  ['http', 'server', 'location'],
    'tcp_nopush':                   ['http', 'server', 'location'],
    'try_files':                    ['server', 'location'],
    'types':                        ['http', 'server', 'location'],
    'types_hash_bucket_size':       ['http', 'server', 'location'],
    'types_hash_max_size':          ['http', 'server', 'location'],
    'underscores_in_headers':       ['http', 'server'],
    'variables_hash_bucket_size':   ['http'],
    'variables_hash_max_size':      ['http'],

    # REF: http://wiki.nginx.org/HttpAccessModule
    'allow':                        ['http', 'server', 'location', 'limit_except'],
    'deny':                         ['http', 'server', 'location', 'limit_except'],

    # REF: http://wiki.nginx.org/HttpAuthBasicModule
    'auth_basic':                   ['http', 'server', 'location', 'limit_except'],
    'auth_basic_user_file':         ['http', 'server', 'location', 'limit_except'],

    # REF: http://wiki.nginx.org/HttpAutoindexModule
    'autoindex':                    ['http', 'server', 'location'],
    'autoindex_exact_size':         ['http', 'server', 'location'],
    'autoindex_localtime':          ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpBrowserModule
    'ancient_browser':              ['http', 'server', 'location'],
    'ancient_browser_value':        ['http', 'server', 'location'],
    'modern_browser':               ['http', 'server', 'location'],
    'modern_browser_value':         ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpCharsetModule
    'charset':                      ['http', 'server', 'location', 'if in location', 'if'], #+if
    'charset_map':                  ['http'],
    'charset_types':                ['http', 'server', 'location'],
    'override_charset':             ['http', 'server', 'location', 'if in location', 'if'], #+if
    'source_charset':               ['http', 'server', 'location', 'if in location', 'if'], #+if
    
    # REF: http://wiki.nginx.org/HttpEmptyGifModule
    'empty_gif':                    ['location'],
    
    # REF: http://wiki.nginx.org/HttpFastcgiModule
    'fastcgi_bind':                 ['http', 'server', 'location'],
    'fastcgi_buffer_size':          ['http', 'server', 'location'],
    'fastcgi_buffers':              ['http', 'server', 'location'],
    'fastcgi_busy_buffers_size':    ['http', 'server', 'location'],
    'fastcgi_cache':                ['http', 'server', 'location'],
    'fastcgi_cache_bypass':         ['http', 'server', 'location'],
    'fastcgi_cache_key':            ['http', 'server', 'location'],
    'fastcgi_cache_lock':           ['http', 'server', 'location'],
    'fastcgi_cache_lock_timeout':   ['http', 'server', 'location'],
    'fastcgi_cache_methods':        ['http', 'server', 'location'],
    'fastcgi_cache_min_uses':       ['http', 'server', 'location'],
    'fastcgi_cache_path':           ['http'],
    'fastcgi_cache_use_stale':      ['http', 'server', 'location'],
    'fastcgi_cache_valid':          ['http', 'server', 'location'],
    'fastcgi_connect_timeout':      ['http', 'server', 'location'],
    'fastcgi_hide_header':          ['http', 'server', 'location'],
    'fastcgi_ignore_client_abort':  ['http', 'server', 'location'],
    'fastcgi_ignore_headers':       ['http', 'server', 'location'],
    'fastcgi_index':                ['http', 'server', 'location'],
    'fastcgi_intercept_errors':     ['http', 'server', 'location'],
    'fastcgi_keep_conn':            ['http', 'server', 'location'],
    'fastcgi_max_temp_file_size':   ['http', 'server', 'location'],
    'fastcgi_next_upstream':        ['http', 'server', 'location'],
    'fastcgi_no_cache':             ['http', 'server', 'location'],
    'fastcgi_param':                ['http', 'server', 'location'],
    'fastcgi_pass':                 ['location', 'if in location', 'if'], #+if
    'fastcgi_pass_header':          ['http', 'server', 'location'],
    'fastcgi_pass_request_body':    ['http', 'server', 'location'],
    'fastcgi_pass_request_headers': ['http', 'server', 'location'],
    'fastcgi_read_timeout':         ['http', 'server', 'location'],
    'fastcgi_redirect_errors':      ['http', 'server', 'location'],
    'fastcgi_send_timeout':         ['http', 'server', 'location'],
    'fastcgi_split_path_info':      ['location'],
    'fastcgi_store':                ['http', 'server', 'location'],
    'fastcgi_store_access':         ['http', 'server', 'location'],
    'fastcgi_temp_file_write_size': ['http', 'server', 'location'],
    'fastcgi_temp_path':            ['http', 'server', 'location'],

    # REF: http://wiki.nginx.org/HttpGeoModule
    'geo':                          ['http'],

    # REF: http://wiki.nginx.org/HttpGzipModule
    'gzip':                         ['http', 'server', 'location', 'if in location', 'if'], #+if
    'gzip_buffers':                 ['http', 'server', 'location'],
    'gzip_comp_level':              ['http', 'server', 'location'],
    'gzip_disable':                 ['http', 'server', 'location'],
    'gzip_http_version':            ['http', 'server', 'location'],
    'gzip_min_length':              ['http', 'server', 'location'],
    'gzip_proxied':                 ['http', 'server', 'location'],
    'gzip_types':                   ['http', 'server', 'location'],
    'gzip_vary':                    ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpHeadersModule
    'add_header':                   ['http', 'server', 'location'],
    'expires':                      ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpIndexModule
    'index':                        ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpLimitReqModule
    'limit_req':                    ['http', 'server', 'location'],
    'limit_req_log_level':          ['http', 'server', 'location'],
    'limit_req_zone':               ['http'],

    # Deprecated in 1.1.8
    # REF: http://wiki.nginx.org/HttpLimitZoneModule
    'limit_zone':                    ['http'],
    #'limit_conn':                    ['http', 'server', 'location'],
    #'limit_conn_log_level':          ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpLimitConnModule
    'limit_conn':                   ['http', 'server', 'location'],
    'limit_conn_zone':              ['http'],
    'limit_conn_log_level':         ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpLogModule
    'access_log':                   ['http', 'server', 'location', 'if in location', 'limit_except', 'if'], #+if
    'log_format':                   ['http'],
    'open_log_file_cache':          ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpMapModule
    'map':                          ['http'],
    'map_hash_max_size':            ['http'],
    'map_hash_bucket_size':         ['http'],
    
    # REF: http://wiki.nginx.org/HttpMemcachedModule
    'memcached_pass':               ['location', 'if in location', 'if'], #+if
    'memcached_connect_timeout':    ['http', 'server', 'location'],
    'memcached_read_timeout':       ['http', 'server', 'location'],
    'memcached_send_timeout':       ['http', 'server', 'location'],
    'memcached_buffer_size':        ['http', 'server', 'location'],
    'memcached_next_upstream':      ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpProxyModule
    'proxy_bind':                   ['http', 'server', 'location'],
    'proxy_buffer_size':            ['http', 'server', 'location'],
    'proxy_buffering':              ['http', 'server', 'location'],
    'proxy_buffers':                ['http', 'server', 'location'],
    'proxy_busy_buffers_size':      ['http', 'server', 'location'],
    'proxy_cache':                  ['http', 'server', 'location'],
    'proxy_cache_bypass':           ['http', 'server', 'location'],
    'proxy_cache_key':              ['http', 'server', 'location'],
    'proxy_cache_lock':             ['http', 'server', 'location'],
    'proxy_cache_lock_timeout':     ['http', 'server', 'location'],
    'proxy_cache_methods':          ['http', 'server', 'location'],
    'proxy_cache_min_uses':         ['http', 'server', 'location'],
    'proxy_cache_path':             ['http'],
    'proxy_cache_use_stale':        ['http', 'server', 'location'],
    'proxy_cache_valid':            ['http', 'server', 'location'],
    'proxy_connect_timeout':        ['http', 'server', 'location'],
    'proxy_cookie_domain':          ['http', 'server', 'location'],
    'proxy_cookie_path':            ['http', 'server', 'location'],
    'proxy_headers_hash_bucket_size':['http', 'server', 'location'],
    'proxy_headers_hash_max_size':  ['http', 'server', 'location'],
    'proxy_hide_header':            ['http', 'server', 'location'],
    'proxy_http_version':           ['http', 'server', 'location'],
    'proxy_ignore_client_abort':    ['http', 'server', 'location'],
    'proxy_ignore_headers':         ['http', 'server', 'location'],
    'proxy_intercept_errors':       ['http', 'server', 'location'],
    'proxy_max_temp_file_size':     ['http', 'server', 'location'],
    'proxy_method':                 ['http', 'server', 'location'],
    'proxy_next_upstream':          ['http', 'server', 'location'],
    'proxy_no_cache':               ['http', 'server', 'location'],
    'proxy_pass':                   ['location', 'if in location', 'limit_except', 'if'], #+if
    'proxy_pass_header':            ['http', 'server', 'location'],
    'proxy_pass_request_body':      ['http', 'server', 'location'],
    'proxy_pass_request_headers':   ['http', 'server', 'location'],
    'proxy_redirect':               ['http', 'server', 'location'],
    'proxy_read_timeout':           ['http', 'server', 'location'],
    'proxy_redirect_errors':        ['http', 'server', 'location'],
    'proxy_send_lowat':             ['http', 'server', 'location'],
    'proxy_send_timeout':           ['http', 'server', 'location'],
    'proxy_set_body':               ['http', 'server', 'location'],
    'proxy_set_header':             ['http', 'server', 'location'],
    'proxy_ssl_session_reuse':      ['http', 'server', 'location'],
    'proxy_store':                  ['http', 'server', 'location'],
    'proxy_store_access':           ['http', 'server', 'location'],
    'proxy_temp_file_write_size':   ['http', 'server', 'location'],
    'proxy_temp_path':              ['http', 'server', 'location'],
    'proxy_upstream_fail_timeout':  ['http', 'server', 'location'],
    'proxy_upstream_max_fails':     ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpRefererModule
    'valid_referers':               ['server', 'location'],

    # REF: http://wiki.nginx.org/HttpRewriteModule
    'break':                        ['server', 'location', 'if'],
    'if':                           ['server', 'location'],
    'return':                       ['server', 'location', 'if'],
    'rewrite':                      ['server', 'location', 'if'],
    'rewrite_log':                  ['server', 'location', 'if'],
    'set':                          ['server', 'location', 'if'],
    'uninitialized_variable_warn':  ['server', 'location', 'if'],
    
    # REF: http://wiki.nginx.org/HttpScgiModule
    'scgi_bind':                    ['http', 'server', 'location'],
    'scgi_buffer_size':             ['http', 'server', 'location'],
    'scgi_buffering':               ['http', 'server', 'location'],
    'scgi_buffers':                 ['http', 'server', 'location'],
    'scgi_busy_buffers_size':       ['http', 'server', 'location', 'if'],
    'scgi_cache':                   ['http', 'server', 'location'],
    'scgi_cache_bypass':            ['http', 'server', 'location'],
    'scgi_cache_key':               ['http', 'server', 'location'],
    'scgi_cache_methods':           ['http', 'server', 'location'],
    'scgi_cache_min_uses':          ['http', 'server', 'location'],
    'scgi_cache_path':              ['http'],
    'scgi_cache_use_stale':         ['http', 'server', 'location'],
    'scgi_cache_valid':             ['http', 'server', 'location'],
    'scgi_connect_timeout':         ['http', 'server', 'location'],
    'scgi_hide_header':             ['http', 'server', 'location'],
    'scgi_ignore_client_abort':     ['http', 'server', 'location'],
    'scgi_ignore_headers':          ['http', 'server', 'location'],
    'scgi_intercept_errors':        ['http', 'server', 'location'],
    'scgi_max_temp_file_size':      ['http', 'server', 'location'], #?
    'scgi_next_upstream':           ['http', 'server', 'location'],
    'scgi_no_cache':                ['http', 'server', 'location'],
    'scgi_param':                   ['http', 'server', 'location'],
    'scgi_pass':                    ['location', 'if in location', 'if'], #+if
    'scgi_pass_header':             ['http', 'server', 'location'],
    'scgi_pass_request_body':       ['http', 'server', 'location'],
    'scgi_pass_request_headers':    ['http', 'server', 'location'],
    'scgi_read_timeout':            ['http', 'server', 'location'],
    'scgi_send_timeout':            ['http', 'server', 'location'],
    'scgi_store':                   ['http', 'server', 'location'],
    'scgi_store_access':            ['http', 'server', 'location'],
    'scgi_temp_file_write_size':    ['http', 'server', 'location'],
    'scgi_temp_path':               ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpSplitClientsModule
    'split_clients':                ['http'],
    
    # REF: http://wiki.nginx.org/HttpSsiModule
    'ssi':                          ['http', 'server', 'location', 'if in location', 'if'], #+if
    'ssi_silent_errors':            ['http', 'server', 'location'],
    'ssi_types':                    ['http', 'server', 'location'],
    'ssi_value_length':             ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpUpstreamModule
    'ip_hash':                      ['upstream'],
    'keepalive':                    ['upstream'],
    'least_conn':                   ['upstream'],
    #'server':                       ['upstream'],
    'upstream':                     ['http'],
    
    # REF: http://wiki.nginx.org/HttpUseridModule
    'userid':                       ['http', 'server', 'location'],
    'userid_domain':                ['http', 'server', 'location'],
    'userid_expires':               ['http', 'server', 'location'],
    'userid_name':                  ['http', 'server', 'location'],
    'userid_p3p':                   ['http', 'server', 'location'],
    'userid_path':                  ['http', 'server', 'location'],
    'userid_service':               ['http', 'server', 'location'],
    
    # REF: http://wiki.nginx.org/HttpUwsgiModule
    'uwsgi_bind':                   ['http', 'server', 'location'],
    'uwsgi_buffer_size':            ['http', 'server', 'location'],
    'uwsgi_buffering':              ['http', 'server', 'location'],
    'uwsgi_buffers':                ['http', 'server', 'location'],
    'uwsgi_busy_buffers_size':      ['http', 'server', 'location', 'if'],
    'uwsgi_cache':                  ['http', 'server', 'location'],
    'uwsgi_cache_bypass':           ['http', 'server', 'location'],
    'uwsgi_cache_key':              ['http', 'server', 'location'],
    'uwsgi_cache_lock':             ['http', 'server', 'location'],
    'uwsgi_cache_lock_timeout':     ['http', 'server', 'location'],
    'uwsgi_cache_methods':          ['http', 'server', 'location'],
    'uwsgi_cache_min_uses':         ['http', 'server', 'location'],
    'uwsgi_cache_path':             ['http', 'server', 'location'],
    'uwsgi_cache_use_stale':        ['http', 'server', 'location'],
    'uwsgi_cache_valid':            ['http', 'server', 'location'],
    'uwsgi_connect_timeout':        ['http', 'server', 'location'],
    'uwsgi_hide_header':            ['http', 'server', 'location'],
    'uwsgi_ignore_client_abort':    ['http', 'server', 'location'],
    'uwsgi_ignore_headers':         ['http', 'server', 'location'],
    'uwsgi_intercept_errors':       ['http', 'server', 'location'],
    'uwsgi_max_temp_file_size':     ['http', 'server', 'location'], #?
    'uwsgi_modifier1':              ['server', 'location'],
    'uwsgi_modifier2':              ['server', 'location'],
    'uwsgi_next_upstream':          ['http', 'server', 'location'],
    'uwsgi_no_cache':               ['http', 'server', 'location'],
    'uwsgi_param':                  ['http', 'server', 'location'],
    'uwsgi_pass':                   ['location', 'if in location', 'if'], #+if
    'uwsgi_pass_header':            ['http', 'server', 'location'],
    'uwsgi_pass_request_body':      ['http', 'server', 'location'],
    'uwsgi_pass_request_headers':   ['http', 'server', 'location'],
    'uwsgi_read_timeout':           ['http', 'server', 'location'],
    'uwsgi_send_timeout':           ['http', 'server', 'location'],
    'uwsgi_store':                  ['http', 'server', 'location'],
    'uwsgi_store_access':           ['http', 'server', 'location'],
    'uwsgi_string':                 ['server', 'location'],
    'uwsgi_temp_file_write_size':   ['http', 'server', 'location', 'if'],
    'uwsgi_temp_path':              ['http', 'server', 'location'],

    # REF: http://wiki.nginx.org/HttpSslModule
    'ssl':                          ['http', 'server'],
    'ssl_certificate':              ['http', 'server'],
    'ssl_certificate_key':          ['http', 'server'],
    'ssl_ciphers':                  ['http', 'server'],
    'ssl_client_certificate':       ['http', 'server'],
    'ssl_crl':                      ['http', 'server'],
    'ssl_dhparam':                  ['http', 'server'],
    'ssl_prefer_server_ciphers':    ['http', 'server'],
    'ssl_protocols':                ['http', 'server'],
    'ssl_verify_client':            ['http', 'server'],
    'ssl_verify_depth':             ['http', 'server'],
    'ssl_session_cache':            ['http', 'server'],
    'ssl_session_timeout':          ['http', 'server'],
    'ssl_engine':                   ['http', 'server'],
    
    # REF: http://wiki.nginx.org/X-accel
    # no directive
}
# module name : can has param if act as a context
# if False then a module name with param would considered a directive
MODULES = {
    'events':       False,
    'http':         False,
    'server':       False,
    'upstream':     True,
    'location':     True,
    'types':        False,
    'if':           True,
    'limit_except': True,
}
DEFAULTVALS = {
    'client_max_body_size': '1m',
    'keepalive_timeout': '75s',
}
NGINXCONF = '/etc/nginx/nginx.conf'
SERVERCONF = '/etc/nginx/conf.d/'
COMMENTFLAG = '#v#'
GENBY='Generated by VPSMate'

def loadconfig(conf=None, getlineinfo=False):
    """Load nginx config and return a dict.
    """
    if not conf: conf = NGINXCONF
    if not os.path.exists(conf): return False
    return _loadconfig(conf, getlineinfo)
    
def _loadconfig(conf, getlineinfo, config=None, context_stack=None):
    """Recursively load nginx config and return a dict.
    """
    if not config:
        file_i = 0
        context = '_'
        config = {'_files': [conf], '_': [{}], '_isdirty': False}
        context_stack = [context]
        cconfig = config[context][-1]
    else:
        if getlineinfo:
            if conf not in config['_files']:
                file_i = len(config['_files'])
                config['_files'].append(conf)
            else:
                file_i = config['_files'].index(conf)
        cconfig = config
        for c in context_stack: cconfig = cconfig[c][-1]
        context = context_stack[-1]

    line_buffer = []
    
    with open(conf) as f:
        for line_i, line in enumerate(f):
            line = line.strip()
            if DEBUG: print '----------', line

            # deal with our speical comment string
            line_disabled = False
            if line.startswith(COMMENTFLAG):
                while line.startswith(COMMENTFLAG): line = line[3:]
                line = line.strip()
                line_disabled = True

            if not line or line.startswith('#'): continue
            
            # deal with comment and detect vpsmate flag in comment
            fields = line.split('#', 1)
            line = fields[0].strip()
            gen_by_vpsmate = False
            if len(fields) > 1 and fields[1].strip() == GENBY:
                gen_by_vpsmate = True

            # context up
            if line == '}':
                if getlineinfo:
                    cconfig['_range']['end'] = {'file': file_i, 'line': [line_i, 1]}
                if DEBUG: print context_stack, '-', context_stack[-1], 
                context_stack.pop()
                context = context_stack[-1]
                if DEBUG: print '=', context_stack
                cconfig = config
                for c in context_stack: cconfig = cconfig[c][-1]
                continue

            # this line may not ending, combine it with next line
            if line[-1] not in (';', '{', '}'):
                line_buffer.append(line)
                continue
            elif len(line_buffer)>0:
                line_buffer.append(line)
                line = ''.join(line_buffer)
                line_count = len(line_buffer)
                line_buffer = []
            else:
                line_count = 1

            # only support one directive at a line
            ## one line may contain serveral directives
            #parts = re.split('[;{}]', line)
            #for part_i, part in enumerate(parts):
            #    if not part or part.startswith('#'): continue
            #    fields = part.split()
            fields = line.split()
            key = fields[0].strip(';')  # some directive have no value like ip_hash
            #value = ' '.join(fields[1:]).strip()
            value = ' '.join(fields[1:]).strip(';')

            if DIRECTIVES.has_key(key) and context in DIRECTIVES[key]:
                if (not MODULES.has_key(key)    # not in module name list
                     or MODULES.has_key(key)    # or in module name list
                        and not MODULES[key]    # and this module can't has param
                        and value != '{'):      # but actually it has
                    if getlineinfo:
                        v = {'file': file_i, 'line': [line_i-line_count+1, line_count], 'value': value}
                    else:
                        v = value
                    if cconfig.has_key(key):
                        cconfig[key].append(v)
                    else:
                        cconfig[key] = [v]
                    if key == 'include':    # expand include files
                        includepath = value
                        if not includepath.startswith('/'):
                            includepath = os.path.join(os.path.dirname(config['_files'][0]), includepath)
                        confs = glob.glob(includepath)
                        # order by domain name, excluding tld
                        getdm = lambda x: x.split('/')[-1].split('.')[-3::-1]
                        confs = sorted(confs, lambda x,y: cmp(getdm(x), getdm(y)))
                        for subconf in confs:
                            if os.path.exists(subconf):
                                if DEBUG: print '\n**********', subconf, '\n'
                                _loadconfig(subconf, getlineinfo, config, context_stack)
                else:
                    context = key
                    if DEBUG: print context_stack, '+', context,
                    context_stack.append(context)
                    if DEBUG: print '=', context_stack
                    if cconfig.has_key(context):
                        cconfig[context].append({})
                    else:
                        cconfig[context] = [{}]
                    cconfig = cconfig[context][-1]
                    value = value.strip('{').strip()
                    if getlineinfo:
                        cconfig['_param'] =  {'file': file_i, 'line': [line_i-line_count+1, line_count], 'disabled': line_disabled, 'value': value}
                        # record the context range
                        cconfig['_range'] = {'begin': {'file': file_i, 'line': [line_i-line_count+1, line_count]}}
                        cconfig['_vpsmate'] = gen_by_vpsmate
                    else:
                        cconfig['_param'] =  value
                        cconfig['_disabled'] = line_disabled
                        cconfig['_vpsmate'] = gen_by_vpsmate

    return config

def _context_gethttp(config=None):
    """Get http context config.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, True)
    return config['_'][0]['http'][0]

def _context_getservers(disabled=None, config=None, getlineinfo=True):
    """Get server context configs.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, getlineinfo)
    http = config['_'][0]['http'][0]
    if not http.has_key('server'): return []
    servers = http['server']
    if disabled == None or not getlineinfo:
        return servers
    else:
        return [server for server in servers
                if server['_param']['disabled']==disabled]

def _context_getserver(ip, port, server_name, config=None, disabled=None, getlineinfo=True):
    """Get a server context config by server name.
    
    If disabled is set to None, all servers would be return.
    If disabled is set to True, only disabled servers would be return.
    If disabled is set to False, only normal servers would be return.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, getlineinfo)
    cnfservers = _context_getservers(disabled=disabled, config=config, getlineinfo=getlineinfo)
    if not ip or ip in ('*', '0.0.0.0'): ip = ''
    for s in cnfservers:
        if getlineinfo:
            server_names = ' '.join([v['value'] for v in s['server_name']]).split()
            listens = [v['value'].split()[0] for v in s['listen']]
        else:
            server_names = ' '.join([v for v in s['server_name']]).split()
            listens = [v.split()[0] for v in s['listen']]
        find_listen = ip and ['%s:%s' % (ip, port)] or [port, '*:%s' % port, '0.0.0.0:%s' % port];
        if server_name in server_names and any([i in listens for i in find_listen]):
            return s
    return False

def _context_getupstreams(server_name, config=None, disabled=None, getlineinfo=True):
    """Get upstream list related to a server.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, getlineinfo)
    upstreams = http_get('upstream', config)
    if not upstreams: return False
    if getlineinfo:
        upstreams = [upstream for upstream in upstreams 
            if upstream['_param']['value'].startswith('backend_of_%s_' % server_name)]
    else:
        upstreams = [upstream for upstream in upstreams 
            if upstream['_param'].startswith('backend_of_%s_' % server_name)]
        
    if disabled == None or not getlineinfo:
        return upstreams
    else:
        return [upstream for upstream in upstreams
                if upstream['_param']['disabled']==disabled]

def _comment(filepath, start, end):
    """Commend some lines in the file.
    """
    if not os.path.exists(filepath): return False
    data = []
    with open(filepath) as f:
        for i, line in enumerate(f):
            if i>=start and i<=end:
                if not line.startswith(COMMENTFLAG): data.append(COMMENTFLAG)
            data.append(line)
    with open(filepath, 'w') as f: f.write(''.join(data))
    return True

def _uncomment(filepath, start, end):
    """Uncommend some lines in the file.
    """
    if not os.path.exists(filepath): return False
    data = []
    with open(filepath) as f:
        for i, line in enumerate(f):
            if i>=start and i<=end:
                while line.startswith(COMMENTFLAG): line = line[3:]
            data.append(line)
    with open(filepath, 'w') as f: f.write(''.join(data))
    return True

def _delete(filepath, start, end, delete_emptyfile=True):
    """Delete some lines in the file.
    
    If delete_emptyfile is set to True, then the empty file will 
    be deleted from file system.
    """
    if not os.path.exists(filepath): return False
    data = []
    with open(filepath) as f:
        for i, line in enumerate(f):
            if i>=start and i<=end: continue
            data.append(line)
    with open(filepath, 'w') as f: f.write(''.join(data))
    if delete_emptyfile:
        if ''.join(data).strip() == '': os.unlink(filepath)
    return True

def _getcontextrange(context, config):
    """Return the range of the input context, including the file path.
    
    Return format:
    [filepath, line_start, line_end]
    """
    file_i = context['_range']['begin']['file']
    filepath = config['_files'][file_i]
    line_start = context['_range']['begin']['line'][0]
    line_end = context['_range']['end']['line'][0]
    return [filepath, line_start, line_end]

def _context_commentserver(ip, port, server_name, config=None):
    """Comment a context using VPSMate's special comment string '#v#'
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, True)
    scontext = _context_getserver(ip, port, server_name, config=config)
    if not scontext: return False
    filepath, line_start, line_end = _getcontextrange(scontext, config)
    return _comment(filepath, line_start, line_end)

def _context_uncommentserver(ip, port, server_name, config=None):
    """Uncomment a VPSMate's special-commented context.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, True)
    scontext = _context_getserver(ip, port, server_name, config=config)
    if not scontext: return False
    filepath, line_start, line_end = _getcontextrange(scontext, config)
    return _uncomment(filepath, line_start, line_end)

def _context_deleteserver(ip, port, server_name, config=None, disabled=None):
    """Delete a server context.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, True)
    scontext = _context_getserver(ip, port, server_name, config=config, disabled=disabled)
    if not scontext: return False
    filepath, line_start, line_end = _getcontextrange(scontext, config)
    config['_isdirty'] = True
    return _delete(filepath, line_start, line_end)

def _context_commentupstreams(server_name, config=None):
    """Comment upstreams by server names.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, True)
    upstreams = _context_getupstreams(server_name, config=config)
    if not upstreams: return True
    for upstream in upstreams:
        filepath, line_start, line_end = _getcontextrange(upstream, config)
        if not _comment(filepath, line_start, line_end): return False
    return True

def _context_uncommentupstreams(server_name, config=None):
    """Uncomment upstreams by server names.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, True)
    upstreams = _context_getupstreams(server_name, config=config)
    if not upstreams: return True
    for upstream in upstreams:
        filepath, line_start, line_end = _getcontextrange(upstream, config)
        if not _uncomment(filepath, line_start, line_end): return False
    return True

def _context_deleteupstreams(server_name, config=None, disabled=None):
    """Delete upstreams by server name.
    """
    while True:
        # we need to reload config after delete one upstream
        if not config or config['_isdirty']:
            config = loadconfig(NGINXCONF, True)
        upstreams = _context_getupstreams(server_name, config=config, disabled=disabled)
        if not upstreams: return True
        for upstream in upstreams:
            filepath, line_start, line_end = _getcontextrange(upstream, config)
            config['_isdirty'] = True
            if not _delete(filepath, line_start, line_end): return False
            break   # only delete the first one
    return True

def _context_http_init_limit_conn(config=None, version=None):
    """Init limit_conn_zone in http context.

    We only recognize limit_conn_zone with name "addr".
    
    Return True if initialized do.
    Or False if nothing to do with it.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, True)

    if not version or utils.version_get(version, '1.1.8'):
        conn_zones = http_get('limit_conn_zone')
        if not conn_zones:
            http_set('limit_conn_zone', '$binary_remote_addr zone=addr:10m', config)
            return True
        else:
            addr_conn_zone_found = False
            for conn_zone in conn_zones:
                zonename = conn_zone.split('zone=', 1)[-1].split(':', 1)[0]
                if zonename == 'addr':
                    addr_conn_zone_found = True
                    break
            if not addr_conn_zone_found:
                conn_zones.append('$binary_remote_addr zone=addr:10m')
                http_set('limit_conn_zone', conn_zones, config)
                return True
            else:
                return False
    else:
        conn_zones = http_get('limit_zone')
        if not conn_zones:
            http_set('limit_zone', 'addr $binary_remote_addr 10m', config)
            return True
        else:
            addr_conn_zone_found = False
            for conn_zone in conn_zones:
                zonename = conn_zone.split()[0]
                if zonename == 'addr':
                    addr_conn_zone_found = True
                    break
            if not addr_conn_zone_found:
                conn_zones.append('addr $binary_remote_addr 10m')
                http_set('limit_zone', conn_zones, config)
                return True
            else:
                return False
        

def _context_server_clear_default_server(ip, port, config=None):
    """Clear the default_server flag at specified ip:port.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, True)
    cnfservers = _context_getservers(config=config)
    found = False
    for cnfserver in cnfservers:
        listens = cnfserver['listen']
        for listen in listens:
            if 'default_server' in listen['value']:
                _replace([(config['_files'][listen['file']], listen['line'][0], listen['line'][1])],
                        ['listen %s;' % listen['value'].replace('default_server', '').strip()])
                found = True
                break
        if found: break
    return found

def _replace(positions, lines):
    """Replace the lines specified in list positions to new lines.
    
    Structure of positions:
    [
        (filepath, line_start, line_count),
        ...
    ]
    Parameter positions can not be empty.

    * If the new lines is empty, old lines with be deleted.
    * If the new lines is less than the old lines, the rest old lines
      will also be deleted.
    * If the new lines is more than the old lines, then new value will 
      append after the last line of the old lines.
    """
    # merge line positions by filepath
    # struct: {'/path/to/file': [3, 4, 10, ...], ...}
    files = {}
    for pos in positions:
        filepath, line_start, line_count = pos
        if not files.has_key(filepath): files[filepath] = []
        for i in range(line_count):
            files[filepath].append(line_start+i)
    # replace line by line
    for filepath, line_nums in files.iteritems():
        flines = []
        with open(filepath) as f:
            for i, fline in enumerate(f):
                if i in line_nums:
                    if len(lines) > 0:
                        # replace with a new line
                        line = lines[0]
                        lines = lines[1:]
                        # detect the space at the start of the old line
                        # this aim to keep the indent of the line
                        space = ''
                        for c in fline:
                            if c not in (' ', '\t'): break
                            space += c
                        flines.append(''.join([space, line, '\n']))
                    else:
                        # no more new line, delete the old line
                        continue
                else:
                    if i > line_nums[-1] and len(lines) > 0:
                        # exceed the last old line, insert the rest new lines here
                        # detect the indent of the last line
                        space = ''
                        if len(flines)>0: # last line exists
                            for c in flines[-1]:
                                if c not in (' ', '\t'): break
                                space += c
                        for line in lines:
                            flines.append(''.join([space, line, '\n']))
                        lines = []
                    flines.append(fline)
        # write back to file
        with open(filepath, 'w') as f: f.write(''.join(flines))

def _insert(filepath, line_start, lines):
    """Insert the lines to the specified position.
    """
    flines = []
    with open(filepath) as f:
        for i, fline in enumerate(f):
            if i == line_start:
                # detect the indent of the last not empty line
                space = ''
                flines_len = len(flines)
                if flines_len>0: # last line exists
                    line_i = -1
                    while flines[line_i].strip() == '' and -line_i <= flines_len:
                        line_i -= 1
                    for c in flines[line_i]:
                            if c not in (' ', '\t'): break
                            space += c
                    if flines[line_i].strip().endswith('{'):
                        space += '    '
                for line in lines:
                    flines.append(''.join([space, line, '\n']))
            flines.append(fline)
    # write back to file
    with open(filepath, 'w') as f: f.write(''.join(flines))

def _detect_engines(context):
    """Detect engines in context.
    """
    engine_flags = {
        'root' : 'static',
        'alias' : 'static_alias',
        'fastcgi_pass': 'fastcgi',
        'scgi_pass': 'scgi',
        'uwsgi_pass': 'uwsgi',
        'proxy_pass': 'proxy',
        'rewrite': 'rewrite',
        'return': 'return',
    }
    contexts = ['location', 'if', 'limit_except']

    engines = []
    for k, v in context.iteritems():
        if engine_flags.has_key(k):
            if k == 'rewrite':
                engines.extend([x and 'redirect' or 'rewrite' for x in _isredirect(v)])
            else:
                engines.append(engine_flags[k])
        elif k in contexts:
            for ctx in context[k]:
                engines.extend(_detect_engines(ctx))

    # return a uniq result
    engines = list(set(engines))
    if 'static_alias' in engines:
        if len(engines) == 1:
            engines[0] = 'static'
        else:
            engines = filter(lambda a: a != 'static_alias', engines)
    return engines
        
def _isredirect(values):
    """Check if rewrite values is redirect.
    """
    return [v.split().pop() in ('redirect', 'permanent') for v in values]
    
def getservers(config=None):
    """Get servers from nginx configuration files.

    Struct of server dict:
    {
        'server_names': [
            'test.com',
            'www.test.com'
        ],
        'listens': [
            {'ip': '192.168.1.2', 'port': '80', 'default_server': true},
            {'ip': '*', 'port': '88', 'default_server': false}
        ],
        'engines': [
            'static',
            'rewrite',
            'redirect',
            'fastcgi',
            'scgi',
            'uwsgi',
            'proxy',
        ],
    }
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF)   # do not need to load lineinfo
    cnfservers = _context_getservers(config=config)
    servers = []
    for s in cnfservers:
        server = {}
        server['server_names'] = ' '.join(s['server_name']).split()
        
        # parse server and port, and check if is default server
        server['listens'] = []
        for listen in s['listen']:
            default_server = False
            if 'default_server' in listen: default_server = True
            for item in listen.split():
                fs = item.split(':', 1)
                if len(fs) == 1:
                    if fs[0].isdigit():
                        server['listens'].append({
                            'ip': '*',
                            'port': fs[0],
                            'default_server': default_server
                        })
                else:
                    server['listens'].append({
                        'ip': fs[0],
                        'port': fs[1],
                        'default_server': default_server
                    })
        
        engines = _detect_engines(s)
        engine_orders = ['static', 'fastcgi', 'scgi', 'uwsgi', 'redirect', 'proxy', 'rewrite', 'return']
        engines = [(engine_orders.index(engine), engine) for engine in engines]
        engines.sort()
        if engines:
            server['engines'] = zip(*engines)[1]
        else:
            server['engines'] = []
        
        # check the status of this server
        if s['_disabled']:
            server['status'] = 'off'
        else:
            server['status'] = 'on'
        
        servers.append(server)
    return servers
    
def http_get(directive, config=None):
    """Get directive values in http context.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF)
    hcontext = _context_gethttp(config)
    if hcontext.has_key(directive):
        return hcontext[directive]
    elif DEFAULTVALS.has_key(directive):
        return DEFAULTVALS[directive]
    else:
        return None

def http_getfirst(directive, config=None):
    """Get the first value of the directive in http context.
    """
    values = http_get(directive, config)
    if values: return values[0]
    return None
    
def http_set(directive, values, config=None):
    """Set a directive in http context.
    
    If directive exists, the value will be replace in place.
    If directive not exists, new directive will be created at the beginning of http context.
    
    Parameter values can be a list or a string.
    If values is set to empty list or None or empty string, then the directive will be deleted.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, True)
    hcontext = _context_gethttp(config)

    if not values:
        values = []
    elif isinstance(values, str):
        values = [values]
    values = ['%s %s;' % (directive, v) for v in values]

    if hcontext.has_key(directive):
        # update or delete value
        dvalues = hcontext[directive]
        lines = [(config['_files'][dvalue['file']], dvalue['line'][0], dvalue['line'][1]) for dvalue in dvalues]
        _replace(lines, values)
    else:
        # add directive to the beginning of http context
        # some directive like proxy_cache_path should be declare before use the resource,
        # so we should insert it at the beginning
        begin = hcontext['_range']['begin']
        _insert(config['_files'][begin['file']], begin['line'][0]+begin['line'][1], values)
    
    config['_isdirty'] = True

def disableserver(ip, port, server_name):
    """Disable a server.
    """
    _context_commentupstreams(server_name)
    return _context_commentserver(ip, port, server_name)

def enableserver(ip, port, server_name):
    """Enable a server.
    """
    _context_uncommentupstreams(server_name)
    return _context_uncommentserver(ip, port, server_name)

def deleteserver(ip, port, server_name, disabled=None):
    """Delete a server.
    
    If disabled is not None, it will only delete those servers which is disabled or enabled.
    """
    _context_deleteupstreams(server_name, disabled=disabled)
    return _context_deleteserver(ip, port, server_name, disabled=disabled)

def servername_exists(ip, port, server_name, config=None):
    """Check if the server_name at given ip:port is already exists.
    """
    return _context_getserver(ip, port, server_name, config=config) and True or False

def getserver(ip, port, server_name, config=None):
    """Get server setting from nginx config files.
    """
    if not config or config['_isdirty']:
        config = loadconfig(NGINXCONF, False)
    scontext = _context_getserver(ip, port, server_name, config=config, getlineinfo=False)
    if not scontext: return False

    server = {}
    server['_vpsmate'] = scontext['_vpsmate']
    server['server_names'] = []
    if scontext.has_key('server_name'):
        for name in scontext['server_name']:
            server['server_names'].extend(name.split())

    server['listens'] = []
    if scontext.has_key('listen'):
        cnflistens = scontext['listen']
        for cnflisten in cnflistens:
            listen = {}
            fields = cnflisten.split()
            listen['ssl'] = 'ssl' in fields
            listen['default_server'] = 'default_server' in fields
            ipport = fields[0].split(':', 1)
            if len(ipport) == 1:
                listen['ip'] = ''
                listen['port'] = ipport[0]
            else:
                listen['ip'] = ipport[0]
                listen['port'] = ipport[1]
            server['listens'].append(listen)
    
    if scontext.has_key('charset'): server['charset'] = scontext['charset'][-1]
    if scontext.has_key('index'): server['index'] = scontext['index'][-1]
    if scontext.has_key('limit_rate'): server['limit_rate'] = scontext['limit_rate'][-1].replace('k','')
    if scontext.has_key('limit_conn'): server['limit_conn'] = scontext['limit_conn'][-1].split()[-1]
    if scontext.has_key('ssl') and scontext['ssl'][-1] == 'on': # deal with old config file
        for listen in server['listens']: listen['ssl'] = True
    if scontext.has_key('ssl_certificate'): server['ssl_crt'] = scontext['ssl_certificate'][-1]
    if scontext.has_key('ssl_certificate_key'): server['ssl_key'] = scontext['ssl_certificate_key'][-1]
    if scontext.has_key('rewrite'):
        server['rewrite_rules'] = ['rewrite %s' % rule for rule in scontext['rewrite']]
    
    server['locations'] = []
    if scontext.has_key('location'):
        locs = scontext['location']
        for loc in locs:
            location = {}
            location['urlpath'] = loc['_param']
            if loc.has_key('root'):
                location['root'] = loc['root'][-1]
            elif scontext.has_key('root'): # deal with old config file
                location['root'] = scontext['root'][-1]
            if loc.has_key('alias'): location['root'] = loc['alias'][-1]
            if loc.has_key('autoindex'): location['autoindex'] = loc['autoindex'][-1] == 'on'

            # detect redirect and rewrite
            # we treat redirect and rewrite conflict
            rewrites = []
            if loc.has_key('rewrite'):
                rewrites = loc['rewrite']
            if loc.has_key('if'):
                for ifstm in loc['if']:
                    if re.sub('\s', '', ifstm['_param']) == '(!-e$request_filename)':
                        location['rewrite_detect_file'] = True
                    if ifstm.has_key('rewrite'):
                        rewrites.extend(ifstm['rewrite'])
            
            for rule in rewrites:
                rwinfo = rule.split()
                if rwinfo[-1] in ('permanent', 'redirect'):
                    if rwinfo[1].endswith('$request_uri?') or rwinfo[1].endswith('$request_uri_alias?'):
                        redirect_option = 'keep'
                        redirect_url = rwinfo[1].replace('$request_uri?', '').replace('$request_uri_alias?', '')
                    else:
                        redirect_option = 'ignore'
                        redirect_url = rwinfo[1]
                    redirect_type = rwinfo[-1] == 'permanent' and '301' or '302'
                    location['redirect_url'] = redirect_url
                    location['redirect_type'] = redirect_type
                    location['redirect_option'] = redirect_option
                else:
                    if not location.has_key('rewrite_rules'): location['rewrite_rules'] = []
                    location['rewrite_rules'].append('rewrite %s' % rule)

            # detect fastcgi
            if loc.has_key('fastcgi_pass'):
                location['fastcgi_pass'] = loc['fastcgi_pass'][-1]
            elif loc.has_key('location'):
                for l in loc['location']:
                    if l.has_key('fastcgi_pass'):
                        location['fastcgi_pass'] = l['fastcgi_pass'][-1]
                    break   # only recoginze the first fastcgi setting

            # detect proxy 
            if loc.has_key('proxy_pass'):
                backend = loc['proxy_pass'][-1]
                if backend.startswith('http'): location['proxy_protocol'] = 'http'
                if backend.startswith('https'): location['proxy_protocol'] = 'https'
                if location.has_key('proxy_protocol'):
                    if loc.has_key('proxy_set_header'):
                        headers = loc['proxy_set_header']
                        for header in headers:
                            hinfo = re.split(r'\s+', header, 1)
                            if len(hinfo) == 1: continue
                            if hinfo[0] == 'X-Real-IP':
                                if hinfo[1] == '$remote_addr':
                                    location['proxy_realip'] = True
                            elif hinfo[0] == 'Host':
                                location['proxy_host'] = hinfo[1]
                    # detect upstream
                    upstream_name = 'backend_of_%s_%s' % (server_name, location['urlpath'].replace('/', '_'))
                    if backend == '%s://%s' % (location['proxy_protocol'], upstream_name):
                        upstreams = http_get('upstream', config)
                        for upstream in upstreams:
                            if upstream['_param'] == upstream_name:
                                if upstream.has_key('ip_hash'): location['proxy_balance'] = 'ip_hash'
                                if upstream.has_key('least_conn'): location['proxy_balance'] = 'least_conn'
                                if not location.has_key('proxy_balance'): location['proxy_balance'] = 'weight'
                                if upstream.has_key('keepalive'): location['proxy_keepalive'] = upstream['keepalive'][-1]
                                if upstream.has_key('server'):
                                    location['proxy_backends'] = []
                                    for s in upstream['server']:
                                        sinfo = s.split()
                                        backend = {}
                                        backend['server'] = sinfo[0]
                                        for t in sinfo[1:]:
                                            if t.startswith('weight='):
                                                backend['weight'] = t.replace('weight=', '')
                                            elif t.startswith('max_fails='):
                                                backend['max_fails'] = t.replace('max_fails=', '')
                                            elif t.startswith('fail_timeout='):
                                                backend['fail_timeout'] = t.replace('fail_timeout=', '').replace('s','')
                                        location['proxy_backends'].append(backend)
                                break # found the right upstream
                # detect proxy cache
                if loc.has_key('proxy_cache'):
                    cachename = loc['proxy_cache'][-1]
                    if cachename.lower() != 'off':
                        location['proxy_cache'] = cachename
                        if loc.has_key('proxy_cache_min_uses'):
                            location['proxy_cache_min_uses'] = loc['proxy_cache_min_uses'][-1]
                        if loc.has_key('proxy_cache_methods') and 'POST' in loc['proxy_cache_methods'][-1].upper().split():
                            location['proxy_cache_methods'] = 'POST'
                        if loc.has_key('proxy_cache_key'):
                            location['proxy_cache_key'] = loc['proxy_cache_key'][-1]
                        if loc.has_key('proxy_cache_use_stale'):
                            location['proxy_cache_use_stale'] = loc['proxy_cache_use_stale'][-1].split()
                        if loc.has_key('proxy_cache_valid'):
                            location['proxy_cache_valid'] = []
                            for valid in loc['proxy_cache_valid']:
                                fields = valid.split()
                                for i in range(0, len(fields)-1):
                                    location['proxy_cache_valid'].append({'code': fields[i], 'time': fields[-1]})
                        if loc.has_key('proxy_cache_lock'):
                            location['proxy_cache_lock'] = loc['proxy_cache_lock'][-1].lower() == 'on'
                        if loc.has_key('proxy_cache_lock_timeout'):
                            location['proxy_cache_lock_timeout'] = loc['proxy_cache_lock_timeout'][-1].replace('s', '')

            # detect error code
            if loc.has_key('return'):
                location['error_code'] = loc['return'][-1]

            server['locations'].append(location)
    
    return server
    
def addserver(server_names, listens, charset=None, index=None, locations=None,
    limit_rate=None, limit_conn=None, ssl_crt=None, ssl_key=None,
    rewrite_rules=None, conflict_check=True, version=None):
    """Add a new server.
    
    We create new config file for each server under /etc/nginx/conf.d/.
    Config file name depends on the first of server_names.
    
	Parameter examples:
    * server_names: ['example.com', 'www.example.com']
    * listens:
      [
        {
            'ip': '',
            'port': '80',
            'ssl': True,
            'default_server': False
        }
      ]
    * charset: 'utf-8'
    * index: 'index.html index.htm index.php'
    * locations: 
      [
        {
            'urlpath': '/',
            'root': '/var/www/example',
            'fastcgi_pass': '127.0.0.1:9000',
            'rewrite_detect_file': True,
            'rewrite_rules': [
                'rewrite ^/$ /index.php last',
                'rewrite ^/(.*)$ /index.php/$1 last',
            ],
        },
        {
            'urlpath': '/download',
            'root': '/var/www/example/download',
            'autoindex': True,
        },
        {
            'urlpath': '/redirect',
            'redirect_url': 'http://test.com/',
            'redirect_type': '301',
			'redirect_option': 'keep',
        },
        {
            'urlpath': '/proxy',
            'proxy_balance': 'weight',
            'proxy_protocol': 'http',
            'proxy_host': 'www.baidu.com',
            'proxy_charset': 'utf-8',
            'proxy_realip': True,
            'proxy_keepalive': 10,
            'proxy_backends': [
                {'server':'www.baidu.com'}
            ],
			'proxy_cache': 'proxycache',
			'proxy_cache_min_uses': '5',
			'proxy_cache_methods': 'POST',
			'proxy_cache_key': '$scheme$proxy_host$request_uri',
			'proxy_cache_valid': [
                {
                    'code': '200',
                    'time': '1m',
                }
            ],
			'proxy_cache_use_stale': [
				'error', 'timeout', 'invalid_header', 'updating',
                'http_500', 'http_502', 'http_503', 'http_504', 'http_404'
			],
			'proxy_cache_lock': True,
			'proxy_cache_lock_timeout': '5',
        },
        {
            'urlpath': '/error',
            'error_code': '502',
        }
      ]
    * limit_rate: '100'
    * limit_conn: '10'
    * ssl_crt: '/etc/nginx/ssl/server.crt'
    * ssl_key: '/etc/nginx/ssl/server.key'
    * rewrite_rules: 
      [
        'rewrite ^ https://www.example.com$document_uri permanent'
      ]
    """
    # check if any of listen - server_name pair already exists
    if conflict_check:
        for server_name in server_names:
            for listen in listens:
                ip = listen.has_key('ip') and listen['ip'] or ''
                if servername_exists(ip, listen['port'], server_name):
                    return False
    
    # start generate the config string
    servercfg = ['server { # %s' % GENBY]

    if limit_rate: servercfg.append('    limit_rate %sk;' % limit_rate)
    if limit_conn:
        _context_http_init_limit_conn(version=version)
        servercfg.append('    limit_conn addr %s;' % limit_conn)

    for listen in listens:
        flag_ds = listen.has_key('default_server') and listen['default_server'] and ' default_server' or ''
        flag_ssl = listen.has_key('ssl') and listen['ssl'] and ' ssl' or ''
        ip = listen.has_key('ip') and listen['ip'] or ''
        port = listen['port']
        if ip:
            servercfg.append('    listen %s:%s%s%s;' % (ip, port, flag_ds, flag_ssl))
        else:
            servercfg.append('    listen %s%s%s;' % (port, flag_ds, flag_ssl))
        # if set to default server, we should clear the default_server flag
        if flag_ds: _context_server_clear_default_server(ip, port)
            
    servercfg.append('    server_name %s;' % (' '.join(server_names)))

    if charset: servercfg.append('    charset %s;' % charset)
    servercfg.append('')

    if ssl_crt and ssl_key:
        if not os.path.exists(ssl_crt) or not os.path.exists(ssl_key): return False
        servercfg.append('    ssl_certificate %s;' % ssl_crt)
        servercfg.append('    ssl_certificate_key %s;' % ssl_key)
        servercfg.append('    ssl_session_timeout 5m;')
        servercfg.append('    ssl_protocols SSLv2 SSLv3 TLSv1;')
        servercfg.append('    ssl_ciphers ALL:!ADH:!EXPORT56:RC4+RSA:+HIGH:+MEDIUM:+LOW:+SSLv2:+EXP;')
        servercfg.append('    ssl_prefer_server_ciphers on;')
        servercfg.append('')
    
    if index:
        servercfg.append('    index %s;' % index)
        servercfg.append('')
    
    upstreams = {}
    if locations:
        urlpaths = [] # use to detect if urlpath duplicates
        for location in locations:
            urlpath = location['urlpath'].strip()
            if urlpath in urlpaths: return False
            urlpaths.append(urlpath)

            servercfg.append('    location %s {' % urlpath)
            if location.has_key('root'):
                if urlpath.startswith('~'):  # deal with old config
                    servercfg.append('        root    %s;' % location['root'])
                else:
                    if urlpath == '/':
                        servercfg.append('        root    %s;' % location['root'])
                    else:
                        servercfg.append('        alias   %s;' % location['root'])

            if location.has_key('autoindex'):
                servercfg.append('        autoindex   %s;' % (location['autoindex'] and 'on' or 'off'))

            if location.has_key('fastcgi_pass'):
                if urlpath.startswith('~'):  # deal with old config
                    servercfg.append('        fastcgi_index  index.php;')
                    servercfg.append('        fastcgi_split_path_info ^(.+\.php)(/?.+)$;')
                    servercfg.append('        fastcgi_param PATH_INFO $fastcgi_path_info;')
                    servercfg.append('        fastcgi_param PATH_TRANSLATED $document_root$fastcgi_path_info;')
                    servercfg.append('        include        fastcgi_params;')
                    servercfg.append('        fastcgi_pass   %s;' % location['fastcgi_pass'])
                else:
                    if urlpath == '/':
                        servercfg.append('        location ~ ^/.+\.php {')
                        servercfg.append('            fastcgi_param  SCRIPT_FILENAME    $document_root$fastcgi_script_name;')
                    else:
                        servercfg.append('        location ~ ^%s(/.+\.php) {' % urlpath)
                        servercfg.append('            root  %s;' % location['root'])
                        servercfg.append('            set $fastcgi_script_alias $1;')
                        servercfg.append('            fastcgi_param  SCRIPT_FILENAME    $document_root$fastcgi_script_alias;')

                    servercfg.append('            fastcgi_index  index.php;')
                    servercfg.append('            fastcgi_split_path_info ^(.+\.php)(/?.+)$;')
                    servercfg.append('            fastcgi_param PATH_INFO $fastcgi_path_info;')
                    servercfg.append('            fastcgi_param PATH_TRANSLATED $document_root$fastcgi_path_info;')
                    servercfg.append('            include        fastcgi_params;')
                    servercfg.append('            fastcgi_pass   %s;' % location['fastcgi_pass'])
                    servercfg.append('        }')
            
            if location.has_key('rewrite_rules'):
                rules = location['rewrite_rules']
                if location.has_key('rewrite_detect_file') and location['rewrite_detect_file']:
                    servercfg.append('        if (!-e $request_filename)')
                    servercfg.append('        {')
                    for rule in rules:
                        servercfg.append('            %s;' % rule)
                    servercfg.append('        }')
                else:
                    for rule in rules:
                        servercfg.append('        %s;' % rule)

            if location.has_key('redirect_url'):
                redirect_url = location['redirect_url']
                if redirect_url:
                    redirect_type = location.has_key('redirect_type') and location['redirect_type'] or '302'
                    redirect_option = location.has_key('redirect_option') and location['redirect_option'] or 'ignore'
                    if urlpath == '/' or redirect_option == 'ignore':
                        servercfg.append('        rewrite ^ %s%s %s;' % (redirect_url,
                                redirect_option=='keep' and '$request_uri?' or '',
                                redirect_type=='301' and 'permanent' or 'redirect'))
                    else:
                        servercfg.append('        if ($request_uri ~ ^%s(/.+)$) {' % urlpath)
                        servercfg.append('            set $request_uri_alias $1;')
                        servercfg.append('            rewrite ^ %s$request_uri_alias? %s;' % (redirect_url,
                                redirect_type=='301' and 'permanent' or 'redirect'))
                        servercfg.append('        }')

            if location.has_key('proxy_backends') and location['proxy_backends']:
                if urlpath != '/':
                    servercfg.append('        rewrite %s(.*) / break;' % urlpath)
                if location.has_key('proxy_charset') and location['proxy_charset']:
                    servercfg.append('        charset %s;' % location['proxy_charset'])
                if location.has_key('proxy_host') and location['proxy_host']:
                    servercfg.append('        proxy_set_header Host %s;' % location['proxy_host'])
                if location.has_key('proxy_realip') and location['proxy_realip']:
                    servercfg.append('        proxy_set_header X-Real-IP  $remote_addr;')
                proxy_protocol = location.has_key('proxy_protocol') and location['proxy_protocol'] or 'http'
                upstream_name = "backend_of_%s_%s" % (server_names[0], urlpath.replace('/', '_'))
                servercfg.append('        proxy_pass %s://%s;' % (proxy_protocol, upstream_name))
                proxy_balance = location.has_key('proxy_balance') and location['proxy_balance'] or 'ip_hash'
                upstreams[upstream_name] = {
                    'balance': proxy_balance,
                    'keepalive': location.has_key('proxy_keepalive') and location['proxy_keepalive'] or None,
                    'backends': location['proxy_backends']
                }

            if location.has_key('proxy_cache') and location['proxy_cache']:
                servercfg.append('        proxy_cache %s;' % location['proxy_cache'])
                if location.has_key('proxy_cache_min_uses'):
                    servercfg.append('        proxy_cache_min_uses %s;' % location['proxy_cache_min_uses'])
                if location.has_key('proxy_cache_methods'):
                    servercfg.append('        proxy_cache_methods %s;' % location['proxy_cache_methods'])
                if location.has_key('proxy_cache_key'):
                    servercfg.append('        proxy_cache_key %s;' % location['proxy_cache_key'])
                if location.has_key('proxy_cache_valid'):
                    for v in location['proxy_cache_valid']:
                        servercfg.append('        proxy_cache_valid %s %s;' % (v['code'], v['time']))
                if location.has_key('proxy_cache_use_stale'):
                    servercfg.append('        proxy_cache_use_stale %s;' % (' '.join(location['proxy_cache_use_stale'])))
                if location.has_key('proxy_cache_lock') and location['proxy_cache_lock']:
                    servercfg.append('        proxy_cache_lock on;')
                    if location.has_key('proxy_cache_lock_timeout'):
                        servercfg.append('        proxy_cache_lock_timeout %ss;' % location['proxy_cache_lock_timeout'])

            if location.has_key('error_code'): servercfg.append('        return %s;' % location['error_code'])

            servercfg.append('    }')
            servercfg.append('')

    if rewrite_rules:
        for rewrite_rule in rewrite_rules:
            if rewrite_rule: servercfg.append('    %s;' % rewrite_rule.strip())

    # end of server context
    servercfg.append('}')

    for upstream_name, upstream in upstreams.iteritems():
        balance = upstream['balance']
        backends = upstream['backends']

        servercfg.append('upstream %s { # %s' % (upstream_name, GENBY))

        if len(backends) > 1: # have balance options
            if balance == 'ip_hash': servercfg.append('    ip_hash;')
            if balance == 'least_conn': servercfg.append('    least_conn;')
            if upstream['keepalive']: servercfg.append('    keepalive %s;' % upstream['keepalive'])
            for backend in backends:
                weight = fail_timeout = max_fails = ''
                if balance == 'weight' and backend.has_key('weight') and backend['weight']:
                    weight = ' weight=%s' % backend['weight'];
                if backend.has_key('fail_timeout') and backend['fail_timeout']:
                    fail_timeout = ' fail_timeout=%ss' % backend['fail_timeout'];
                if backend.has_key('max_fails') and backend['max_fails']:
                    max_fails = ' max_fails=%s' % backend['max_fails'];
                servercfg.append('    server %s%s%s%s;' % (backend['server'],
                            weight, fail_timeout, max_fails))
        else:
            servercfg.append('    server %s;' % backends[0]['server'])

        servercfg.append('}')
    
    #print '\n'.join(servercfg)
    configfile = os.path.join(SERVERCONF, '%s.conf' % server_names[0])
    configfile_exists = os.path.exists(configfile)

    # check if need to add a new line at the end of the file to
    # avoid first line go to the same former } line
    if configfile_exists:
        with open(configfile) as f:
            f.seek(-1, 2)
            if f.read(1) != '\n':
                servercfg.insert(0, '')
    with open(configfile, configfile_exists and 'a' or 'w') as f: f.write('\n'.join(servercfg))
    return True

def updateserver(old_ip, old_port, old_server_name,
    server_names, listens, charset=None, index=None, locations=None,
    limit_rate=None, limit_conn=None, ssl_crt=None, ssl_key=None,
    rewrite_rules=None, version=None):
    """Update a existing server.
    
    If the old config is not in the right place, we would automatically delete it and
    create the new config to coresponding config file under /etc/nginx/conf.d/.
    """
    # compare the old context and the new context
    # to check if the ip:port/server_name change and conflict status
    config = loadconfig(NGINXCONF, True)
    oldscontext = _context_getserver(old_ip, old_port, old_server_name, config)
    if not oldscontext: return False
    for server_name in server_names:
        for listen in listens:
            ip = listen.has_key('ip') and listen['ip'] or ''
            scontext = _context_getserver(ip, listen['port'], server_name)
            # server context found, but not equals to the old
            # this means conflict occur
            if scontext and scontext != oldscontext:
                return False

    # init limit_conn_zone in http, this may cause http context change
    # reload config if change occur
    if limit_conn:
        if _context_http_init_limit_conn(version=version):
            config = loadconfig(NGINXCONF, True)
    
    # disable the old server and relative upstreams
    if not _context_commentserver(old_ip, old_port, old_server_name, config=config): return False
    if not _context_commentupstreams(old_server_name, config=config): return False

    # add the new server
    if not addserver(server_names, listens, charset=charset, index=index, locations=locations,
        limit_rate=limit_rate, limit_conn=limit_conn, ssl_crt=ssl_crt, ssl_key=ssl_key,
        rewrite_rules=rewrite_rules, conflict_check=False, version=version): return False

    # only delete the disabled server
    _context_deleteupstreams(old_server_name, disabled=True)
    _context_deleteserver(old_ip, old_port, old_server_name, disabled=True)

    return True


if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    #_insert('/etc/nginx/nginx.conf', 31, ['gzip off'])
    #_replace([('/etc/nginx/nginx.conf', 31, 1)], ['gzip on', 'gzip off'])
    #http_set('gzip', 'off')
    #http_set('limit_conn_zone', '$binary_remote_addr  zone=addr:10m')
    #print http_get('limit_conn_zone')
    #print http_getfirst('limit_conn_zone')

    #pp.pprint(loadconfig(NGINXCONF, True))
    #pp.pprint(getservers())
    #pp.pprint(_context_getserver('0.0.0.0', '80', 'test.local'))
    #pp.pprint(disableserver('0.0.0.0', '80', 'test.local'))
    #pp.pprint(enableserver('0.0.0.0', '80', 'test.local'))
    #pp.pprint(deleteserver('0.0.0.0', '80', 'youmeiyoua.com'))

    #print servername_exists('0.0.0.0', '80', 'www.paomi.local')

    #print _context_server_clear_default_server('0.0.0.0', '8000')
    
    #pp.pprint(deleteserver('0.0.0.0', '8000', 'test.db.local'))
    #pp.pprint(_context_getupstreams('test.db.local', disabled=True))
    #pp.pprint(_context_deleteupstreams('test.db.local'))
    #pp.pprint(_context_uncommentupstreams('test.db.local'))
    #pp.pprint(_context_getupstreams('test.db.local'))
    #pp.pprint(getserver('*', '80', 'www.baidu.com'))
    #print _context_getserver('*', '80', '192.168.0.13')

    if 0:
        print addserver(
            ['example.com', 'test.db.local'],
            [{'port': '8000'}, {'port': '88'}],
            charset='utf-8',
            index='index.html index.htm index.php',
            locations=None,
            limit_rate='100k',
            limit_conn='10',
            rewrite_rules=['rewrite ^ https://www.example.com$document_uri permanent'])
    if 0:
        print updateserver(
            '', '8000', 'test.db.local',
            ['test.db.local'],
            [{'port': '8000', 'default_server': True}],
            charset='utf-8',
            index='index.html index.htm index.php',
            locations=[
                {
                    'urlpath': '/',
                    'root': '/var/www/example',
                    'fastcgi_pass': '127.0.0.1:9000',
                }, {
                    'urlpath': '/phpinfo',
                    'root': '/var/www/phpinfo',
                    'fastcgi_pass': '127.0.0.1:9000',
                }, {
                    'urlpath': '/redirect',
                    'redirect_url': 'http://www.baidu.com',
                    'redirect_type': '301',
                    'redirect_option': 'keep',
                }, {
                    'urlpath': '/proxy',
                    'proxy_balance': 'weight',
                    'proxy_protocol': 'http',
                    'proxy_host': 'www.baidu.com',
                    'proxy_realip': True,
                    'proxy_backends': [
                        {'server':'www.citydog.me'},
                        {'server':'www.baidu.com'},
                    ],
                },{
                    'urlpath': '/error',
                    'error_code': '502',
                }
            ],
            limit_rate='100',
            limit_conn='10')