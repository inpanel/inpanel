angular.module('inpanel.directives', []).
    directive('navbar', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/container/directives/navbar.html',
            controller: ['$scope', '$rootScope', function ($scope, $rootScope) {
                $rootScope.navbar_loaded = true;
            }]
        };
    }).
    directive('loading', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            controller: ['$scope', function ($scope) {
                if (!$scope.loadingText) $scope.loadingText = '模块加载中，请稍候......';
            }],
            template: '<div class="text-center">\
            <h6>{{loadingText}}</h6>\
            <div class="progress" style="width:230px;margin-left: auto;margin-right: auto;">\
            <div class="progress-bar progress-bar-striped active" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="100" style="width:100%;"></div>\
            </div></div>',
            replace: true
        };
    }).
    directive('message', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/container/directives/message.html',
            controller: ['$scope', '$rootScope', function ($scope, $rootScope) {
                $rootScope.showErrorMsg = false;
                $rootScope.errorMessage = '';
                $rootScope.showSuccessMsg = false;
                $rootScope.successMessage = '';
                $rootScope.showWarningMsg = false;
                $rootScope.warningMessage = '';
                $rootScope.showInfoMsg = false;
                $rootScope.infoMessage = '';
                $scope.$rootScope = $rootScope;
                if (!$scope.id) $scope.id = 'message';
            }]
        };
    }).
    directive('srvminiop', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/container/directives/srvminiop.html',
            controller: ['$scope', function ($scope) {
                $scope.$scope = $scope.$parent;
            }]
        };
    }).
    directive('srvbase', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/container/directives/srvbase.html',
            controller: ['$rootScope', '$scope', 'Request', 'Task', function ($rootScope, $scope, Request, Task) {
                $scope.$scope = $scope.$parent;

                // 从父 scope 的 detail 对象读取包信息
                $scope.pkginfo = $scope.$parent.detail ? {
                    'name': $scope.$parent.detail.package_name || $scope.$parent.detail.name,
                    'version': $scope.$parent.detail.package_version || '',
                    'summary': $scope.$parent.detail.description || ''
                } : null;

                // checkVersion 改为从 detail 刷新包信息
                $scope.$parent.checkVersion = function () {
                    var detail = $scope.$parent.detail;
                    if (detail) {
                        $scope.pkginfo = {
                            'name': detail.package_name || detail.name,
                            'version': detail.package_version || '',
                            'summary': detail.description || ''
                        };
                    }
                };

                $scope.toggleAutostart = function () {
                    Request.post('/api/service/chkconfig', {
                        'service': $scope.service || $scope.$parent.service,
                        'autostart': $scope.$parent.autostart ? 'off' : 'on'
                    }, function () {
                        $scope.$parent.checkInstalled();
                    });
                };

                var serviceop = function (action) {
                    return function () {
                        var svc = $scope.service || $scope.$parent.service;
                        Task.call(
                            $scope.$parent,
                            $rootScope.module,
                            '/api/task/service.' + action,
                            '/api/task/service.' + action + '_' + svc, {
                                'name': $scope.name,
                                'service': svc
                            },
                            $scope.$parent.checkInstalled
                        );
                    };
                };

                $scope.start = serviceop('start');
                $scope.stop = serviceop('stop');
                $scope.restart = serviceop('restart');
            }]
        };
    }).
    directive('srvinstall', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/container/directives/srvinstall.html',
            controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Task', function ($rootScope, $scope, Request, Timeout, Task) {
                $scope.$scope = $scope.$parent;

                $scope.installing = false;
                $scope.installMsg = '';

                // 异步安装服务
                $scope.startInstall = function () {
                    $scope.installMsg = '正在安装...';
                    $scope.installing = true;
                    var svc = $scope.service || $scope.$parent.service;
                    Task.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/api/task/service.install',
                        '/api/task/service.install_' + svc, {
                            'service': svc
                        }, {
                            'wait': function (data) {
                                $scope.installMsg = data.msg || '正在安装...';
                            },
                            'success': function (data) {
                                $scope.installMsg = data.msg || '安装完成';
                                Timeout(function () {
                                    $scope.installing = false;
                                    $scope.$parent.checkInstalled();
                                }, 2000, $rootScope.module);
                            },
                            'error': function (data) {
                                $scope.installMsg = data.msg || '安装失败';
                                Timeout(function () {
                                    $scope.installing = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };

                // 异步卸载服务
                $scope.uninstall = function () {
                    $scope.installMsg = '正在卸载...';
                    $scope.installing = true;
                    var svc = $scope.service || $scope.$parent.service;
                    Task.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/api/task/service.uninstall',
                        '/api/task/service.uninstall_' + svc, {
                            'service': svc
                        }, {
                            'wait': function (data) {
                                $scope.installMsg = data.msg || '正在卸载...';
                            },
                            'success': function (data) {
                                $scope.installMsg = data.msg || '卸载完成';
                                Timeout(function () {
                                    $scope.installing = false;
                                    $scope.$parent.checkInstalled();
                                }, 2000, $rootScope.module);
                            },
                            'error': function (data) {
                                $scope.installMsg = data.msg || '卸载失败';
                                Timeout(function () {
                                    $scope.installing = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };
            }]
        };
    }).
    directive('srvupdate', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/container/directives/srvupdate.html',
            controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Task', function ($rootScope, $scope, Request, Timeout, Task) {
                $scope.$scope = $scope.$parent;

                $scope.updating = false;
                $scope.updateMsg = '';

                // 异步升级服务
                $scope.startUpdate = function () {
                    $scope.updating = true;
                    $scope.updateMsg = '正在升级...';
                    var svc = $scope.service || $scope.$parent.service;
                    Task.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/api/task/service.install',
                        '/api/task/service.install_' + svc, {
                            'service': svc,
                            'action': 'upgrade'
                        }, {
                            'wait': function (data) {
                                $scope.updateMsg = data.msg || '正在升级...';
                            },
                            'success': function (data) {
                                $scope.updateMsg = data.msg || '升级完成';
                                Timeout(function () {
                                    $scope.updating = false;
                                    $scope.$parent.checkInstalled();
                                }, 2000, $rootScope.module);
                            },
                            'error': function (data) {
                                $scope.updateMsg = data.msg || '升级失败';
                                Timeout(function () {
                                    $scope.updating = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };
            }]
        };
    }).
    directive('srvext', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/container/directives/srvext.html',
            controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Task', function ($rootScope, $scope, Request, Timeout, Task) {
                $scope.$scope = $scope.$parent;

                $scope.operating = false;
                $scope.showMsg = '';

                $scope.start = function () {
                    $scope.operating = true;
                    $scope.showMsg = '正在检测版本信息...';
                    Task.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/api/task/yum.info',
                        '/api/task/yum.info_' + $scope.pkg, {
                            'pkg': $scope.pkg,
                            'repo': 'installed'
                        }, {
                            'wait': function (data) {
                                $scope.showMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.showMsg = data.msg;
                                $scope.pkginfo = data.data[0];
                                $scope.checkExt();
                            },
                            'error': function (data) {
                                $scope.showMsg = data.msg;
                                Timeout(function () {
                                    $scope.operating = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };

                // check and list ext of the pkg
                $scope.showExtList = false;
                $scope.checkExt = function () {
                    $scope.operating = true;
                    $scope.showExtList = false;
                    $scope.showMsg = '正在检测扩展...';
                    Task.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/api/task/yum.ext_info',
                        '/api/task/yum.ext_info_' + $scope.pkginfo.name, {
                            'pkg': $scope.pkginfo.name
                        }, {
                            'wait': function (data) {
                                $scope.showMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.showMsg = data.msg;
                                $scope.exts = data.data;
                                $scope.showExtList = true;
                            },
                            'error': function (data) {
                                $scope.showMsg = data.msg;
                                Timeout(function () {
                                    $scope.operating = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };

                // install specified version of ext in specified repository
                $scope.install = function (repo, name, version, release) {
                    $scope.showMsg = '开始安装...';
                    $scope.showExtList = false;
                    Task.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/api/task/yum.install',
                        '/api/task/yum.install_' + repo + '_' + $scope.pkginfo.name + '_' + name + '_' + version + '_' + release, {
                            'repo': repo,
                            'pkg': $scope.pkginfo.name,
                            'ext': name,
                            'version': version,
                            'release': release
                        }, {
                            'wait': function (data) {
                                $scope.showMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.showMsg = data.msg;
                                Timeout(function () {
                                    $scope.operating = false;
                                    $scope.checkExt();
                                }, 3000, $rootScope.module);
                            },
                            'error': function (data) {
                                $scope.showMsg = data.msg;
                                Timeout(function () {
                                    $scope.operating = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };

                // uninstall specified version of ext in specified repository
                $scope.uninstall = function (repo, name, version, release) {
                    $scope.showMsg = '正在删除...';
                    $scope.showExtList = false;
                    Task.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/api/task/yum.uninstall',
                        '/api/task/yum.uninstall_' + $scope.pkginfo.name + '_' + name + '_' + version + '_' + release, {
                            'repo': repo,
                            'pkg': $scope.pkginfo.name,
                            'ext': name,
                            'version': version,
                            'release': release
                        }, {
                            'wait': function (data) {
                                $scope.showMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.showMsg = data.msg;
                                Timeout(function () {
                                    $scope.operating = false;
                                    $scope.checkExt();
                                }, 3000, $rootScope.module);
                            },
                            'error': function (data) {
                                $scope.showMsg = data.msg;
                                Timeout(function () {
                                    $scope.operating = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };
            }]
        };
    }).
    directive('srvuninstall', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/container/directives/srvuninstall.html',
            controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Task', function ($rootScope, $scope, Request, Timeout, Task) {
                $scope.$scope = $scope.$parent;

                $scope.uninstalling = false;
                $scope.uninstallMsg = '';

                // 异步卸载服务
                $scope.startUninstall = function () {
                    $scope.uninstallMsg = '正在卸载...';
                    $scope.uninstalling = true;
                    var svc = $scope.service || $scope.$parent.service;
                    Task.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/api/task/service.uninstall',
                        '/api/task/service.uninstall_' + svc, {
                            'service': svc
                        }, {
                            'wait': function (data) {
                                $scope.uninstallMsg = data.msg || '正在卸载...';
                            },
                            'success': function (data) {
                                $scope.uninstallMsg = data.msg || '卸载完成';
                                Timeout(function () {
                                    $scope.uninstalling = false;
                                    $scope.$parent.checkInstalled();
                                }, 2000, $rootScope.module);
                            },
                            'error': function (data) {
                                $scope.uninstallMsg = data.msg || '卸载失败';
                                Timeout(function () {
                                    $scope.uninstalling = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };
            }]
        };
    }).
    directive('srvfile', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/container/directives/srvfile.html',
            controller: ['$scope', function ($scope) {
                // 从父 scope 的 detail 读取 config_files，优先，否则回退到 ng-init 的 items
                $scope.$watch('$parent.detail', function (detail) {
                    if (detail && detail.config_files && detail.config_files.length > 0) {
                        $scope.items = detail.config_files.map(function (cf) {
                            return {
                                name: cf.label || cf.path,
                                path: cf.path,
                                isfile: !cf.path.endsWith('/'),
                                isdir: cf.path.endsWith('/')
                            };
                        });
                    }
                });
            }]
        };
    }).
    directive('srvlog', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/container/directives/srvlog.html',
            controller: ['$scope', function ($scope) {
                // 从父 scope 的 detail 读取 log_files
                $scope.$watch('$parent.detail', function (detail) {
                    if (detail && detail.log_files && detail.log_files.length > 0) {
                        $scope.items = detail.log_files.map(function (lf) {
                            return {
                                name: lf.label || lf.path,
                                path: lf.path,
                                isfile: true,
                                isdir: false
                            };
                        });
                    }
                });
            }]
        };
    }).
    directive('selector', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/container/directives/selector.html',
            controller: ['$scope', 'Request', function ($scope, Request) {
                $scope.$scope = $scope.$parent;
                $scope.onlydir = true;
                $scope.onlyfile = true;
                $scope.path = '/';
                var parse_path = function () {
                    // parse dir to array
                    if (!$scope.curpath) return;
                    var pathnames = $scope.curpath.split('/');
                    var pathinfos = [];
                    for (var i = 1; i < pathnames.length; i++) {
                        if (!pathnames[i]) continue;
                        var fullpath = pathnames[i - 1] + '/' + pathnames[i];
                        pathinfos.push({
                            'name': pathnames[i],
                            'path': fullpath
                        });
                        pathnames[i] = fullpath;
                    }
                    $scope.pathinfos = pathinfos;
                };
                $scope.load = function (path) {
                    if ($scope.onlyfile) {
                        $scope.otherdir = true;
                        $scope.listdir(path);
                    } else {
                        $scope.otherdir = false;
                        $scope.path = path;
                    }
                };
                $scope.listdir = function (path) {
                    if (path) $scope.path = path;
                    if (!$scope.path)
                        $scope.path = '/root';
                    else if ($scope.path != '/' && $scope.path.substr(-1) == '/')
                        $scope.path = $scope.path.substr(0, $scope.path.length - 1);
                    $scope.path = $scope.path.replace('//', '/');

                    var curpath = $scope.path;
                    Request.post('/api/operation/file', {
                        'action': 'listdir',
                        'path': curpath,
                        'showhidden': false,
                        'remember': false,
                        'onlydir': $scope.onlydir
                    }, function (data) {
                        if (data.code == 0) {
                            $scope.items = data.data;
                            $scope.curpath = curpath;
                            $scope.lastpath = curpath;
                            $scope.curpath_pre = curpath == '/' ? '' : curpath;
                        } else {
                            $scope.path = $scope.lastpath;
                        }
                        parse_path();
                    }, false, true);
                };
                //$scope.listdir();
                $scope.$parent.selector = $scope;
            }]
        };
    }).
    directive('autofocus', function () {
        return function ($scope, element) {
            element[0].focus();
        };
    }).
    directive('waiting', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            controller: ['$scope', function ($scope) {
                $scope.waitingText = $scope.waitingText || '正在加载列表，请稍候......';
            }],
            template: '<div class="well"><img src="images/loading.gif" style="margin-right: 10px;">{{waitingText}}</div>',
            replace: true
        };
    }).
    directive('plugins', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {
                'pluginsName': '='
            },
            replace: true,
            templateUrl: template_path + '/plugins/acme/static/index.html',
            link: function ($scope, $element, $attrs, ctrl) {
                console.log($scope.pluginsName);
            },
            controller: ['$scope', '$rootScope', function ($scope, $rootScope) {
                $rootScope.navbar_loaded = true;
            }]
        };
    });