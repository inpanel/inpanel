angular.module('inpanel.directives', []).
    directive('navbar', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/directives/navbar.html',
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
            templateUrl: template_path + '/partials/directives/message.html',
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
            templateUrl: template_path + '/partials/directives/srvminiop.html',
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
            templateUrl: template_path + '/partials/directives/srvbase.html',
            controller: ['$rootScope', '$scope', 'Request', 'Backend', function ($rootScope, $scope, Request, Backend) {
                $scope.$scope = $scope.$parent;
                $scope.pkginfo = null;

                $scope.$parent.checkVersion = function () {
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_info',
                        '/backend/yum_info_' + $scope.pkg, {
                            'pkg': $scope.pkg,
                            'repo': 'installed'
                        }, {
                            'success': function (data) {
                                $scope.$parent.pkginfo = $scope.pkginfo = data.data[0];
                            },
                            'error': function (data) {
                                $scope.pkginfo = {
                                    'name': '获取失败！'
                                };
                            }
                        },
                        true
                    );
                };

                $scope.toggleAutostart = function () {
                    Request.post('/operation/chkconfig', {
                        'name': $scope.name,
                        'service': $scope.service,
                        'autostart': !$scope.$parent.autostart
                    }, function (data) {
                        $scope.$parent.checkInstalled();
                    });
                };

                var serviceop = function (action) {
                    return function () {
                        Backend.call(
                            $scope.$parent,
                            $rootScope.module,
                            '/backend/service_' + action,
                            '/backend/service_' + action + '_' + $scope.service, {
                                'name': $scope.name,
                                'service': $scope.service
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
            templateUrl: template_path + '/partials/directives/srvinstall.html',
            controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Backend', function ($rootScope, $scope, Request, Timeout, Backend) {
                $scope.$scope = $scope.$parent;

                var repolist = [];
                $scope.installing = false;
                $scope.installMsg = '';

                // check repolist
                $scope.startInstall = function () {
                    $scope.installMsg = '正在检测软件源...';
                    $scope.installing = true;
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_repolist',
                        '/backend/yum_repolist', {}, {
                            'wait': function (data) {
                                $scope.installMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.installMsg = data.msg;
                                if (data && data.data) {
                                    repolist = data.data;
                                }
                                $scope.installRepo();
                            },
                            'error': function (data) {
                                $scope.installMsg = data.msg;
                                Timeout(function () {
                                    $scope.installing = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };

                // install expected repolist
                $scope.installRepo = function () {
                    var newrepo_found = false;
                    for (var i = 0; i < $scope.expected_repolist.length; i++) {
                        var repo_found = false;
                        for (var j = 0; j < repolist.length; j++) {
                            if (repolist[j] == $scope.expected_repolist[i]) {
                                repo_found = true;
                                break;
                            }
                        }
                        if (repo_found) continue;

                        // install repo once a time
                        newrepo_found = true;
                        Backend.call(
                            $scope.$parent,
                            $rootScope.module,
                            '/backend/yum_installrepo',
                            '/backend/yum_installrepo_' + $scope.expected_repolist[i], {
                                'repo': $scope.expected_repolist[i]
                            }, {
                                'wait': function (data) {
                                    $scope.installMsg = data.msg;
                                },
                                'success': function (data) {
                                    $scope.installMsg = data.msg;
                                    repolist.push($scope.expected_repolist[i]);
                                    $scope.installRepo();
                                },
                                'error': function (data) {
                                    $scope.installMsg = data.msg;
                                    Timeout(function () {
                                        $scope.installing = false;
                                    }, 3000, $rootScope.module);
                                }
                            },
                            true
                        );
                        break;
                    }
                    // if no new repo be installed, goto next step
                    if (!newrepo_found) $scope.checkVersion();
                };

                // check and list versions of the pkg
                $scope.showVerList = false;
                $scope.checkVersion = function () {
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_info',
                        '/backend/yum_info_' + $scope.pkg, {
                            'pkg': $scope.pkg
                        }, {
                            'wait': function (data) {
                                $scope.installMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.installMsg = data.msg;
                                $scope.pkgs = data.data;
                                $scope.showVerList = true;
                            },
                            'error': function (data) {
                                $scope.installMsg = data.msg;
                                Timeout(function () {
                                    $scope.installing = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };

                // install specified version of pkg in specified repository
                $scope.install = function (repo, name, version, release) {
                    $scope.installMsg = '开始安装...';
                    $scope.showVerList = false;
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_install',
                        '/backend/yum_install_' + repo + '_' + name + '_' + version + '_' + release, {
                            'repo': repo,
                            'pkg': name,
                            'version': version,
                            'release': release
                        }, {
                            'wait': function (data) {
                                $scope.installMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.installMsg = data.msg;
                                $scope.$parent.activeTabName = 'base';
                                Timeout(function () {
                                    $scope.installing = false;
                                    $scope.$parent.checkInstalled();
                                }, 3000, $rootScope.module);
                            },
                            'error': function (data) {
                                $scope.installMsg = data.msg;
                                Timeout(function () {
                                    $scope.installing = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };

                // uninstall specified version of pkg in specified repository
                $scope.uninstall = function (repo, name, version, release) {
                    $scope.installMsg = '正在清理...';
                    $scope.showVerList = false;
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_uninstall',
                        '/backend/yum_uninstall_' + name + '_' + version + '_' + release, {
                            'repo': repo,
                            'pkg': name,
                            'version': version,
                            'release': release
                        }, {
                            'wait': function (data) {
                                $scope.installMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.installMsg = data.msg;
                                Timeout(function () {
                                    $scope.installing = false;
                                    $scope.$parent.checkInstalled();
                                }, 3000, $rootScope.module);
                            },
                            'error': function (data) {
                                $scope.installMsg = data.msg;
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
            templateUrl: template_path + '/partials/directives/srvupdate.html',
            controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Backend', function ($rootScope, $scope, Request, Timeout, Backend) {
                $scope.$scope = $scope.$parent;

                $scope.updating = false;
                $scope.updateMsg = '';

                // check pkg version
                $scope.startUpdate = function () {
                    $scope.updating = true;
                    $scope.updateMsg = '正在检测当前版本信息...';
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_info',
                        '/backend/yum_info_' + $scope.pkg, {
                            'pkg': $scope.pkg,
                            'repo': 'installed'
                        }, {
                            'wait': function (data) {
                                $scope.updateMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.updateMsg = data.msg;
                                $scope.pkginfo = data.data[0];
                                $scope.checkVersion($scope.pkginfo.name);
                            },
                            'error': function (data) {
                                $scope.updateMsg = data.msg;
                                Timeout(function () {
                                    $scope.updating = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };

                // check and list versions of the pkg
                $scope.showVerList = false;
                $scope.checkVersion = function (name) {
                    $scope.updateMsg = '正在检测新版本...';
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_info',
                        '/backend/yum_info_' + name, {
                            'pkg': name,
                            'option': 'update'
                        }, {
                            'wait': function (data) {
                                $scope.updateMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.updateMsg = data.msg;
                                $scope.pkgs = data.data;
                                $scope.showVerList = true;
                            },
                            'error': function (data) {
                                $scope.updateMsg = data.msg;
                                Timeout(function () {
                                    $scope.updating = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };

                // update pkg
                $scope.update = function (repo, name, version, release) {
                    $scope.updateMsg = '开始升级...';
                    $scope.showVerList = false;
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_update',
                        '/backend/yum_update_' + repo + '_' + name + '_' + version + '_' + release, {
                            'repo': repo,
                            'pkg': name,
                            'version': version,
                            'release': release
                        }, {
                            'wait': function (data) {
                                $scope.updateMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.updateMsg = data.msg;
                                $scope.$parent.activeTabName = 'base';
                                Timeout(function () {
                                    $scope.updating = false;
                                    $scope.$parent.checkInstalled();
                                }, 3000, $rootScope.module);
                            },
                            'error': function (data) {
                                $scope.updateMsg = data.msg;
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
            templateUrl: template_path + '/partials/directives/srvext.html',
            controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Backend', function ($rootScope, $scope, Request, Timeout, Backend) {
                $scope.$scope = $scope.$parent;

                $scope.operating = false;
                $scope.showMsg = '';

                $scope.start = function () {
                    $scope.operating = true;
                    $scope.showMsg = '正在检测版本信息...';
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_info',
                        '/backend/yum_info_' + $scope.pkg, {
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
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_ext_info',
                        '/backend/yum_ext_info_' + $scope.pkginfo.name, {
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
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_install',
                        '/backend/yum_install_' + repo + '_' + $scope.pkginfo.name + '_' + name + '_' + version + '_' + release, {
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
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_uninstall',
                        '/backend/yum_uninstall_' + $scope.pkginfo.name + '_' + name + '_' + version + '_' + release, {
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
            templateUrl: template_path + '/partials/directives/srvuninstall.html',
            controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Backend', function ($rootScope, $scope, Request, Timeout, Backend) {
                $scope.$scope = $scope.$parent;

                $scope.uninstalling = false;
                $scope.uninstallMsg = '';

                // check pkg version
                $scope.startUninstall = function () {
                    $scope.uninstallMsg = '开始卸载...';
                    $scope.uninstalling = true;
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_info',
                        '/backend/yum_info_' + $scope.pkg, {
                            'pkg': $scope.pkg,
                            'repo': 'installed'
                        }, {
                            'wait': function (data) {
                                $scope.uninstallMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.uninstallMsg = data.msg;
                                $scope.pkginfo = data.data[0];
                                $scope.showVersion = true;
                            },
                            'error': function (data) {
                                $scope.uninstallMsg = data.msg;
                                Timeout(function () {
                                    $scope.uninstalling = false;
                                }, 3000, $rootScope.module);
                            }
                        },
                        true
                    );
                };

                // uninstall specified version of pkg in specified repository
                $scope.uninstall = function (repo, name, version, release) {
                    $scope.uninstallMsg = '正在卸载...';
                    $scope.showVersion = false;
                    Backend.call(
                        $scope.$parent,
                        $rootScope.module,
                        '/backend/yum_uninstall',
                        '/backend/yum_uninstall_' + name + '_' + version + '_' + release, {
                            'repo': repo,
                            'pkg': name,
                            'version': version,
                            'release': release
                        }, {
                            'wait': function (data) {
                                $scope.uninstallMsg = data.msg;
                            },
                            'success': function (data) {
                                $scope.uninstallMsg = data.msg;
                                Timeout(function () {
                                    $scope.uninstalling = false;
                                    $scope.$parent.checkInstalled();
                                }, 3000, $rootScope.module);
                            },
                            'error': function (data) {
                                $scope.uninstallMsg = data.msg;
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
            templateUrl: template_path + '/partials/directives/srvfile.html',
            controller: ['$scope', function ($scope) { }]
        };
    }).
    directive('srvlog', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/directives/srvlog.html',
            controller: ['$scope', function ($scope) { }]
        };
    }).
    directive('selector', function () {
        return {
            restrict: 'A',
            transclude: true,
            scope: {},
            replace: true,
            templateUrl: template_path + '/partials/directives/selector.html',
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
                    Request.post('/operation/file', {
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