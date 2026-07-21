var ServiceCtrl = [
    '$scope', '$routeParams', 'Module', 'Timeout', 'Request', 'Task',
    function ($scope, $routeParams, Module, Timeout, Request, Task) {
        var module = 'service';
        Module.init(module, '服务管理');
        Module.initSection('http');
        $scope.scope = $scope;

        $scope.loaded = false;
        $scope.waiting = true;
        $scope.categories = [];
        $scope.otherServices = [];

        $scope.loadInfo = function () {
            Request.get('/api/service/list', function (res) {
                if (res.code === 0 && res.data) {
                    $scope.categories = res.data.categories || [];
                    $scope.otherServices = res.data.other || [];
                    // 首次加载时，activeTabName 设为第一个分类
                    if (!$scope.activeTabName && $scope.categories.length > 0) {
                        $scope.activeTabName = $scope.categories[0].id;
                    }
                }
                if (!$scope.loaded) $scope.loaded = true;
                $scope.waiting = false;
            });
        };

        $scope.toggleAutostart = function (svc) {
            Request.post('/api/service/chkconfig', {
                'service': svc.id,
                'autostart': svc.autostart ? 'off' : 'on'
            }, function () {
                $scope.loadInfo();
            });
        };

        $scope.start = function (svc) {
            Task.call(
                $scope,
                module,
                '/api/task/service.start',
                '/api/task/service.start_' + svc.id, {
                    'service': svc.id,
                    'name': svc.name
                }, {
                    'success': function () {
                        $scope.loadInfo();
                    },
                    'error': function () {
                        $scope.loadInfo();
                    }
                }
            );
        };
        $scope.stop = function (svc) {
            Task.call(
                $scope,
                module,
                '/api/task/service.stop',
                '/api/task/service.stop_' + svc.id, {
                    'service': svc.id,
                    'name': svc.name
                }, {
                    'success': function () {
                        $scope.loadInfo();
                    },
                    'error': function () {
                        $scope.loadInfo();
                    }
                }
            );
        };
        $scope.restart = function (svc) {
            Task.call(
                $scope,
                module,
                '/api/task/service.restart',
                '/api/task/service.restart_' + svc.id, {
                    'service': svc.id,
                    'name': svc.name
                }, {
                    'success': function () {
                        $scope.loadInfo();
                    },
                    'error': function () {
                        $scope.loadInfo();
                    }
                }
            );
        };

        $scope.install = function (svc) {
            Task.call(
                $scope,
                module,
                '/api/task/service.install',
                '/api/task/service.install_' + svc.id, {
                    'service': svc.id
                }, {
                    'success': function () {
                        $scope.loadInfo();
                    },
                    'error': function () {
                        $scope.loadInfo();
                    }
                }
            );
        };
    }
];

var ServiceNginxCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.nginx';
        Module.init(module, 'Nginx');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/nginx', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                    $scope.getsettings();
                    $scope.getcachesettings();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
            Request.get('/api/client/ip', function (res) {
                $scope.ip = res;
            });
        };

        $scope.setting = {
            'limit_rate': '',
            'limit_conn': '',
            'limit_conn_zone': '',
            'client_max_body_size': '',
            'keepalive_timeout': '',
            'access_status': 'off',
            'allow': '',
            'deny': '',
            'gzip': ''
        };

        $scope.getsettings = function () {
            if (!$scope.installed) return;
            Request.post('/api/operation/nginx', {
                'action': 'gethttpsettings',
                'items': 'limit_rate,limit_conn,limit_conn_zone,client_max_body_size,keepalive_timeout,allow[],deny[],gzip'
            }, function (res) {
                if (res.code == 0) {
                    $scope.setting = res.data;
                    var s = $scope.setting;
                    if (s.allow && s.allow.length > 0) s.access_status = 'white';
                    else if (s.deny && s.deny.length > 0) s.access_status = 'black';
                    else s.access_status = 'off';
                    if (s.allow) s.allow = s.allow.join('\n');
                    if (s.deny) s.deny = s.deny.join('\n');
                }
            }, false, true);
        };

        $scope.savesettings = function () {
            var data = angular.copy($scope.setting);
            data.action = 'sethttpsettings';
            data.version = $scope.pkginfo.version;
            Request.post('/api/operation/nginx', data, function (res) {
                if (res.code == 0) {
                    $scope.getsettings();
                }
            });
        };

        var cache_tmpl = {
            'name': 'newcache',
            'mem': '10',
            'path': '/var/www/cache',
            'path_level_1': '1',
            'path_level_2': '2',
            'path_level_3': '0',
            'inactive': '10',
            'inactive_unit': 'm',
            'max_size': '100',
            'max_size_unit': 'm',
            'autocreate': true
        };
        $scope.proxy_caches = [];
        $scope.curcache = -1;
        $scope.setcache = function (i) {
            $scope.curcache = i;
        };

        $scope.getcachesettings = function () {
            if (!$scope.installed) return;
            Request.post('/api/operation/nginx', {
                'action': 'gethttpsettings',
                'items': 'proxy_cache_path[]'
            }, function (res) {
                if (res.code == 0) {
                    $scope.proxy_caches = [];
                    var ps = res.data.proxy_cache_path;
                    if (ps) {
                        for (var i = 0; i < ps.length; i++) {
                            var p = angular.copy(cache_tmpl);
                            angular.extend(p, ps[i]);
                            $scope.proxy_caches.push(p);
                        }
                        $scope.curcache = 0;
                    }
                }
            }, false, true);
        };

        $scope.deletecache = function (i) {
            $scope.proxy_caches.splice(i, 1);
            $scope.curcache--;
            if ($scope.curcache < 0 && $scope.proxy_caches.length > 0) $scope.curcache = 0;
        };
        $scope.addcache = function () {
            var caches = $scope.proxy_caches;
            caches.splice($scope.curcache + 1, 0, angular.copy(cache_tmpl));
            $scope.curcache++;
        };
        $scope.selectcachefolder = function (i) {
            $scope.selector_title = '请选择缓存目录';
            $scope.selector.onlydir = true;
            $scope.selector.onlyfile = false;
            $scope.selector.load($scope.proxy_caches[i].path);
            $scope.selector.selecthandler = function (path) {
                $('#selector').modal('hide');
                $scope.proxy_caches[i].path = path;
            };
            $('#selector').modal();
        };
        $scope.savecaches = function () {
            var data = {
                'action': 'setproxycachesettings',
                'proxy_caches': angular.toJson($scope.proxy_caches)
            };
            Request.post('/api/operation/nginx', data, function (res) {
                if (res.code == 0) {
                    $scope.getcachesettings();
                }
            });
        };
    }
];

var ServiceApacheCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.apache';
        Module.init(module, 'Apache');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/httpd', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                    $scope.getSettings();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };

        $scope.settings = {
            'Listen': 80,
            'ServerAdmin': 'root@localhost',
            'server_name': 'localhost:80',
            'DocumentRoot': '/var/www/html',
            'DirectoryIndex': 'index.html index.htm',
            'AddDefaultCharset': 'UTF-8',
            'limit_rate': '',
            'limit_conn': '',
            'limit_conn_zone': '',
            'client_max_body_size': '',
            'keepalive_timeout': '',
            'access_status': 'off',
            'allow': '',
            'deny': '',
            'Gzip': ''
        };

        $scope.getSettings = function () {
            if (!$scope.installed) return;
            Request.post('/api/operation/apache', {
                'action': 'get_settings',
                'items': 'limit_rate,limit_conn,limit_conn_zone,client_max_body_size,keepalive_timeout,allow[],deny[],gzip'
            }, function (res) {
                if (res.code == 0) {
                    $scope.settings = res.data;
                    var s = $scope.settings;
                    if (s.allow && s.allow.length > 0) s.access_status = 'white';
                    else if (s.deny && s.deny.length > 0) s.access_status = 'black';
                    else s.access_status = 'off';
                    if (s.allow) s.allow = s.allow.join('\n');
                    if (s.deny) s.deny = s.deny.join('\n');
                }
            }, false, true);
        };

        $scope.updateSettings = function () {
            console.log('updateSettings Apache')
            // var data = angular.copy($scope.settings);
            // data.action = 'sethttpsettings';
            // data.version = $scope.pkginfo.version;
            // Request.post('/api/operation/apache', data, function (res) {
            //     if (res.code == 0) {
            //         $scope.getSettings();
            //     }
            // });
        };
    }
];

var ServiceTomcatCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.tomcat';
        Module.init(module, 'Tomcat');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/tomcat', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                    $scope.getsettings();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };

        $scope.setting = {
            'limit_rate': '',
            'limit_conn': '',
            'limit_conn_zone': '',
            'client_max_body_size': '',
            'keepalive_timeout': '',
            'access_status': 'off',
            'allow': '',
            'deny': '',
            'gzip': ''
        };

        $scope.getsettings = function () {
            if (!$scope.installed) return;
            Request.post('/api/operation/apache', {
                'action': 'gethttpsettings',
                'items': 'limit_rate,limit_conn,limit_conn_zone,client_max_body_size,keepalive_timeout,allow[],deny[],gzip'
            }, function (res) {
                if (res.code == 0) {
                    $scope.setting = res.data;
                }
            }, false, true);
        };

        $scope.savesettings = function () {
            var data = angular.copy($scope.setting);
            data.action = 'sethttpsettings';
            data.version = $scope.pkginfo.version;
            Request.post('/api/operation/nginx', data, function (res) {
                if (res.code == 0) {
                    $scope.getsettings();
                }
            });
        };
    }
];

var ServiceVsftpdCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.vsftpd';
        Module.init(module, 'vsftpd');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/vsftpd', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    $scope.getsettings();
                    if ($scope.checkVersion) {
                        $scope.checkVersion();
                    }
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };

        $scope.getsettings = function () {
            Request.post('/api/operation/vsftpd', {
                'action': 'getsettings'
            }, function (data) {
                if (data.code == 0) {
                    $scope.baseconfigs = data.data;
                }
            });
        };

        $scope.savesettings = function () {
            $scope.processing = true;
            Request.post('/api/operation/vsftpd', {
                'action': 'savesettings',
                'anonymous_enable': $scope.baseconfigs.anonymous_enable,
                'local_enable': $scope.baseconfigs.local_enable,
                'local_umask': $scope.baseconfigs.local_umask,
                'anon_upload_enable': $scope.baseconfigs.anon_upload_enable,
                'anon_mkdir_write_enable': $scope.baseconfigs.anon_mkdir_write_enable,
                'dirmessage_enable': $scope.baseconfigs.dirmessage_enable,
                'xferlog_enable': $scope.baseconfigs.xferlog_enable,
                'connect_from_port_20': $scope.baseconfigs.connect_from_port_20,
                'chown_upload': $scope.baseconfigs.chown_upload,
                'chown_username': $scope.baseconfigs.chown_username,
                'xferlog_file': $scope.baseconfigs.xferlog_file,
                'xferlog_std_format': $scope.baseconfigs.xferlog_std_format,
                'idle_session_timeout': $scope.baseconfigs.idle_session_timeout,
                'data_connection_timeout': $scope.baseconfigs.data_connection_timeout,
                'nopriv_user': $scope.baseconfigs.nopriv_user,
                'async_abor_enable': $scope.baseconfigs.async_abor_enable,
                'ascii_upload_enable': $scope.baseconfigs.ascii_upload_enable,
                'ascii_download_enable': $scope.baseconfigs.ascii_download_enable,
                'ftpd_banner': $scope.baseconfigs.ftpd_banner,
                'deny_email_enable': $scope.baseconfigs.deny_email_enable,
                'banned_email_file': $scope.baseconfigs.banned_email_file,
                'chroot_list_enable': $scope.baseconfigs.chroot_list_enable,
                'chroot_list_file': $scope.baseconfigs.chroot_list_file,
                'max_clients': $scope.baseconfigs.max_clients,
                'message_file': $scope.baseconfigs.message_file
            }, function (data) {
                if (data.code == 0) {
                    $scope.getsettings();
                }
                $scope.processing = false;
            });
        };
    }
];

var ServiceMySQLCtrl = [
    '$scope', '$rootScope', '$routeParams', 'Module', 'Message', 'Request', 'Task',
    function ($scope, $rootScope, $routeParams, Module, Message, Request, Task) {
        var module = 'service.mysqld';
        Module.init(module, 'MySQL');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.processing = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/mysqld', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };

        $scope.updatepwd = function () {
            if ($scope.status != 'running') {
                Message.setError('MySQL还未启动，无法修改密码！');
                return;
            }
            $scope.processing = true;
            Request.post('/api/operation/mysql', {
                'action': 'updatepwd',
                'newpassword': $scope.root_passwd,
                'newpasswordc': $scope.root_passwdc,
                'password': $scope.root_opasswd
            }, function (res) {
                if (res.code == 0) {
                    $scope.root_passwd = '';
                    $scope.root_passwdc = '';
                    $scope.root_opasswd = '';
                    // reset cached mysql password
                    $rootScope.$mysql = {
                        'password': '',
                        'password_validated': false
                    };
                }
                $scope.processing = false;
            });
        };

        $scope.fupdatepwd = function () {
            $scope.processing = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.fupdatepwd',
                '/api/task/mysql.fupdatepwd', {
                    'password': $scope.root_passwd,
                    'passwordc': $scope.root_passwdc
                },
                function (res) {
                    if (res.code == 0) {
                        $scope.root_passwd = '';
                        $scope.root_passwdc = '';
                        // reset cached mysql password
                        $rootScope.$mysql = {
                            'password': '',
                            'password_validated': false
                        };
                    }
                    $scope.processing = false;
                }
            );
        };
    }
];

var ServiceMariaDBCtrl = [
    '$scope', '$rootScope', '$routeParams', 'Module', 'Message', 'Request', 'Task',
    function ($scope, $rootScope, $routeParams, Module, Message, Request, Task) {
        var module = 'service.mariadb';
        Module.init(module, 'MariaDB');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.processing = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/mariadb', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };

        $scope.updatepwd = function () {
            if ($scope.status != 'running') {
                Message.setError('MariaDB 还未启动，无法修改密码！');
                return;
            }
            $scope.processing = true;
            Request.post('/api/operation/mariadb', {
                'action': 'updatepwd',
                'newpassword': $scope.root_passwd,
                'newpasswordc': $scope.root_passwdc,
                'password': $scope.root_opasswd
            }, function (res) {
                if (res.code == 0) {
                    $scope.root_passwd = '';
                    $scope.root_passwdc = '';
                    $scope.root_opasswd = '';
                    // reset cached mariadb password
                    $rootScope.$mariadb = {
                        'password': '',
                        'password_validated': false
                    };
                }
                $scope.processing = false;
            });
        };

        $scope.fupdatepwd = function () {
            $scope.processing = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.fupdatepwd',
                '/api/task/mysql.fupdatepwd', {
                    'password': $scope.root_passwd,
                    'passwordc': $scope.root_passwdc
                },
                function (res) {
                    if (res.code == 0) {
                        $scope.root_passwd = '';
                        $scope.root_passwdc = '';
                        // reset cached mysql password
                        $rootScope.$mariadb = {
                            'password': '',
                            'password_validated': false
                        };
                    }
                    $scope.processing = false;
                }
            );
        };
    }
];

var ServiceRedisCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.redis';
        Module.init(module, 'Redis');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/redis', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceMemcacheCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.memcache';
        Module.init(module, 'Memcache');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/memcached', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceMongoDBCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.mongodb';
        Module.init(module, 'MongoDB');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/mongod', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];
var ServiceMinIOCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.minio';
        Module.init(module, 'MinIO');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/minio', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];
var ServicePHP56Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.php56';
        Module.init(module, 'PHP 5.6');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/php56-php-fpm', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServicePHP74Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.php74';
        Module.init(module, 'PHP 7.4');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/php74-php-fpm', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServicePHP80Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.php80';
        Module.init(module, 'PHP 8.0');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/php80-php-fpm', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServicePHP81Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.php81';
        Module.init(module, 'PHP 8.1');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/php81-php-fpm', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServicePHP82Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.php82';
        Module.init(module, 'PHP 8.2');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/php82-php-fpm', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServicePHP83Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.php83';
        Module.init(module, 'PHP 8.3');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/php83-php-fpm', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServicePHP84Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.php84';
        Module.init(module, 'PHP 8.4');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/php84-php-fpm', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceJava8Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.java8';
        Module.init(module, 'Java 8');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/java8', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceJava11Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.java11';
        Module.init(module, 'Java 11');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/java11', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceJava17Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.java17';
        Module.init(module, 'Java 17');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/java17', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceJava21Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.java21';
        Module.init(module, 'Java 21');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/java21', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceNodeJS18Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.nodejs18';
        Module.init(module, 'Node.js 18');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/nodejs18', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceNodeJS20Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.nodejs20';
        Module.init(module, 'Node.js 20');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/nodejs20', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceNodeJS22Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.nodejs22';
        Module.init(module, 'Node.js 22');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/nodejs22', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceNodeJS24Ctrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.nodejs24';
        Module.init(module, 'Node.js 24');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;
        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/nodejs24', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServicePHPCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.php';
        Module.init(module, 'PHP');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/php-fpm', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                    $scope.getphpsettings();
                    $scope.getfpmsettings();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };

        $scope.setting = {
            'php': {
                'short_open_tag': false,
                'expose_php': false,
                'max_execution_time': '',
                'memory_limit': '',
                'display_errors': false,
                'post_max_size': '',
                'upload_max_filesize': '',
                'date.timezone': ''
            },
            'fpm': {
                'listen': '',
                'pm': false,
                'pm.max_children': '',
                'pm.start_servers': '',
                'pm.min_spare_servers': '',
                'pm.max_spare_servers': '',
                'pm.max_requests': '',
                'request_terminate_timeout': '',
                'request_slowlog_timeout': ''
            }
        };

        var _toint = function (v) {
            v = parseInt(v);
            if (isNaN(v))
                v = '';
            else
                v += '';
            return v;
        };

        $scope.getphpsettings = function () {
            if (!$scope.installed) return;
            Request.post('/api/operation/php', {
                'action': 'getphpsettings'
            }, function (res) {
                if (res.code == 0) {
                    var s = res.data;
                    var d = $scope.setting['php'];
                    d['short_open_tag'] = (s['short_open_tag'] && s['short_open_tag'].toLowerCase() == 'on');
                    d['expose_php'] = (s['expose_php'] && s['expose_php'].toLowerCase() == 'on');
                    d['max_execution_time'] = s['max_execution_time'] ? s['max_execution_time'] : '';
                    d['memory_limit'] = s['memory_limit'] ? _toint(s['memory_limit']) : '';
                    d['display_errors'] = (s['display_errors'] && s['display_errors'].toLowerCase() == 'on');
                    d['post_max_size'] = s['post_max_size'] ? _toint(s['post_max_size']) : '';
                    d['upload_max_filesize'] = s['upload_max_filesize'] ? _toint(s['upload_max_filesize']) : '';
                    d['date.timezone'] = s['date.timezone'] ? s['date.timezone'] : '';
                }
            }, false, true);
        };

        $scope.getfpmsettings = function () {
            if (!$scope.installed) return;
            Request.post('/api/operation/php', {
                'action': 'getfpmsettings'
            }, function (res) {
                if (res.code == 0) {
                    var s = res.data;
                    var d = $scope.setting['fpm'];
                    d['listen'] = s['listen'] ? s['listen'] : '';
                    d['pm'] = (s['pm'] && s['pm'].toLowerCase() == 'dynamic');
                    d['pm.max_children'] = s['pm.max_children'] ? _toint(s['pm.max_children']) : '';
                    d['pm.start_servers'] = s['pm.start_servers'] ? _toint(s['pm.start_servers']) : '';
                    d['pm.min_spare_servers'] = s['pm.min_spare_servers'] ? _toint(s['pm.min_spare_servers']) : '';
                    d['pm.max_spare_servers'] = s['pm.max_spare_servers'] ? _toint(s['pm.max_spare_servers']) : '';
                    d['pm.max_requests'] = s['pm.max_requests'] ? _toint(s['pm.max_requests']) : '';
                    d['request_terminate_timeout'] = s['request_terminate_timeout'] ? _toint(s['request_terminate_timeout']) : '';
                    d['request_slowlog_timeout'] = s['request_slowlog_timeout'] ? _toint(s['request_slowlog_timeout']) : '';
                }
            }, false, true);
        };

        $scope.updatephpsettings = function () {
            var data = angular.copy($scope.setting.php);
            data.action = 'updatephpsettings';
            Request.post('/api/operation/php', data, $scope.getphpsettings);
        };
        $scope.updatefpmsettings = function () {
            var data = angular.copy($scope.setting.fpm);
            data.action = 'updatefpmsettings';
            Request.post('/api/operation/php', data, $scope.getfpmsettings);
        };
    }
];

var ServiceSendmailCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.sendmail';
        Module.init(module, 'Sendmail');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/sendmail', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceSSHCtrl = [
    '$scope', '$routeParams', 'Module', 'Request', 'Task', 'Message',
    function ($scope, $routeParams, Module, Request, Task, Message) {
        var module = 'service.ssh';
        Module.init(module, 'SSH');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/sshd', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    $scope.getsettings();
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };

        $scope.setting = {};
        $scope.getsettings = function () {
            if (!$scope.installed) return;
            Request.post('/api/operation/ssh', {
                'action': 'getsettings'
            }, function (res) {
                if (res.code == 0) {
                    $scope.setting = res.data;
                    $scope.setting.disable_pwdauth = !$scope.setting.enable_pwdauth;
                }
            }, false, true);
        };
        $scope.savesettings = function () {
            var data = {};
            data.action = 'savesettings';
            data.port = $scope.setting.port;
            data.enable_pwdauth = $scope.setting.enable_pwdauth;
            data.enable_sftp = $scope.setting.enable_sftp;
            Request.post('/api/operation/ssh', data, function (res) {
                if (res.code == 0) {
                    $scope.getsettings();
                }
            });
        };
        $scope.savepksettings = function () {
            var data = {};
            data.action = 'savesettings';
            data.pubkey = $scope.setting.pubkey;
            data.enable_pubkauth = $scope.setting.enable_pubkauth;
            data.enable_pwdauth = !$scope.setting.disable_pwdauth;
            Request.post('/api/operation/ssh', data, function (res) {
                if (res.code == 0) {
                    $scope.getsettings();
                }
            });
        };
        $scope.gensshkey = function () {
            if ($scope.setting.pubkey || $scope.setting.prvkey) {
                $scope.confirm_title = '重新生成公钥/私钥对';
                $scope.confirm_body = '公钥/私钥已存在，是否覆盖原文件？';
                $('#confirm').modal();
                $scope.confirm = $scope.dogenkey;
                return;
            }
            $scope.dogenkey();
        };
        $scope.dogenkey = function () {
            Task.call(
                $scope,
                module,
                '/api/task/ssh.genkey',
                '/api/task/ssh.genkey', {}, {
                    'success': function () {
                        $scope.getsettings();
                    }
                }
            );
        };
        $scope.chpasswd = function () {
            $('#chpasswd').modal();
        };
        $scope.dochpasswd = function () {
            if ($scope.newpassword != $scope.newpasswordc) {
                Message.setError('新密码和确认密码不一致！');
                return;
            }
            Task.call(
                $scope,
                module,
                '/api/task/ssh.chpasswd',
                '/api/task/ssh.chpasswd', {
                    'path': $scope.setting.prvkey,
                    'oldpassword': $scope.oldpassword,
                    'newpassword': $scope.newpassword
                }, {
                    'success': function () {
                        $scope.oldpassword = $scope.newpassword = $scope.newpasswordc = '';
                    }
                }
            );
        };
    }
];

var ServiceIPTablesCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.iptables';
        Module.init(module, 'IPTables');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/iptables', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceFirewalldCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.firewalld';
        Module.init(module, 'Firewalld');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/firewalld', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceUfwCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.ufw';
        Module.init(module, 'UFW');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/ufw', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceFail2banCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.fail2ban';
        Module.init(module, 'Fail2Ban');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/fail2ban', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceCronCtrl = [
    '$scope', '$routeParams', 'Module', 'Request', 'Message',
    function ($scope, $routeParams, Module, Request, Message) {
        var module = 'service.cron';
        Module.init(module, 'Cron');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;
        var section = Module.getSection();

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/crond', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
            if (section && section == 'settings') {
                $scope.tabSettings();
            }
        };
        $scope.settings = {};
        $scope.getSettings = function () {
            if (!$scope.installed) return;
            Request.post('/api/operation/cron', {
                'action': 'get_settings'
            }, function (res) {
                if (res.code == 0) {
                    $scope.settings = res.data;
                    Message.setSuccess(res.msg);
                }
            }, false, true);
        };
        $scope.updateSetting = function () {
            if (!$scope.installed) return;
            Request.post('/api/operation/cron', {
                'action': 'save_settings',
                'mailto': $scope.settings.mailto
            }, function (res) {
                if (res.code == 0) {
                    $scope.tabSettings();
                    Message.setSuccess(res.msg);
                } else if (res.code == -1) {
                    Message.setError(res.msg);
                }
            }, false, true);
        };
        $scope.tabSettings = function () {
            $scope.sec('settings');
            Module.setSection('settings');
            $scope.getSettings();
        }
    }
];

var ServiceNTPCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.ntp';
        Module.init(module, 'NTP');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/ntpd', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];

var ServiceNamedCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.named';
        var section = Module.getSection();
        Module.init(module, 'named');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/named', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                    if (section == 'settings') {
                        $scope.load_settings();
                    }
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
        $scope.load_settings = function () {
            if (!$scope.installed) return;
            $scope.getsettings();
            $scope.sec('settings');
            Module.setSection('settings');
        };
        $scope.getsettings = function () {
            Request.post('/api/operation/named', {
                'action': 'getsettings'
            }, function (data) {
                if (data.code == 0) {
                    $scope.baseconfigs = data.data;
                }
            });
        };

        $scope.savesettings = function () {
            $scope.processing = true;
            Request.post('/api/operation/named', {
                'action': 'savesettings'
            }, function (data) {
                if (data.code == 0) {
                    $scope.getsettings();
                }
                $scope.processing = false;
            });
        };
    }
];

var ServiceLighttpdCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.lighttpd';
        var section = Module.getSection();
        Module.init(module, 'Lighttpd');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/lighttpd', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if (section == 'settings') {
                        $scope.load_settings();
                    }
                    if ($scope.checkVersion) {
                        $scope.checkVersion();
                    }
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
        $scope.load_settings = function () {
            if (!$scope.installed) return;
            $scope.getsettings();
            $scope.sec('settings');
            Module.setSection('settings');
        };
        $scope.getsettings = function () {
            Request.post('/api/operation/lighttpd', {
                'action': 'getsettings'
            }, function (data) {
                if (data.code == 0) {
                    $scope.baseconfigs = data.data;
                }
            });
        };
        $scope.savesettings = function () {
            $scope.processing = true;
            Request.post('/api/operation/lighttpd', {
                'action': 'savesettings'
            }, function (data) {
                if (data.code == 0) {
                    $scope.getsettings();
                }
                $scope.processing = false;
            });
        };
    }
];

var ServiceProFTPDCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.proftpd';
        var section = Module.getSection();
        Module.init(module, 'ProFTPD');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/proftpd', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if (section == 'settings') {
                        $scope.load_settings();
                    }
                    if ($scope.checkVersion) {
                        $scope.checkVersion();
                    }
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
        $scope.load_settings = function () {
            if (!$scope.installed) return;
            $scope.getsettings();
            $scope.sec('settings');
            Module.setSection('settings');
        };
        $scope.getsettings = function () {
            Request.post('/api/operation/proftpd', {
                'action': 'getsettings'
            }, function (data) {
                if (data.code == 0) {
                    $scope.baseconfigs = data.data;
                }
            });
        };

        $scope.savesettings = function () {
            $scope.processing = true;
            Request.post('/api/operation/proftpd', {
                'action': 'savesettings'
            }, function (data) {
                if (data.code == 0) {
                    $scope.getsettings();
                }
                $scope.processing = false;
            });
        };
    }
];

var ServicePureFTPdCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.pureftpd';
        var section = Module.getSection();
        Module.init(module, 'Pure-FTPd');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/pure-ftpd', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if (section == 'settings') {
                        $scope.load_settings();
                    }
                    if ($scope.checkVersion) {
                        $scope.checkVersion();
                    }
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };

        $scope.load_settings = function () {
            if (!$scope.installed) return;
            $scope.getsettings();
            $scope.sec('settings');
            Module.setSection('settings');
        };
        $scope.getsettings = function () {
            Request.post('/api/operation/pureftpd', {
                'action': 'getsettings'
            }, function (data) {
                if (data.code == 0) {
                    $scope.baseconfigs = data.data;
                }
            });
        };
        $scope.savesettings = function () {
            $scope.processing = true;
            Request.post('/api/operation/pureftpd', {
                'action': 'savesettings'
            }, function (data) {
                if (data.code == 0) {
                    $scope.getsettings();
                }
                $scope.processing = false;
            });
        };
    }
];

var ServiceSambaCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'service.samba';
        Module.init(module, 'Samba');
        Module.initSection('base');
        $scope.scope = $scope;
        $scope.info = null;
        $scope.loaded = false;

        $scope.installed = false;
        $scope.waiting = true;
        $scope.checking = false;

        $scope.checkInstalled = function () {
            $scope.checking = true;
            Request.get('/api/service/detail/smb', function (res) {
                var info = res.data;
                if (res.code === 0 && info) {
                    $scope.installed = true;
                    $scope.autostart = info.autostart;
                    $scope.status = info.status;
                    $scope.detail = info;
                    if ($scope.checkVersion) $scope.checkVersion();
                } else {
                    $scope.installed = false;
                }
                $scope.loaded = true;
                $scope.waiting = false;
                $scope.checking = false;
            });
        };
    }
];
