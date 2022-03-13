var LoginCtrl = [
    '$scope', '$rootScope', '$location', 'Module', 'Message', 'Request',
    function ($scope, $rootScope, $location, Module, Message, Request) {
        var module = 'login';
        Module.init(module, '登录');
        $scope.loginText = '登录';
        $scope.errorText = '';
        $scope.showForgetPwdMsg = false;
        $scope.loaded = true;
        $scope.username = '';
        $scope.password = '';

        var password_strength = function (pwd) {
            var strongRegex = new RegExp("^(?=.{8,})(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*\\W).*$", "g");
            var mediumRegex = new RegExp("^(?=.{7,})(((?=.*[A-Z])(?=.*[a-z]))|((?=.*[A-Z])(?=.*[0-9]))|((?=.*[a-z])(?=.*[0-9]))).*$", "g");
            var enoughRegex = new RegExp("(?=.{6,}).*", "g");
            if (false == enoughRegex.test(pwd)) {
                return '无安全性可言';
            } else if (strongRegex.test(pwd)) {
                return '高';
            } else if (mediumRegex.test(pwd)) {
                return '一般';
            } else {
                return '低';
            }
        };

        $scope.login = function (rawpwd) {
            $scope.errorText = '';
            if ($scope.username.replace(/(^\s*)|(\s*$)/g, '') === '') {
                $scope.errorText = '用户名不能为空！';
                return
            }
            if ($scope.password.replace(/(^\s*)|(\s*$)/g, '') === '') {
                $scope.errorText = '密码不能为空！';
                return
            }
            $scope.loginText = '登录中...';
            Request.post('/api/login', {
                username: $scope.username,
                password: rawpwd ? $scope.password : hex_md5($scope.password)
            }, function (data) {
                if (data.code >= 0) {
                    $scope.loaded = false;
                    var path = $rootScope.loginto ? $rootScope.loginto : '/main';
                    var section = $rootScope.loginto_section;
                    if (data.code == 0) {
                        $location.path(path);
                        if (section) {
                            $scope.sec(section);
                        }
                    } else {
                        // need to check the password strength
                        $scope.pwdStrength = password_strength($scope.password);
                        if ($scope.pwdStrength != '高') {
                            Message.setError(false);
                            Message.setWarning(false);
                            $('#main').hide();
                            $scope.loginMessage = data.msg;
                            $scope.loginWarning = true;
                        } else {
                            $location.path(path);
                            if (section) {
                                $scope.sec(section);
                            }
                        }
                    }
                } else {
                    $scope.loginText = '登录';
                }
            });
        };
    }
];

var LogoutCtrl = [
    '$scope', '$location', 'Module', 'Request', 'Timeout',
    function ($scope, $location, Module, Request, Timeout) {
        var module = 'logout';
        Module.init(module, '退出登录');
        $scope.loaded = false;
        Timeout(function () {
            $scope.loaded = true;
            Request.get('/api/xsrf', function () {
                Request.post('/api/logout', {}, function (data) {
                    Timeout(function () {
                        $location.path('/');
                    }, 3000, module);
                });
            });
        }, 1000, module);
    }
];

var deepUpdate = function (orgObj, newObj) {
    for (i in newObj) {
        if (typeof (newObj[i]) == 'object') {
            deepUpdate(orgObj[i], newObj[i]);
        } else {
            if (orgObj[i] != newObj[i]) {
                orgObj[i] = newObj[i];
            }
        }
    }
};

var MainCtrl = [
    '$scope', '$routeParams', '$location', 'Module', 'Timeout', 'Request',
    function ($scope, $routeParams, $location, Module, Timeout, Request) {
        var module = 'main';
        Module.init(module, '首页');
        Module.initSection('server');
        $scope.version = {};
        $scope.info = null;
        $scope.loaded = false;

        $scope.detectVer = true;
        $scope.hasNewver = false;
        $scope.auto_refresh = false;

        $scope.checkUpVersion = function () {
            Request.get('/api/version', function (res) {
                $scope.version = res.data;
                $scope.checkNewVersion();
            });
        }
        $scope.checkNewVersion = function () {
            Request.get('/api/setting/upver', function (data) {
                if (data.code == -1) {
                    $scope.upverMessage = data.msg;
                } else if (data.code == 0) {
                    var v = data.data;
                    if (
                        parseFloat(v.version) > parseFloat($scope.version.version) ||
                        (parseFloat(v.version) == parseFloat($scope.version.version) && parseInt(v.build) > parseInt($scope.version.build))
                    ) {
                        $scope.detectVer = false;
                        $scope.hasNewver = true;
                    }
                }
            });
        };

        $scope.checkUpdate = function () {
            $location.path('/setting');
            $scope.sec('upversion');
        }
        $scope.loadInfo = function (items) {
            $scope.checkUpVersion();
            if (!items) items = '*';
            Request.get('/api/query/' + items, function (data) {
                if ($scope.info == null) {
                    $scope.info = data;
                    $scope.info['server.cpustat']['total']['used_rate'] = '获取中...';
                    for (var i = 0; i < data['server.netifaces'].length; i++) {
                        $scope.info['server.netifaces'][i]['rx_speed'] = '0';
                        $scope.info['server.netifaces'][i]['tx_speed'] = '0';
                    }
                    if (!$scope.loaded) $scope.loaded = true;
                } else {
                    if ($scope.info) {
                        // caculate the cpu usage
                        var stat = data['server.cpustat']['total'];
                        var orgstat = $scope.info['server.cpustat']['total'];
                        var used = (stat['used'] - orgstat['used']) / (stat['all'] - orgstat['all']);
                        used = Math.round(used * 10000) * 10;
                        var idle = 100000 - used;
                        used = ((used + 1) / 1000).toString();
                        idle = ((idle + 1) / 1000).toString();
                        stat['used_rate'] = used.substring(0, used.length - 1) + '%';
                        stat['idle_rate'] = idle.substring(0, idle.length - 1) + '%';
                        // caculate the network speeds
                        var ifs = data['server.netifaces'];
                        var orgifs = $scope.info['server.netifaces'];
                        for (var i = 0; i < ifs.length; i++) {
                            var td = ifs[i]['timestamp'] - orgifs[i]['timestamp'];
                            if (td > 0) {
                                ifs[i]['rx_speed'] = Math.round((ifs[i]['rx_bytes'] - orgifs[i]['rx_bytes']) / td);
                                ifs[i]['tx_speed'] = Math.round((ifs[i]['tx_bytes'] - orgifs[i]['tx_bytes']) / td);
                            }
                        }
                    }
                    deepUpdate($scope.info, data);
                }
                if ($scope.auto_refresh) {
                    Timeout($scope.loadInfo, 1000, module);
                }
            });
        };

        $scope.refresh = function () {
            $scope.loadInfo();
        };
        $scope.auto_refresh_open = function () {
            $scope.auto_refresh = true;
            $scope.loadInfo();
        };
        $scope.auto_refresh_close = function () {
            $scope.auto_refresh = false;
        };
    }
];

var FtpCtrl = [
    '$scope', 'Module',
    function ($scope, Module) {
        var module = 'ftp';
        Module.init(module, 'FTP管理');
        $scope.loaded = false;

        var section = Module.getSection();
        $scope.load = function () {
            $scope.loaded = true;
            if (section && section == 'users') {
                $scope.loadUsers();
            } else if (section && section == 'process') {
                $scope.loadProcess();
            } else {
                $scope.loadUsers();
            }
        }
        $scope.loadUsers = function () {
            $scope.sec('users');
            Module.setSection('users');
        };
        $scope.loadProcess = function () {
            $scope.sec('process');
            Module.setSection('process');
        };
    }
];

var BackupCtrl = ['$scope', 'Module',
    function ($scope, Module) {
        var module = 'backup';
        Module.init(module, '备份管理');
        $scope.loaded = false;

        var section = Module.getSection();
        $scope.load = function () {
            $scope.loaded = true;
            if (section && section == 'files') {
                $scope.loadFiles();
            } else if (section && section == 'database') {
                $scope.loadDatabase();
            } else if (section && section == 'remote') {
                $scope.loadRemote();
            } else {
                $scope.loadFiles();
            }
        }
        $scope.loadFiles = function () {
            $scope.sec('files');
            Module.setSection('files');
        };
        $scope.loadDatabase = function () {
            $scope.sec('database');
            Module.setSection('database');
        };
        $scope.loadRemote = function () {
            $scope.sec('remote');
            Module.setSection('remote');
        };
    }
];

var SecureCtrl = [
    '$scope', 'Module',
    function ($scope, Module) {
        var module = 'secure';
        Module.init(module, '安全管理');
        $scope.loaded = true;
    }
];

var LogCtrl = [
    '$scope', 'Module',
    function ($scope, Module) {
        var module = 'log';
        Module.init(module, '日志管理');
        $scope.loaded = true;
    }
];

var SettingCtrl = [
    '$scope', '$routeParams', 'Module', 'Timeout', 'Message', 'Request',
    function ($scope, $routeParams, Module, Timeout, Message, Request) {
        var module = 'setting';
        Module.init(module, '系统设置');
        Module.initSection('authinfo');
        $scope.version = {};
        $scope.newVersion = '';
        $scope.newReleasetime = '';
        $scope.newBuild = '';
        $scope.showUpdateBtn = false;
        $scope.showRestartBtn = true;
        $scope.loaded = true;
        $scope.password = '';
        $scope.passwordc = '';

        $scope.checkUpVersion = function () {
            Request.get('/api/version', function (res) {
                $scope.version = res.data;
                $scope.checkNewVersion();
            });
        }

        $scope.loadAuthInfo = function () {
            Request.get('/api/setting/auth', function (res) {
                $scope.username = res.username;
                $scope.passwordcheck = res.passwordcheck;
            });
        }
        $scope.loadServerInfo = function () {
            Request.get('/api/setting/server', function (res) {
                $scope.forcehttps = res.forcehttps;
                $scope.ip = res.ip;
                $scope.port = res.port;
                $scope.sslkey = res.sslkey;
                $scope.sslcrt = res.sslcrt;
            });
        }
        $scope.loadAccessKey = function () {
            Request.get('/api/setting/accesskey', function (res) {
                $scope.accesskey = res.accesskey;
                $scope.accesskeyenable = res.accesskeyenable;
            });
        }
        $scope.updateAuthInfo = function () {
            Request.post('/api/setting/auth', {
                username: $scope.username,
                password: $scope.password ? hex_md5($scope.password) : '',
                passwordc: $scope.passwordc ? hex_md5($scope.passwordc) : '',
                passwordcheck: $scope.passwordcheck
            }, function (res) {
                if (res.code == 0) $scope.loadAuthInfo();
            });
        };
        $scope.updateServerInfo = function () {
            Request.post('/api/setting/server', {
                forcehttps: $scope.forcehttps,
                ip: $scope.ip,
                port: $scope.port,
                sslkey: $scope.sslkey,
                sslcrt: $scope.sslcrt
            }, function (res) {
                if (res.code == 0) $scope.loadServerInfo();
            });
        };

        // ssl selector
        $scope.selectsslcrt = function () {
            $scope.selector_title = '请选择证书文件（*.crt）';
            $scope.selector.onlydir = false;
            $scope.selector.onlyfile = true;
            $scope.selector.load('/');
            $scope.selector.selecthandler = function (path) {
                $('#selector').modal('hide');
                $scope.sslcrt = path;
            };
            $('#selector').modal();
        };
        $scope.selectsslkey = function () {
            $scope.selector_title = '请选择私钥文件（*.key）';
            $scope.selector.onlydir = false;
            $scope.selector.onlyfile = true;
            $scope.selector.load('/');
            $scope.selector.selecthandler = function (path) {
                $('#selector').modal('hide');
                $scope.sslkey = path;
            };
            $('#selector').modal();
        };

        $scope.updateAccessKey = function () {
            Request.post('/api/setting/accesskey', {
                accesskey: $scope.accesskey,
                accesskeyenable: $scope.accesskeyenable
            }, function (res) {
                if (res.code == 0) $scope.loadAccessKey();
            });
        };
        $scope.checkNewVersion = function () {
            $scope.upverMessage = '正在检测新版本...';
            Request.get('/api/setting/upver?force=1', function (data) {
                if (data.code == -1) {
                    $scope.upverMessage = data.msg;
                } else if (data.code == 0) {
                    var v = data.data;
                    if (
                        parseFloat(v.version.split('.').join('')) > parseFloat($scope.version.version.split('.').join('')) ||
                        (v.version == $scope.version.version && parseInt(v.build) > parseInt($scope.version.build))
                    ) {
                        $scope.upverMessage = '<table class="table table-hover table-bordered">' +
                            '<thead><tr><th colspan="2">有可用的新版本</th></tr></thead>' +
                            '<tbody><tr><td style="width: 200px;">版本信息：</td><td>v' + v.version + ' b' + v.build + '</td></tr>' +
                            '<tr><td>发布时间：</td><td>' + v.releasetime + '</td></tr>' +
                            '<tr><td>变更记录：</td><td><a href="' + v.changelog + '" target="_blank">' +
                            '查看版本变更记录</a></td></tr></tbody></table>';
                        $scope.updateBtnText = '开始在线升级';
                        $scope.showUpdateBtn = true;
                        $scope.newVersion = v.version;
                        $scope.newBuild = v.build;
                        $scope.newReleasetime = v.releasetime;
                    } else {
                        $scope.upverMessage = '当前已是最新版本！';
                    }
                }
            });
        };
        $scope.update = function () {
            $scope.upverMessage = '正在升级，请稍候...'
            $scope.showUpdateBtn = false;
            Request.post('/api/backend/update', {}, function (data) {
                var getUpdateStatus = function () {
                    Request.get('/api/backend/update', function (data) {
                        Message.setInfo('')
                        if (data.msg) $scope.upverMessage = data.msg;
                        if (data.code == -1) {
                            return false;
                        } else if (data.status == 'finish' && data.code == 0) {
                            // restart service
                            $scope.upverMessage = '正在重启 InPanel...';
                            Timeout(function () {
                                Request.post('/api/backend/service_restart', {
                                    service: 'inpanel'
                                }, function (data) {
                                    var getRestartStatus = function () {
                                        Request.get('/api/backend/service_restart_inpanel', function (data) {
                                            Message.setInfo('')
                                            if (data.msg) $scope.upverMessage = data.msg;
                                            Timeout(getRestartStatus, 500, module);
                                        }, function (data, status) { // error occur because server is terminate
                                            if (status == 403 || status == 0) {
                                                $scope.upverMessage = '升级成功！请刷新页面重新登录。';
                                                return false;
                                            }
                                            return true;
                                        });
                                    };
                                    Timeout(getRestartStatus, 500, module);
                                });
                            }, 1000, module);
                        } else {
                            Timeout(getUpdateStatus, 500, module);
                        }
                    });
                };
                Timeout(getUpdateStatus, 500, module);
            });
        };
        $scope.restartMessage = '是否要重启 InPanel ？';
        $scope.restart = function () {
            $scope.restartMessage = '正在重启，请稍候...'
            $scope.showRestartBtn = false;
            Timeout(function () {
                Request.post('/api/backend/service_restart', {
                    service: 'inpanel'
                }, function (data) {
                    var getRestartStatus = function () {
                        Request.get('/api/backend/service_restart_inpanel', function (data) {
                            if (data.msg) $scope.restartMessage = data.msg;
                            Timeout(getRestartStatus, 500, module);
                        }, function (data, status) { // error occur because server is terminate
                            if (status == 403 || status == 0) {
                                $scope.restartMessage = '重启成功！请刷新页面重新登录。';
                                return false;
                            }
                            return true;
                        });
                    };
                    Timeout(getRestartStatus, 500, module);
                });
            }, 1000, module);
        };

        $scope.genaccesskey = function () {
            var randstring = '';
            for (var i = 0; i < 32; i++) {
                randstring += String.fromCharCode(Math.floor(256 * Math.random()));
            }

            // JS base64 REF: http://stackoverflow.com/questions/246801/how-can-you-encode-to-base64-using-javascript
            var b64encode = function (input) {
                var b64keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
                var output = "";
                var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
                var i = 0;

                while (i < input.length) {

                    chr1 = input.charCodeAt(i++);
                    chr2 = input.charCodeAt(i++);
                    chr3 = input.charCodeAt(i++);

                    enc1 = chr1 >> 2;
                    enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
                    enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
                    enc4 = chr3 & 63;

                    if (isNaN(chr2)) {
                        enc3 = enc4 = 64;
                    } else if (isNaN(chr3)) {
                        enc4 = 64;
                    }

                    output = output +
                        b64keyStr.charAt(enc1) + b64keyStr.charAt(enc2) +
                        b64keyStr.charAt(enc3) + b64keyStr.charAt(enc4);
                }

                return output;
            };

            $scope.accesskey = b64encode(randstring);
        };
    }
];

var SorryCtrl = [
    '$scope', 'Module', '$timeout',
    function ($scope, Module, $timeout) {
        var module = 'sorry';
        Module.init(module, '页面不存在');
        $scope.loaded = true;
    }
];