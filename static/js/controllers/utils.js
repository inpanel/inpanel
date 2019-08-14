var UtilsCtrl = ['$scope', 'Module', 'Request',
    function($scope, Module, Request) {
        var module = 'utils';
        Module.init(module, '系统工具');
        $scope.loaded = true;

        $scope.rebootconfirm = function() {
            $('#rebootconfirm').modal();
        };
        $scope.reboot = function() {
            Request.post('/operation/reboot');
        };
    }
];

var UtilsUserCtrl = [
    '$scope', '$routeParams', 'Module', 'Timeout', 'Request',
    function($scope, $routeParams, Module, Timeout, Request) {
        var module = 'utils.user';
        var section = Module.getSection();
        var enabled_sections = ['user', 'group'];
        Module.init(module, '用户管理');
        Module.initSection(enabled_sections[0]);
        $scope.loaded = true;

        $scope.tab_sec = function (section) {
            // var init = Module.getSection() != section
            section = (section && enabled_sections.indexOf(section) > -1) ? section : enabled_sections[0];
            $scope.sec(section);
            Module.setSection(section);
            // $scope['load_' + section](init);
        };
        $scope.loadUsers = function() {
            Request.post('/operation/user', {
                'action': 'listuser'
            }, function(data) {
                if (data.code == 0) {
                    $scope.users = data.data;
                }
            }, false, true);
        };
        $scope.loadGroups = function() {
            Request.post('/operation/user', {
                'action': 'listgroup'
            }, function(data) {
                if (data.code == 0) {
                    $scope.groups = data.data;
                }
            }, false, true);
        };
        $scope.useraddconfirm = function() {
            $scope.curuser = {
                'pw_name': '',
                'pw_gecos': '',
                'pw_gname': '',
                'pw_shell': '/bin/bash',
                'pw_passwd': '',
                'pw_passwdc': '',
                'createhome': true,
                'lock': false
            };
            $('#useraddconfirm').modal();
        };
        $scope.useradd = function() {
            var userdata = $scope.curuser;
            userdata['action'] = 'useradd';
            Request.post('/operation/user', userdata, function(data) {
                if (data.code == 0) {
                    $scope.loadUsers();
                    $scope.loadGroups();
                }
            });
        };
        $scope.usermodconfirm = function(i) {
            var curuser = $scope.users[i];
            $scope.curuser = {
                'pw_name': curuser.pw_name,
                'pw_gecos': curuser.pw_gecos,
                'pw_gname': curuser.pw_gname,
                'pw_dir': curuser.pw_dir,
                'pw_shell': curuser.pw_shell,
                'pw_passwd': '',
                'pw_passwdc': '',
                'lock': curuser.lock
            };
            $('#usermodconfirm').modal();
        };
        $scope.usermod = function() {
            var userdata = $scope.curuser;
            userdata['action'] = 'usermod';
            Request.post('/operation/user', userdata, function(data) {
                if (data.code == 0) {
                    $scope.loadUsers();
                    $scope.loadGroups();
                }
            });
        };
        $scope.userdelconfirm = function(i) {
            var curuser = $scope.users[i];
            $scope.curuser = {
                'pw_name': curuser.pw_name
            };
            $('#userdelconfirm').modal();
        };
        $scope.userdel = function() {
            Request.post('/operation/user', {
                'action': 'userdel',
                'pw_name': $scope.curuser['pw_name']
            }, function(data) {
                if (data.code == 0) {
                    $scope.loadUsers();
                    $scope.loadGroups();
                }
            });
        };
        $scope.groupaddconfirm = function() {
            $scope.curgrp_name = '';
            $('#groupaddconfirm').modal();
        };
        $scope.groupadd = function() {
            Request.post('/operation/user', {
                'action': 'groupadd',
                'gr_name': $scope.curgrp_name
            }, function(data) {
                if (data.code == 0) {
                    $scope.loadGroups();
                }
            });
        };
        $scope.groupmodconfirm = function(i) {
            $scope.curgrp_newname = $scope.curgrp_name = $scope.groups[i].gr_name;
            $('#groupmodconfirm').modal();
        };
        $scope.groupmod = function() {
            Request.post('/operation/user', {
                'action': 'groupmod',
                'gr_name': $scope.curgrp_name,
                'gr_newname': $scope.curgrp_newname
            }, function(data) {
                if (data.code == 0) {
                    $scope.loadGroups();
                }
            });
        };
        $scope.groupdelconfirm = function(i) {
            $scope.curgrp_name = $scope.groups[i].gr_name;
            $('#groupdelconfirm').modal();
        };
        $scope.groupdel = function() {
            Request.post('/operation/user', {
                'action': 'groupdel',
                'gr_name': $scope.curgrp_name
            }, function(data) {
                if (data.code == 0) {
                    $scope.loadGroups();
                }
            });
        };
        $scope.groupmemsaddconfirm = function(i) {
            $scope.curgrp_name = $scope.groups[i].gr_name;
            $scope.curgrp_mem = '';
            $('#groupmemsaddconfirm').modal();
        };
        $scope.groupmemsadd = function() {
            Request.post('/operation/user', {
                'action': 'groupmems_add',
                'gr_name': $scope.curgrp_name,
                'mem': $scope.curgrp_mem
            }, function(data) {
                if (data.code == 0) {
                    $scope.loadUsers();
                    $scope.loadGroups();
                }
            });
        };
        $scope.groupmemsdelconfirm = function(i) {
            $scope.curgrp_name = $scope.groups[i].gr_name;
            $scope.curgrp_mems = $scope.groups[i].gr_mem;
            $scope.curgrp_mem = '';
            $('#groupmemsdelconfirm').modal();
        };
        $scope.groupmemsdel = function() {
            Request.post('/operation/user', {
                'action': 'groupmems_del',
                'gr_name': $scope.curgrp_name,
                'mem': $scope.curgrp_mem
            }, function(data) {
                if (data.code == 0) {
                    $scope.loadUsers();
                    $scope.loadGroups();
                }
            });
        };
    }
];

var UtilsProcessCtrl = [
    '$scope', '$routeParams', 'Module', 'Timeout', 'Request',
    function ($scope, $routeParams, Module, Timeout, Request) {
        var module = 'utils.process';
        var section = Module.getSection();
        var enabled_sections = ['list', 'other'];
        Module.init(module, '进程管理');
        Module.initSection(enabled_sections[0]);
        $scope.loaded = false;
        $scope.init_process = true;
        $scope.delete_process = '';
        $scope.time_interval = 1000;
        $scope.auto_refresh = false;
        $scope.process = {
            process: [],
            total: 0
        };
        $scope.current_process = {};
        $scope.current_process_loaded = {'info': false, 'status': false, 'file': false, 'io': false, 'memory': false, 'network': false}

        $scope.load = function () {
            $scope.loaded = true;
            $scope.tab_sec(section);
        };

        $scope.tab_sec = function (section) {
            var init = Module.getSection() != section
            section = (section && enabled_sections.indexOf(section) > -1) ? section : enabled_sections[0];
            $scope.sec(section);
            Module.setSection(section);
            $scope['load_' + section](init);
        };

        var getProcess = function() {
            Request.get('/utils/process/list', function (res) {
                if (res && res.code == 0) {
                    $scope.process.process = res.data;
                    $scope.process.total = res.data.length;
                }
                if (!$scope.loaded) {
                    $scope.loaded = true;
                }
                if ($scope.init_process) {
                    $scope.init_process = false;
                }
                if (Module.getSection() == 'list' && $scope.auto_refresh) {
                    Timeout(getProcess, $scope.time_interval, module);
                }
            });
        };
        $scope.load_list = function (init) {
            if (!init && !$scope.init_process) {
                return; // Prevent duplicate requests
            }
            getProcess();
        };
        $scope.load_other = function (init) {
            console.log('待开发功能', init)
        }
        $scope.processkillconfirm = function(i) {
            $scope.delete_process = i || '';
            $('#processkillconfirm').modal();
        };
        $scope.processkill = function () {
            if ($scope.delete_process && $scope.delete_process['pid']) {
                Request.post('/utils/process/kill/' + $scope.delete_process['pid'], null, function () {
                    $scope.delete_process = '';
                    $scope.refresh();
                });
            }
        };
        $scope.process_detail = function (p) {
            if (p && p['pid']) {
                $('#process_detail_dialog').modal();
                $scope.current_process.name = p['name'];
                $scope.current_process.pid = p['pid'];
                $scope.load_detial(p['pid']);
            }
        };
        $scope.load_detial = function (pid) {
            if (pid) {
                $scope.current_process_loaded = {'info': false, 'status': false, 'file': false, 'io': false, 'memory': false, 'network': false}
                Request.get('/utils/process/info/' + pid, function (res) {
                    $scope.current_process_loaded.info = true;
                    if (res && res.code == 0) {
                        $scope.current_process.info = res.data;
                    }
                });
                Request.get('/utils/process/status/' + pid, function (res) {
                    $scope.current_process_loaded.status = true;
                    if (res && res.code == 0) {
                        $scope.current_process.status = res.data;
                    }
                });
                Request.get('/utils/process/file/' + pid, function (res) {
                    $scope.current_process_loaded.file = true;
                    if (res && res.code == 0) {
                        $scope.current_process.file = res.data;
                    }
                });
                Request.get('/utils/process/io/' + pid, function (res) {
                    $scope.current_process_loaded.io = true;
                    if (res && res.code == 0) {
                        $scope.current_process.io = res.data;
                    }
                });
                Request.get('/utils/process/memory/' + pid, function (res) {
                    $scope.current_process_loaded.memory = true;
                    if (res && res.code == 0) {
                        $scope.current_process.memory = res.data;
                    }
                });
                Request.get('/utils/process/network/' + pid, function (res) {
                    $scope.current_process_loaded.network = true;
                    if (res && res.code == 0) {
                        $scope.current_process.network = res.data;
                    }
                });
            }
        };
        $scope.process_detail_close = function () {
            Timeout(function() {
                $scope.current_process = {};
            }, 600, module);
        }
        $scope.refresh = function () {
            console.log('刷新列表');
            getProcess();
        };
        $scope.auto_refresh_open = function () {
            console.log('打开自动刷新');
            $scope.auto_refresh = true;
            getProcess();
        };
        $scope.auto_refresh_close = function () {
            console.log('关闭自动刷新');
            $scope.auto_refresh = false;
        };
    }
]

var UtilsNetworkCtrl = [
    '$scope', '$routeParams', 'Module', 'Timeout', 'Message', 'Request',
    function($scope, $routeParams, Module, Timeout, Message, Request) {
        var module = 'utils.network';
        Module.init(module, '网络设置');
        Module.initSection('hostname');
        $scope.restartMessage = '是否要重启网络？';
        $scope.loaded = true;
        $scope.showRestartBtn = true;

        $scope.loadHostName = function () {
            Request.get('/utils/network/hostname', function(data) {
                $scope.hostname = data.hostname;
            });
        };
        $scope.saveHostName = function () {
            Request.post('/utils/network/hostname', {
                'hostname': $scope.hostname
            }, function (data) {
                if (data.code == 0) $scope.loadHostName();
            });
        };
        $scope.loadIfNames = function() {
            Request.get('/utils/network/ifnames', function(data) {
                $scope.ifnames = data.ifnames;
                $scope.ifname = $scope.ifnames[0];
                // load the default iface's config
                $scope.loadIfConfig($scope.ifname);
            });
        };
        $scope.loadIfConfig = function(ifname) {
            $scope.ifname = ifname;
            Request.get('/utils/network/ifconfig/' + ifname, function(data) {
                $scope.ip = data['ip'];
                $scope.mask = data['mask'];
                $scope.gw = data['gw'];
            });
        };
        $scope.saveIfConfig = function() {
            Request.post('/utils/network/ifconfig/' + $scope.ifname, {
                'ip': $scope.ip,
                'mask': $scope.mask,
                'gw': $scope.gw
            }, function(data) {
                if (data.code == 0) $scope.loadIfConfig($scope.ifname);
            });
        };
        $scope.loadNameservers = function() {
            Request.get('/utils/network/nameservers', function(data) {
                $scope.nameservers = data['nameservers'];
            });
        };
        $scope.saveNameservers = function() {
            var nameservers = [];
            $('.nameserver').each(function() {
                var ns = $(this).val();
                if (ns) nameservers.push(ns);
            });
            Request.post('/utils/network/nameservers', {
                'nameservers': nameservers.join(',')
            }, function(data) {
                if (data.code == 0) $scope.loadNameservers();
            });
        };
        $scope.addNameserver = function() {
            $scope.nameservers.push('');
        };
        $scope.delNameserver = function(i) {
            $scope.nameservers.splice(i, 1);
        };
        $scope.restart = function() {
            $scope.restartMessage = '正在重启，请稍候...'
            $scope.showRestartBtn = false;
            Timeout(function() {
                Request.post('/backend/service_restart', {
                    service: 'network'
                }, function(data) {
                    var getRestartStatus = function() {
                        Request.get('backend/service_restart_network', function(data) {
                            if (data.msg) $scope.restartMessage = data.msg;
                            if (data.status == 'finish') {
                                Message.setSuccess('');
                                Timeout(function() {
                                    $scope.restartMessage = '是否要重启网络？';
                                    $scope.showRestartBtn = true;
                                }, 3000, module);
                            } else
                                Timeout(getRestartStatus, 500, module);
                        });
                    };
                    Timeout(getRestartStatus, 500, module);
                });
            }, 1000, module);
        };
    }
];

var UtilsTimeCtrl = [
    '$scope', '$routeParams', 'Module', 'Timeout', 'Request', 'Backend',
    function($scope, $routeParams, Module, Timeout, Request, Backend) {
        var module = 'utils.time';
        Module.init(module, '时间设置');
        Module.initSection('datetime');
        $scope.loaded = true;
        $scope.ntpdChecking = true;
        $scope.ntpdStatus = null;

        $scope.loadDatetime = function() {
            Request.get('/utils/time/datetime', function(data) {
                $scope.datetime = data;
                $scope.newDatetime = data.str;
            });
        };
        $scope.saveDatetime = function() {
            Request.post('/backend/datetime', {
                'datetime': $scope.newDatetime
            }, function(data) {
                Request.setProcessing(true);
                var getStatus = function() {
                    Request.get('backend/datetime', function(data) {
                        if (data.status != 'finish') {
                            Request.setProcessing(true);
                            Timeout(getStatus, 500, module);
                        }
                    });
                };
                Timeout(getStatus, 500, module);
            });
        };

        $scope.loadTimezone = function() {
            Request.get('/utils/time/timezone', function(data) {
                var timezone = data.timezone;
                $scope.timezone = timezone ? timezone : '时区不可识别';
                if (timezone) {
                    var tzinfo = timezone.split('/');
                    $scope.timezone_region = tzinfo[0];
                    $scope.timezone_city = tzinfo[1];
                } else {
                    $scope.timezone_region = 'Asia';
                    $scope.timezone_city = 'Shanghai';
                }
            });
        };
        $scope.loadTimezones = function(region, callback) {
            if (region) {
                Request.get('/utils/time/timezone_list/' + region, function(data) {
                    $scope.cities = data.cities;
                    if (callback) callback.call();
                });
            } else {
                Request.get('/utils/time/timezone_list', function(data) {
                    $scope.regions = data.regions;
                    var getcities = function() {
                        Request.get('/utils/time/timezone_list/' + $scope.timezone_region, function(data) {
                            $scope.cities = data.cities;
                        });
                    };
                    if ($scope.timezone_region) getcities();
                    else Timeout(getcities, 500, module);
                });
            }
        };
        $scope.setTimezone = function(region, city) {
            $scope.timezone_region = region;
            $scope.loadTimezones(region, function() {
                $scope.timezone_city = city;
            });
        };
        $scope.saveTimezone = function() {
            var region = $scope.timezone_region;
            var city = $scope.timezone_city;
            Request.post('/utils/time/timezone', {
                'timezone': region + '/' + city
            }, function(data) {
                if (data.code == 0) {
                    $scope.loadTimezone();
                    $scope.loadDatetime();
                }
            });
        };

        $scope.synctime = function() {
            var server = 'pool.ntp.org';
            Request.post('/backend/ntpdate', {
                'server': server
            }, function(data) {
                Request.setProcessing(true);
                var getStatus = function() {
                    Request.get('backend/ntpdate_' + server, function(data) {
                        if (data.status != 'finish') {
                            Request.setProcessing(true);
                            Timeout(getStatus, 500, module);
                        } else {
                            $scope.loadDatetime();
                        }
                    });
                };
                Timeout(getStatus, 500, module);
            });
        };

        var installInit = function() {
            $scope.installMessage = '时间同步需要使用 NTP 服务，您当前尚未安装该服务。<br>是否安装 ？';
            $scope.showInstallBtn = true;
        };
        var startInit = function() {
            $scope.startMessage = 'NTP 服务已安装但还未启动。是否启动同步 ？';
            $scope.showStartBtn = true;
        };
        var stopInit = function() {
            $scope.stopMessage = 'NTP 服务正在运行，系统时间会一直保持同步。是否停止同步 ？';
            $scope.showStopBtn = true;
        };
        installInit();
        startInit();
        stopInit();

        $scope.loadSync = function() {
            Request.get('/query/service.ntpd', function(data) {
                if (data['service.ntpd']) {
                    $scope.ntpdStatus = data['service.ntpd']['status'];
                }
                $scope.ntpdChecking = false;
            });
        };
        $scope.ntp_install = function() {
            $scope.installMessage = '正在安装，请稍候...'
            $scope.showInstallBtn = false;
            Backend.call(
                $scope,
                module,
                '/backend/yum_install',
                '/backend/yum_install_base_ntp', {
                    'repo': 'base',
                    'pkg': 'ntp'
                }, {
                    'wait': function(data) {
                        $scope.installMessage = data.msg;
                    },
                    'success': function(data) {
                        $scope.installMessage = data.msg;
                        Timeout($scope.loadSync, 3000, module);
                    },
                    'error': function(data) {
                        $scope.installMessage = data.msg;
                        Timeout($scope.loadSync, 3000, module);
                    }
                },
                true
            );
        };
        $scope.ntp_start = function() {
            $scope.startMessage = '正在启动，请稍候...'
            $scope.showStartBtn = false;
            Backend.call(
                $scope,
                module,
                '/backend/service_start',
                '/backend/service_start_ntpd', {
                    name: 'NTP',
                    service: 'ntpd'
                }, {
                    'wait': function(data) {
                        $scope.startMessage = data.msg;
                    },
                    'success': function(data) {
                        $scope.startMessage = data.msg;
                        Timeout(function() {
                            startInit();
                            $scope.loadSync();
                        }, 3000, module);
                    },
                    'error': function(data) {
                        $scope.startMessage = data.msg;
                        Timeout(function() {
                            startInit();
                            $scope.loadSync();
                        }, 3000, module);
                    }
                },
                true
            );
        };
        $scope.ntp_stop = function() {
            $scope.stopMessage = '正在停止，请稍候...'
            $scope.showStopBtn = false;
            Backend.call(
                $scope,
                module,
                '/backend/service_stop',
                '/backend/service_stop_ntpd', {
                    name: 'NTP',
                    service: 'ntpd'
                }, {
                    'wait': function(data) {
                        $scope.stopMessage = data.msg;
                    },
                    'success': function(data) {
                        $scope.stopMessage = data.msg;
                        Timeout(function() {
                            stopInit();
                            $scope.loadSync();
                        }, 3000, module);
                    },
                    'error': function(data) {
                        $scope.stopMessage = data.msg;
                        Timeout(function() {
                            stopInit();
                            $scope.loadSync();
                        }, 3000, module);
                    }
                },
                true
            );
        };
    }
];

var StorageCtrl = [
    '$scope', 'Module', 'Timeout', 'Request', 'Message', 'Backend',
    function($scope, Module, Timeout, Request, Message, Backend) {
        var module = 'utils.storage';
        Module.init(module, '磁盘管理');
        $scope.loaded = false;
        $scope.waiting = true;
        $scope.init_local = true;
        var section = Module.getSection();
        var enabled_sections = ['local', 'remote'];
        Module.initSection(enabled_sections[0]);

        $scope.load = function () {
            $scope.loaded = true;
            $scope.tab_sec(section);
        };

        $scope.tab_sec = function (section) {
            console.log(Module.getSection(), section);
            section = (section && enabled_sections.indexOf(section) > -1) ? section : enabled_sections[0];
            var init = Module.getSection() != section
            $scope.sec(section);
            Module.setSection(section);
            $scope['load_' + section](init);
        };

        $scope.load_local = function(init) {
            if (!init && !$scope.init_local) {
                return; // Prevent duplicate requests
            }
            $scope.get_diskinfo();
        };
        $scope.load_remote = function(init) {
            console.log('加载网络磁盘', init);
        };
        $scope.get_diskinfo = function () {
            Request.get('/query/server.diskinfo', function(data) {
                if (!$scope.loaded) $scope.loaded = true;
                $scope.diskinfo = data['server.diskinfo'];
                $scope.waiting = false;
                if ($scope.init_local) {
                    $scope.init_local = false;
                }
            });
        };
        $scope.swaponconfirm = function(devname) {
            $scope.devname = devname;
            $('#swaponconfirm').modal();
        };
        $scope.swapon = function() {
            Backend.call(
                $scope,
                module,
                '/backend/swapon',
                '/backend/swapon_on_' + $scope.devname, { 'devname': $scope.devname }, { 'success': $scope.get_diskinfo }
            );
        };
        $scope.swapoffconfirm = function(devname) {
            $scope.devname = devname;
            $('#swapoffconfirm').modal();
        };
        $scope.swapoff = function() {
            Backend.call(
                $scope,
                module,
                '/backend/swapoff',
                '/backend/swapon_off_' + $scope.devname, { 'devname': $scope.devname }, { 'success': $scope.get_diskinfo }
            );
        };
        $scope.umountconfirm = function(devname) {
            $scope.devname = devname;
            $('#umountconfirm').modal();
        };
        $scope.umount = function() {
            Backend.call(
                $scope,
                module,
                '/backend/umount',
                '/backend/mount_umount_' + $scope.devname, { 'devname': $scope.devname }, { 'success': $scope.get_diskinfo }
            );
        };
        $scope.mountconfirm = function(devname, fstype) {
            $scope.devname = devname;
            $scope.mountpoint = '';
            $scope.fstype = fstype;
            Request.get('/query/config.fstab(' + devname + ')', function(data) {
                if (data['config.fstab'] && typeof(data['config.fstab']['mount']) != 'undefined') {
                    $scope.mountpoint = data['config.fstab']['mount'];
                }
            });
            $('#mountconfirm').modal();
        };
        $scope.selectmountpoint = function(i) {
            $scope.selector_title = '请选择挂载点';
            $scope.selector.onlydir = true;
            $scope.selector.onlyfile = false;
            $scope.selector.load($scope.mountpoint ? $scope.mountpoint : '/');
            $scope.selector.selecthandler = function(path) {
                $('#selector').modal('hide');
                $scope.mountpoint = path;
            };
            $('#selector').modal();
        };
        $scope.mount = function() {
            Backend.call(
                $scope,
                module,
                '/backend/mount',
                '/backend/mount_mount_' + $scope.devname, {
                    'devname': $scope.devname,
                    'mountpoint': $scope.mountpoint,
                    'fstype': $scope.fstype
                }, { 'success': $scope.get_diskinfo }
            );
        };
        $scope.formatconfirm = function(devname) {
            $scope.devname = devname;
            Request.get('/query/tool.supportfs', function(data) {
                $scope.supportfs = data['tool.supportfs'];
            });
            $('#formatconfirm').modal();
        };
        $scope.format = function() {
            Backend.call(
                $scope,
                module,
                '/backend/format',
                '/backend/format_' + $scope.devname, {
                    'devname': $scope.devname,
                    'fstype': $scope.fstype
                }, { 'success': $scope.get_diskinfo }
            );
        };
        $scope.addpartconfirm = function(devname, unpartition) {
            $scope.devname = devname;
            $scope.unpartition = unpartition;
            $('#addpartconfirm').modal();
        };
        $scope.addpart = function() {
            $scope.waiting = true;
            Message.setInfo('正在 ' + $scope.devname + ' 上创建分区，请稍候...', true);
            Request.post('/operation/fdisk', {
                'action': 'add',
                'devname': $scope.devname,
                'size': $scope.size,
                'unit': $scope.unit
            }, function(data) {
                if (data.code == 0)
                    $scope.get_diskinfo();
                else
                    $scope.waiting = false;
            });
        };
        $scope.delpartconfirm = function(devname) {
            $scope.devname = devname;
            $('#delpartconfirm').modal();
        };
        $scope.delpart = function() {
            $scope.waiting = true;
            Message.setInfo('正在删除分区 ' + $scope.devname + '，请稍候...', true);
            Request.post('/operation/fdisk', {
                'action': 'delete',
                'devname': $scope.devname
            }, function(data) {
                if (data.code == 0)
                    $scope.get_diskinfo();
                else
                    $scope.waiting = false;
            });
        };
        $scope.scanpartconfirm = function(devname) {
            $scope.devname = devname;
            $('#scanpartconfirm').modal();
        };
        $scope.scanpart = function() {
            $scope.waiting = true;
            Message.setInfo('正在扫描 ' + $scope.devname + ' 的分区，请稍候...', true);
            Request.post('/operation/fdisk', {
                'action': 'scan',
                'devname': $scope.devname
            }, function(data) {
                if (data.code == 0)
                    Timeout($scope.get_diskinfo, 1000, module);
                else
                    $scope.waiting = false;
            });
        };
    }
];

var StorageAutoFMCtrl = [
    '$scope', 'Module', 'Timeout', 'Request', 'Message', 'Backend',
    function($scope, Module, Timeout, Request, Message, Backend) {
        var module = 'utils.autofm';
        Module.init(module, '自动格式化挂载');
        $scope.loaded = false;
        $scope.waiting = true;
        $scope.diskcount = 0;

        $scope.loadDiskinfo = function() {
            Request.get('/query/server.diskinfo', function(data) {
                if (!$scope.loaded) $scope.loaded = true;
                $scope.diskinfo = data['server.diskinfo'];
                $scope.waiting = false;
                $scope.diskcount = 0;
                for (var i in data['server.diskinfo']['partitions']) {
                    var p = data['server.diskinfo']['partitions'][i];
                    if (p.is_hw && !p.is_pv && p.partcount == 0 && !p.mount) {
                        $scope.diskcount++;
                    }
                }
            });
        };
        $scope.confirm = function(devname) {
            $scope.devname = devname;
            $scope.mountpoint = '';
            $scope.fstype = '';
            // check mount points under /data/
            Request.post('/operation/file', {
                'action': 'listdir',
                'path': '/data',
                'showhidden': true,
                'remember': false
            }, function(data) {
                if (data.code == 0) {
                    var items = data.data;
                    if (items.length == 0) {
                        $scope.mountpoint = '/data/0';
                    } else {
                        var names = {};
                        for (var i = 0; i < items.length; i++) {
                            names[items[i].name] = true;
                        }
                        var diski = 0;
                        while (1) {
                            if (!names['' + diski]) break;
                            diski++;
                        }
                        $scope.mountpoint = '/data/' + diski;
                    }
                } else {
                    // /data not exists, create it
                    Request.post('/operation/file', {
                        'action': 'createfolder',
                        'path': '/',
                        'name': 'data'
                    });
                    $scope.mountpoint = '/data/0';
                }
            }, false, true);
            Request.get('/query/tool.supportfs', function(data) {
                var fs = data['tool.supportfs'];
                for (var i = 0; i < fs.length; i++) {
                    if (fs[i] == 'swap') fs.splice(i, 1);
                    if (fs[i] == 'xfs') $scope.fstype = 'xfs';
                    else if (fs[i] == 'ext4') $scope.fstype = 'ext4';
                    else if (fs[i] == 'ext3') $scope.fstype = 'ext3';
                }
                $scope.supportfs = fs;
            });
            $('#confirm').modal();
        };
        $scope.selectmountpoint = function(i) {
            $scope.selector_title = '请选择挂载点';
            $scope.selector.onlydir = true;
            $scope.selector.onlyfile = false;
            $scope.selector.load($scope.mountpoint);
            $scope.selector.selecthandler = function(path) {
                $('#selector').modal('hide');
                $scope.mountpoint = path;
            };
            $('#selector').modal();
        };
        $scope.autofm = function() {
            // check the mount point
            Request.post('/operation/file', {
                'action': 'listdir',
                'path': $scope.mountpoint,
                'showhidden': true,
                'remember': false
            }, function(data) {
                if (data.code == 0) {
                    var items = data.data;
                    if (items.length > 0) {
                        var mount_detect = false;
                        for (var i = 0; i < items.length; i++) {
                            if (items[i].name == 'lost+found') {
                                mount_detect = true;
                                break;
                            }
                        }
                        if (mount_detect)
                            Message.setError('已有其它设备挂载在 ' + $scope.mountpoint + ' 下，请重新选择挂载点。');
                        else
                            Message.setError('挂载点 ' + $scope.mountpoint + ' 下存在文件或目录，无法挂载！请重新选择挂载点。');
                    } else {
                        $scope.format();
                    }
                } else {
                    // mountpoint not exists, create it
                    var p = $scope.mountpoint.split('/');
                    var name = p.pop();
                    var path = p.join('/');
                    Request.post('/operation/file', {
                        'action': 'createfolder',
                        'path': path,
                        'name': name
                    }, $scope.format);
                }
            }, false, true);
        };
        $scope.mount = function() {
            Backend.call(
                $scope,
                module,
                '/backend/mount',
                '/backend/mount_mount_' + $scope.devname, {
                    'devname': $scope.devname,
                    'mountpoint': $scope.mountpoint,
                    'fstype': $scope.fstype
                }, { 'success': $scope.loadDiskinfo }
            );
        };
        $scope.format = function() {
            Backend.call(
                $scope,
                module,
                '/backend/format',
                '/backend/format_' + $scope.devname, {
                    'devname': $scope.devname,
                    'fstype': $scope.fstype
                }, { 'success': $scope.mount }
            );
        };
    }
];

var StorageMoveDataCtrl = [
    '$scope', 'Module', 'Timeout', 'Request', 'Message', 'Backend',
    function($scope, Module, Timeout, Request, Message, Backend) {
        var module = 'utils.movedata';
        Module.init(module, '数据移至数据盘');
        $scope.loaded = false;
        $scope.waiting = true;
        $scope.srcpath = '/var';
        $scope.despath = '/';
        $scope.mountpoint = '/';

        $scope.loadMounts = function() {
            Request.get('/query/server.mounts', function(data) {
                if (!$scope.loaded) $scope.loaded = true;
                $scope.mounts = data['server.mounts'];
                $scope.waiting = false;
            });
        };
        $scope.setdespath = function(value) {
            $scope.despath = value;
        };
        $scope.selectsrcpath = function(i) {
            $scope.selector_title = '请选择要迁移的目录（原始目录）';
            $scope.selector.onlydir = true;
            $scope.selector.onlyfile = false;
            $scope.selector.load($scope.srcpath);
            $scope.selector.selecthandler = function(path) {
                $('#selector').modal('hide');
                $scope.srcpath = path;
            };
            $('#selector').modal();
        };
        $scope.selectdespath = function(i) {
            $scope.selector_title = '请选择要迁移到的目录（目标目录）';
            $scope.selector.onlydir = true;
            $scope.selector.onlyfile = false;
            $scope.selector.load($scope.despath);
            $scope.selector.selecthandler = function(path) {
                $('#selector').modal('hide');
                $scope.despath = path;
            };
            $('#selector').modal();
        };
        $scope.movedata = function() {
            $scope.waiting = true;
            var srcpath = $scope.srcpath.replace(/\/$/, '');
            var srcname = srcpath.split('/').pop();
            var despath = $scope.despath.replace(/\/$/, '') + '/' + srcname;
            if (despath == srcpath) {
                Message.setError('路径没有改变，无须迁移！');
                $scope.waiting = false;
                return;
            }
            // check the srcpath
            Message.setInfo('正在检测，请稍候...', true);
            Request.post('/operation/file', {
                'action': 'getitem',
                'path': srcpath
            }, function(data) {
                if (data.code == 0) {
                    // check if dir or link
                    if (!data.data.isdir) {
                        Message.setError($scope.srcpath + ' 不是有效的目录！（可能是文件或链接）');
                        $scope.waiting = false;
                        return;
                    }
                    // check the despath
                    Request.post('/operation/file', {
                        'action': 'getitem',
                        'path': despath
                    }, function(data) {
                        if (data.code == 0) {
                            Message.setError('目标目录下已有同名文件或目录 ' + despath + '，迁移失败！');
                            $scope.waiting = false;
                        } else {
                            // moving
                            Backend.call(
                                $scope,
                                module,
                                '/backend/move',
                                '/backend/move_' + srcpath + '_' + despath, {
                                    'srcpath': srcpath,
                                    'despath': despath
                                }, {
                                    'success': function(data) {
                                        Message.setInfo('正在原始目录创建链接...');
                                        Request.post('/operation/file', {
                                            'action': 'link',
                                            'srcpath': despath,
                                            'despath': srcpath
                                        }, function(data) {
                                            if (data.code == 0) {
                                                Message.setSuccess('迁移完成！');
                                            } else {
                                                Message.setError('迁移失败！' + data.msg);
                                            }
                                            $scope.waiting = false;
                                        }, false, true);
                                    },
                                    'error': function(data) {
                                        Message.setError('迁移过程中发生错误，迁移失败！');
                                        $scope.waiting = false;
                                    }
                                }
                            );
                        }
                    }, false, true);
                }
            });
        };
    }
];

var UtilsSSLCtrl = ['$scope', 'Module', '$routeParams', 'Request', 'Message', 'Backend', 'Timeout',
    function($scope, Module, $routeParams, Request, Message, Backend, Timeout) {
        var module = 'utils.ssl';
        Module.init(module, 'SSL证书管理');
        var section = Module.getSection();
        var enabled_sections = ['keys', 'crts', 'csrs', 'host'];
        Module.initSection(enabled_sections[0]);
        $scope.installed = false;
        $scope.loaded = false;
        $scope.showAlertInfo = true;
        $scope.loading_keys = true;
        $scope.loading_crts = true;
        $scope.loading_csrs = true;
        $scope.loading_host = true;
        $scope.list_keys = [];
        $scope.list_crts = [];
        $scope.list_csrs = [];
        $scope.list_host = [];

        $scope.load = function() {
            $scope.installed = true;
            $scope.loaded = true;
            $scope.tab_sec(section);
        };

        $scope.tab_sec = function (section) {
            section = (section && enabled_sections.indexOf(section) > -1) ? section : enabled_sections[0];
            $scope.sec(section);
            Module.setSection(section);
            $scope['load_' + section]();
        };

        $scope.load_keys = function (callback) {
            $scope.loading_keys = true;
            Request.get('/utils/ssl/keys', function(res) {
                $scope.loading_keys = false;
                if (res.list) {
                    $scope.list_keys = res.list;
                }
                if (callback) {
                    callback.call();
                }
            });
        };
        $scope.load_crts = function (callback) {
            $scope.loading_crts = true;
            Request.get('/utils/ssl/crts', function(res) {
                $scope.loading_crts = false;
                if (res.list) {
                    $scope.list_crts = res.list;
                }
                if (callback) {
                    callback.call();
                }
            });
        };
        $scope.load_csrs = function (callback) {
            $scope.loading_csrs = true;
            Request.get('/utils/ssl/csrs', function(res) {
                $scope.loading_csrs = false;
                if (res.list) {
                    $scope.list_csrs = res.list;
                }
                if (callback) {
                    callback.call();
                }
            });
        };
        $scope.load_host = function (callback) {
            $scope.loading_host = true;
            Request.get('/utils/ssl/host', function(res) {
                $scope.loading_host = false;
                if (res.list) {
                    $scope.list_host = res.list;
                }
                if (callback) {
                    callback.call();
                }
            });
        };
        $scope.add_domain_keys = function (callback) {
            $scope.loading_host = true;
            Request.post('/utils/ssl/keys', {
                'action': 'add_domain_keys'
            }, function(res) {
                // $scope.loading_host = false;
                if (res) {
                    console.log('创建成功')
                }
                if (callback) {
                    callback.call();
                }
            });
        };
        $scope.keys_check = function (keys, callback) {
            console.log('keys_check', keys);
            if (callback) {
                callback.call();
            }
        };
        $scope.keys_delete = function (keys, confirmed, callback) {
            if (confirmed && confirmed == true) {
                console.log('keys_delete', keys);
                if (callback) {
                    callback.call();
                }
            } else {
                $scope.keys_delete_confirm(keys, callback)
            }
        };
        $scope.keys_delete_confirm = function(keys, callback) {
            console.log('keys_delete_confirm', keys);
            $scope.confirm_title = '删除私钥确认';
            $scope.confirm_body = '<p>删除私钥后，可能会导致对应域名 https 请求出问题！<p><p>确认要删除吗？</p>';
            $('#confirm').modal();
            $scope.confirm = function() {
                $scope.keys_delete(keys, true, callback);
            };
        };
        $scope.crts_check = function (crts, callback) {
            console.log('crts_check', crts);
            if (callback) {
                callback.call();
            }
        };
        $scope.crts_renew = function (crts, callback) {
            console.log('crts_renew', crts);
            if (callback) {
                callback.call();
            }
        };
        $scope.crts_revoke = function (crts, confirmed, callback) {
            if (confirmed && confirmed == true) {
                console.log('crts_revoke', crts);
                if (callback) {
                    callback.call();
                }
            } else {
                $scope.crts_revoke_confirm(crts, callback)
            }
        };
        $scope.crts_revoke_confirm = function(crts, callback) {
            console.log('crts_delete_confirm', crts);
            $scope.confirm_title = '吊销证书';
            $scope.confirm_body = '<p>吊销此证书后，会导致对应域名的 HTTPS 请求出问题！<p><p>确定要吊销吗？</p>';
            $('#confirm').modal();
            $scope.confirm = function() {
                $scope.crts_revoke(crts, true, callback);
            };
        };
        $scope.crts_delete = function (crts, confirmed, callback) {
            if (confirmed && confirmed == true) {
                console.log('crts_delete', crts);
                if (callback) {
                    callback.call();
                }
            } else {
                $scope.crts_delete_confirm(crts, callback)
            }
        };
        $scope.crts_delete_confirm = function(crts, callback) {
            console.log('crts_delete_confirm', crts);
            $scope.confirm_title = '删除证书';
            $scope.confirm_body = '<p>删除证书后，会导致对应域名的 HTTPS 请求出问题！<p><p>确定要删除吗？</p>';
            $('#confirm').modal();
            $scope.confirm = function() {
                $scope.crts_delete(crts, true, callback);
            };
        };
    }
];

var StorageRemoteCtrl = [
    '$scope', 'Module', '$routeParams', 'Timeout', 'Request', 'Message', 'Backend', '$location',
    function($scope, Module, $routeParams,Timeout, Request, Message, Backend, $location) {
        var module = 'utils.remote';
        Module.init(module, '网络磁盘');
        $scope.loaded = false;
        $scope.loading_info = true;
        $scope.action = '';
        $scope.protocol = 'ftp';
        $scope.storage_info = {
            'name': '',
            'address': '',
            'account': '',
            'password': '',
            'protocol': ''
        };
        $scope.checking_davfs2 = true;
        $scope.status_davfs2 = null;
        console.log('action', $routeParams.action)
        if ($routeParams.section && $routeParams.section.indexOf('edit_') == 0) {
            $scope.action = 'edit';
        } else {
            $scope.action = 'new';
            $scope.loading_info = false;
        }
        $scope.load = function () {
            $scope.loaded = true;
            if ($scope.action == 'edit') {
                $scope.load_info();
            }
        };
        $scope.load_info = function () {
            var tmp = $routeParams.section.split('_');
            // console.log(tmp);
            $scope.protocol = tmp[1];
            Timeout(function() {
                $scope.loading_info = false;
                // $scope.storage_info['name'] = '坚果云测试用';
            }, 600, module);
        };
        $scope.storage_add = function () {
            if ($scope.protocol == 'webdav') {
                console.log('storage_add/webdav');
                // if (!$scope.status_davfs2) {
                //     $scope.loadDavfs2($scope.storage_add);
                //     return;
                // }
                if (!$scope.protocol || !$scope.storage_info['address']) {
                    return;
                }
                var data = {
                    'name': $scope.storage_info['name'],
                    'address': $scope.storage_info['address'],
                    'account': $scope.storage_info['account'],
                    'password': $scope.storage_info['password'],
                    'protocol': $scope.protocol,
                };
                console.log('提交数据', data);
                Timeout(function() {
                    $scope.loading_info = false;
                    // $scope.storage_info['name'] = '_test';
                    $location.path('/storage/remote/edit_' + encodeURIComponent(data.protocol + '_' + data.address));
                }, 600, module);
            }
        };
        $scope.storage_update = function () {
            console.log('保存');
        };

        $scope.loadDavfs2 = function(callback) {
            Request.get('/query/service.davfs2', function(data) {
                $scope.checking_davfs2 = false;
                if (data['service.davfs2']) {
                    $scope.status_davfs2 = data['service.davfs2']['status'];
                    if (callback) {
                        callback();
                    };
                } else {
                    $scope.installMessage = 'WebDAV 需要使用 davfs2 服务，您当前尚未安装该服务。<br>是否安装 ？';
                    $scope.showInstallBtn = true;
                }
            });
        };
        $scope.install_davfs2 = function() {
            $scope.installMessage = '正在安装支持，请稍候...'
            $scope.showInstallBtn = false;
            Backend.call(
                $scope,
                module,
                '/backend/yum_install',
                '/backend/yum_install_epel_davfs2', {
                    'repo': 'epel',
                    'pkg': 'davfs2'
                }, {
                    'wait': function(data) {
                        $scope.installMessage = data.msg;
                    },
                    'success': function(data) {
                        $scope.installMessage = data.msg;
                        Timeout($scope.loadDavfs2, 3000, module);
                    },
                    'error': function(data) {
                        $scope.installMessage = data.msg;
                        Timeout($scope.loadDavfs2, 3000, module);
                    }
                },
                true
            );
        };
        $scope.start_davfs2 = function() {
            $scope.startMessage = '正在启动，请稍候...'
            $scope.showStartBtn = false;
            Backend.call(
                $scope,
                module,
                '/backend/service_start',
                '/backend/service_start_davfs2', {
                    name: 'Davfs2',
                    service: 'davfs2'
                }, {
                    'wait': function(data) {
                        $scope.startMessage = data.msg;
                    },
                    'success': function(data) {
                        $scope.startMessage = data.msg;
                        Timeout(function() {
                            // startInit();
                            $scope.loadDavfs2();
                        }, 3000, module);
                    },
                    'error': function(data) {
                        $scope.startMessage = data.msg;
                        Timeout(function() {
                            // startInit();
                            $scope.loadDavfs2();
                        }, 3000, module);
                    }
                },
                true
            );
        };

    }
];

var UtilsRepositoryCtrl = [
    '$scope', 'Module', '$routeParams', 'Timeout', 'Request', 'Message', 'Backend', '$location',
    function($scope, Module, $routeParams, Timeout, Request, Message, Backend, $location) {
        var module = 'utils.repository';
        Module.init(module, '软件仓库');
        $scope.loaded = false;
        $scope.action = '';
        var section = Module.getSection();
        var enabled_sections = ['yum', 'apt', 'pacman', 'dnf', 'zypper'];
        Module.initSection(enabled_sections[0]);
        $scope.loading = false;

        $scope.load = function () {
            $scope.loaded = true;
            $scope.tab_sec(section);
        };

        $scope.tab_sec = function (section) {
            var init = Module.getSection() != section
            section = (section && enabled_sections.indexOf(section) > -1) ? section : enabled_sections[0];
            $scope.sec(section);
            Module.setSection(section);
            $scope['load_' + section](init);
        };
        $scope.load_yum = function () {
            $scope.loading = true;
            Timeout(function() {
                $scope.loading = false;
            }, 1000, module);
        };
        $scope.load_apt = function () {
            $scope.loading = true;
            Timeout(function() {
                $scope.loading = false;
            }, 1000, module);
        };
        $scope.load_pacman = function () {
            $scope.loading = true;
            Timeout(function() {
                $scope.loading = false;
            }, 1000, module);
        };
        $scope.load_dnf = function () {
            $scope.loading = true;
            Timeout(function() {
                $scope.loading = false;
            }, 1000, module);
        };
        $scope.load_zypper = function () {
            $scope.loading = true;
            Timeout(function() {
                $scope.loading = false;
            }, 1000, module);
        };
    }
];

var UtilsCronCtrl = ['$scope', 'Module', 'Request', 'Timeout',
    function ($scope, Module, Request, Timeout) {
        var module = 'utils.cron';
        Module.init(module, '定时任务');
        var section = Module.getSection();
        var enabled_sections = ['normal', 'system', 'environment', 'local'];
        Module.initSection(enabled_sections[0]);
        $scope.loaded = false;
        $scope.cron_normal = {
            user: 'root',
            list: []
        };
        $scope.cron_system = {
            user: '',
            list: []
        };
        $scope.has_cron_service = false;

        $scope.load = function () {
            Request.get('/query/service.crond', function(data) {
                if (data['service.crond'] && data['service.crond'].status) {
                    $scope.has_cron_service = true;
                }
                $scope.tab_sec(section);
                $scope.loaded = true;
                $scope.load_user();
            });
        };

        $scope.tab_sec = function (section) {
            var init = Module.getSection() != section
            section = (section && enabled_sections.indexOf(section) > -1) ? section : enabled_sections[0];
            $scope.sec(section);
            Module.setSection(section);
            $scope['load_' + section](init);
        };

        $scope.common_options = '';
        $scope.cron_time = {
            minute: '',
            hour: '',
            day: '',
            month: '',
            weekday: ''
        };
        $scope.options = {
            minute: '',
            hour: '',
            day: '',
            month: '',
            weekday: ''
        };

        $scope.task_id = '';
        $scope.task_time = '';
        $scope.task_user = '';
        $scope.task_level = '';
        $scope.task_email = '';
        $scope.task_command = '';

        $scope.first = {
            normal: true,
            system: true,
            environment: true,
            local: true
        };
        $scope.load_normal = function (init) {
            if (init || $scope.first.normal) {
                $scope.load_normal_list();
            }
        };
        $scope.load_system = function (init) {
            if (init || $scope.first.system) {
                $scope.load_system_list();
            }
        };
        $scope.load_environment = function (init) {
            if (init || $scope.first.environment) {
                $scope.load_environment_list();
            }
        };
        $scope.load_local = function (init) {
            if (init || $scope.first.local) {
                $scope.load_local_list();
            }
        };

        $scope.loading = {
            normal: false,
            system: false,
            environment: false,
            local: false
        };
        $scope.load_normal_list = function () {
            if (!$scope.has_cron_service || $scope.loading.normal) return; // Prevent duplicate requests
            $scope.loading.normal = true;
            $scope.first.normal = false;
            Request.post('/operation/cron', {
                'action': 'cron_list',
                'user': $scope.cron_normal.user,
                'level': 'normal'
            }, function (data) {
                $scope.loading.normal = false;
                if (data.code == 0) {
                    $scope.cron_normal.list = data.data;
                }
            }, false, true);
        };
        $scope.load_system_list = function () {
            if (!$scope.has_cron_service || $scope.loading.system) return; // Prevent duplicate requests
            $scope.loading.system = true;
            $scope.first.system = false;
            Request.post('/operation/cron', {
                'action': 'cron_list',
                'user': $scope.cron_system.user,
                'level': 'system',
            }, function (data) {
                $scope.loading.system = false;
                if (data.code == 0) {
                    $scope.cron_system.list = data.data;
                }
            }, false, true);
        };
        $scope.load_environment_list = function () {
            if (!$scope.has_cron_service || $scope.loading.environment) return; // Prevent duplicate requests
            $scope.loading.environment = true;
            $scope.first.environment = false;
            Timeout(function() {
                $scope.loading.environment = false;
            }, 500, module);
            // Request.post('/operation/cron', {'action': 'cron_list'}, function (data) {
            //     $scope.loading.environment = false;
            //     if (data.code == 0) {}
            // }, false, true);
        };
        $scope.load_local_list = function () {
            if (!$scope.has_cron_service || $scope.loading.local) return; // Prevent duplicate requests
            $scope.loading.local = true;
            $scope.first.local = false;
            Timeout(function() {
                $scope.loading.local = false;
            }, 500, module);
            // Request.post('/operation/cron', {'action': 'cron_list'}, function (data) {
            //     $scope.loading.local = false;
            //     if (data.code == 0) {}
            // }, false, true);
        };

        $scope.$watch('cron_time', function (n) {
            $scope.task_time = n.minute + ' ' + n.hour + ' ' + n.day + ' ' + n.month + ' ' + n.weekday;
        }, true);
        $scope.select_common_option = function () {
            var option = $scope.common_options;
            if (option && option != '') {
                var option_array = option.split(' ');

                $scope.cron_time.minute = option_array[0];
                $scope.cron_time.hour = option_array[1];
                $scope.cron_time.day = option_array[2];
                $scope.cron_time.month = option_array[3];
                $scope.cron_time.weekday = option_array[4];

                $scope.options.minute = option_array[0];
                $scope.options.hour = option_array[1];
                $scope.options.day = option_array[2];
                $scope.options.month = option_array[3];
                $scope.options.weekday = option_array[4];
            } else {
                for (var i in $scope.cron_time) {
                    $scope.cron_time[i] = ''
                }
                for (var j in $scope.options) {
                    $scope.options[j] = ''
                }
            }
        };
        $scope.input_single_option = function (type) {
            if (typeof type === 'undefined' || type === '') {
                return;
            };
            $scope.options[type] = $scope.cron_time[type];
        };
        $scope.select_single_option = function (type) {
            if (typeof type === 'undefined' || type === '') {
                return;
            };
            $scope.cron_time[type] = $scope.options[type];
        };

        $scope.load_user = function () {
            Request.post('/operation/user', {
                'action': 'listuser',
                'fullinfo': false
            }, function (data) {
                if (data.code == 0) {
                    $scope.users = data.data;
                }
            }, false, true);
        };
        $scope.add_cron_normal = function() {
            $scope.form_clear();
            $scope.task_user = $scope.cron_normal.user || "";
            $scope.task_level = 'normal';
            $('#cron-add-confirm').modal();
        };
        $scope.add_cron_system = function() {
            $scope.form_clear();
            $scope.task_user = $scope.cron_system.user || "";
            $scope.task_level = 'system';
            $('#cron-add-confirm').modal();
        };
        $scope.add_cron_jobs = function () {
            $('#cron-add-confirm').modal('hide');
            Request.post('/operation/cron', {
                action: 'cron_add',
                minute: $scope.cron_time.minute,
                hour: $scope.cron_time.hour,
                day: $scope.cron_time.day,
                month: $scope.cron_time.month,
                weekday: $scope.cron_time.weekday,
                command: $scope.task_command,
                user: $scope.task_user,
                email: $scope.task_email,
                level: $scope.task_level
            }, function(res) {
                if (res.code == 0) {
                    $('#cron-add-confirm').modal('hide');
                    if ($scope.task_level == 'system') {
                        $scope.load_system_list();
                    } else {
                        $scope.load_normal_list();
                    }
                }
            });
        };
        $scope.form_clear = function () {
            // $scope.cron_time = {
            //     minute: '',
            //     hour: '',
            //     day: '',
            //     month: '',
            //     weekday: '',
            // };
            $scope.common_options = ''
            $scope.select_common_option()
            $scope.task_id = '';
            $scope.task_user = '';
            $scope.task_email = '';
            $scope.task_level = '';
            $scope.task_command = '';
        };
        $scope.cron_detail = function (info, level) {
            $('#cron-add-confirm').modal();
            $scope.form_clear();
            $scope.cron_time = {
                minute: info.minute,
                hour: info.hour,
                day: info.day,
                month: info.month,
                weekday: info.weekday,
            };
            $scope.options = angular.copy($scope.cron_time);
            $scope.task_id = info.id;
            $scope.task_user = info.user;
            $scope.task_email = '';
            $scope.task_level = level;
            $scope.task_command = info.command;
        };
        $scope.update_cron_jobs = function () {
            $('#cron-add-confirm').modal('hide');
            var currlist = $scope.task_level == 'system' && $scope.cron_system.user ? $scope.cron_system.user : '';
            Request.post('/operation/cron', {
                action: 'cron_mod',
                minute: $scope.cron_time.minute,
                hour: $scope.cron_time.hour,
                day: $scope.cron_time.day,
                month: $scope.cron_time.month,
                weekday: $scope.cron_time.weekday,
                command: $scope.task_command,
                cronid: String($scope.task_id),
                user: $scope.task_user,
                level: $scope.task_level,
                email: $scope.task_email,
                currlist: currlist
            }, function(res) {
                if (res.code == 0) {
                    $('#cron-add-confirm').modal('hide');
                    if ($scope.task_level == 'system') {
                        $scope.load_system_list();
                    } else {
                        $scope.load_normal_list();
                    }
                }
            });
        };
        $scope.cron_del_confirm = function(info, level) {
            if (!info || !info.id || !info.user) return;
            $scope.task_id = info.id;
            $scope.task_user = info.user;
            $scope.task_level = level;
            $('#cron-delete-confirm').modal();
        };
        $scope.del_cron_jobs = function () {
            $('#cron-delete-confirm').modal('hide');
            // current user's task on system level
            var currlist = $scope.task_level == 'system' && $scope.cron_system.user ? $scope.cron_system.user : '';
            Request.post('/operation/cron', {
                action: 'cron_del',
                cronid: String($scope.task_id),
                user: $scope.task_user,
                level: $scope.task_level,
                currlist: currlist
            }, function(res) {
                if (res.code == 0) {
                    $('#cron-delete-confirm').modal('hide');
                    if ($scope.task_level == 'system') {
                        $scope.load_system_list();
                    } else {
                        $scope.load_normal_list();
                    }
                }
            });
        };
        $scope.add_environment = function () {
            console.log('add_environment');
        };
        $scope.add_cron_local = function() {
            console.log('add_cron_local');
        };
    }
];

var UtilsShellCtrl = ['$scope', '$routeParams', 'Module', 'Timeout', 'Request',
    function($scope, $routeParams, Module, Timeout, Request) {
        var module = 'utils.shell';
        Module.init(module, 'SHELL 命令');
        var section = Module.getSection();
        var enabled_sections = ['base', 'advance'];
        Module.initSection(enabled_sections[0]);
        $scope.loaded = false;
        $scope.loading = false;
        $scope.base_cmds = [];
        $scope.base_cwd = '/';
        $scope.base_input = '';

        $scope.load = function () {
            $scope.loaded = true;
            $scope.tab_sec(section);
        };
        $scope.tab_sec = function (section) {
            var init = Module.getSection() != section
            section = (section && enabled_sections.indexOf(section) > -1) ? section : enabled_sections[0];
            $scope.sec(section);
            Module.setSection(section);
            // $scope['load_' + section](init);
        };

        $scope.send_base_cmd = function() {
            if ($scope.base_input == '') {
                return;
            }
            $scope.base_cmds.push('# ' + $scope.base_input);
            Request.post('/operation/shell', {
                'action': 'exec_command',
                'cmd': $scope.base_input,
                'cwd': $scope.base_cwd
            }, function (res) {
                $scope.base_input = '';
                if (res.code == 0) {
                    if (res.data) {
                        $scope.base_cmds.push(res.data.data);
                        // for (i in res.data.data) {
                        //     $scope.base_cmds.push(res.data.data[i]);
                        // }
                    }
                }
            });
        };
    }
];

var UtilsTransmissionCtrl = [
    '$scope', '$routeParams', 'Module', 'Message', 'Timeout', 'Request', 'Backend',
    function($scope, $routeParams, Module, Message, Timeout, Request, Backend) {
        var module = 'utils.transmission';
        var section = Module.getSection();
        var enabled_sections = ['ftp', 'nutstore'];
        Module.init(module, '文件传输');
        Module.initSection(enabled_sections[0]);
        $scope.loaded = true;
        $scope.remote = {
            'address': '',
            'account': '',
            'password': '',
            'source': '/',
            'target': ''
        };
        $scope.tab_sec = function (section) {
            var init = Module.getSection() != section
            section = (section && enabled_sections.indexOf(section) > -1) ? section : enabled_sections[0];
            $scope.sec(section);
            Module.setSection(section);
            $scope['load_' + section](init);
        };
        $scope.load_ftp = function () {
            console.log('传输到 FTP');
        };
        $scope.load_nutstore = function () {
            console.log('传输到坚果云');
        };
        $scope.reset_form = function () {
            $scope.remote = {
                'address': 'vhost250.mianbeian.top',
                'account': 'webmaster@US1508482',
                'password': 'IkBrqalDoLX4irQ0',
                'source': '/',
                'target': '/WEB/'
            };
        };
        $scope.select_files = function () {
            $scope.selector_title = '请选择需要传输的文件';
            $scope.selector.onlydir = false;
            $scope.selector.onlyfile = true;
            $scope.selector.load($scope.remote.source); // 加载默认
            $scope.selector.selecthandler = function (path) { // 回调函数
                $('#selector').modal('hide');
                $scope.remote.source = path;
            };
            $('#selector').modal();
        };
        $scope.transmission_ftp = function () {
            console.log('立即传输', $scope.remote);
            if ($scope.remote.address == '') {
                Message.setWarning('请输入服务器地址');
            } else if ($scope.remote.account == '') {
                Message.setWarning('请输入授权用户');
            } else if ($scope.remote.password == '') {
                Message.setWarning('请输入授权密码');
            } else if ($scope.remote.source == '') {
                Message.setWarning('请选择需要传输的文件');
            } else if ($scope.remote.target == '') {
                Message.setWarning('请输入远程服务器保存路径');
            } else {
                console.log('立即传输2', $scope.remote);
                $scope.trans_to_ftp();
            }
        };
        $scope.trans_to_ftp = function () {
            console.log('立即传输', $scope.remote);
            var op_data = angular.copy($scope.remote);
            Backend.call($scope, module, '/backend/transtoftp', '/backend/transtoftp_' + op_data.address + '_' + op_data.source + '_' + op_data.target,
                op_data, {
                    'success': function(data) {
                        Message.setInfo(data.msg || '传输成功！');
                    }
                }
            );
        };
    }
];