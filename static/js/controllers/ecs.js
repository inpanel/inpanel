var ECSCtrl = [
    '$scope', '$rootScope', '$location', 'Module', 'Message', 'Request',
    function ($scope, $rootScope, $location, Module, Message, Request) {
        var module = 'ecs';
        Module.init(module, '云服务器管理');
        $scope.loaded = false;
        $scope.instances = [];

        $scope.load = function () {
            Request.get('/ecs/account?status=enable', function (data) {
                if (data.code == 0) {
                    $scope.accounts = data.data;
                    if ($scope.accounts.length > 0) {
                        if (!$rootScope.$ecs.access_key_id)
                            $rootScope.$ecs.access_key_id = $scope.accounts[0].access_key_id;
                        $scope.loadinstances();
                    }
                }
                $scope.loaded = true;
            }, false, true);
        };

        $scope.loadinstances = function (pagedir) {
            $scope.instloading = true;
            $scope.lastinstances = angular.copy($scope.instances);
            $scope.instances = [];
            $scope.errmsg = '';
            if (pagedir) $rootScope.$ecs.page_number = parseInt($rootScope.$ecs.page_number) + parseInt(pagedir);
            var query = 'access_key_id=' + $rootScope.$ecs.access_key_id + '&page_number=' + $rootScope.$ecs.page_number + '&page_size=' + $rootScope.$ecs.page_size;
            Request.get('/ecs/instances?' + query, function (data) {
                if (data.code == 0) {
                    data = data.data;
                    $scope.instances = data.instances;
                    if ($scope.instances.length > 0) {
                        $rootScope.$ecs.page_number = data.page_number;
                        $rootScope.$ecs.page_size = data.page_size;
                    } else {
                        // detect whether there has next page
                        if ($rootScope.$ecs.page_number > 1) {
                            Message.setError('这已经是最后一页了。');
                            $rootScope.$ecs.page_number--;
                            $scope.instances = $scope.lastinstances;
                        }
                    }
                } else {
                    Message.setError('');
                    $scope.errmsg = data.msg;
                }
                $scope.instloading = false;
            });
        };

        $scope.chaccount = function () {
            $rootScope.$ecs.page_number = 1;
            $scope.loadinstances();
        };
    }
];

var ECSIndexCtrl = [
    '$scope', '$rootScope', '$location', 'Module', 'Message', 'Request',
    function ($scope, $rootScope, $location, Module, Message, Request) {
        var module = 'ecs.index';
        Module.init(module, '云服务器管理');
        $scope.loaded = false;
        $scope.instances = [];

        $scope.load = function () {
            $scope.loaded = true;
        };
    }
];

var ECSSettingCtrl = [
    '$scope', '$rootScope', '$routeParams', '$location', 'Module', 'Message', 'Request', 'Timeout', 'Backend',
    function ($scope, $rootScope, $routeParams, $location, Module, Message, Request, Timeout, Backend) {
        var section = $routeParams.section;
        var section = decodeURIComponent(section);
        fs = section.split(',');
        $scope.instance_name = fs[0];
        var access_key_id = fs[1];

        var module = 'ecs.setting';
        Module.init(module, '管理 ' + $scope.instance_name);
        Module.initSection('base');
        $scope.loaded = false;
        var query = 'access_key_id=' + access_key_id + '&instance_name=' + $scope.instance_name;

        $scope.load = function (quiet) {
            Request.get('/ecs/instance?' + query, function (data) {
                if (data.code == 0) {
                    $scope.instance = data.data;
                    if ($scope.images.length == 0) $scope.loadimages();
                }
                $scope.loaded = true;
                if ($scope.instance) {
                    var s = $scope.instance.Status.toLowerCase();
                    if (s == 'pending' || s == 'starting' || s == 'stopping' || s == 'transferring' || s == 'resetting')
                        Timeout(function () {
                            $scope.load(true);
                        }, 1000, module);
                    if (s != 'pending' && s != 'starting' && s != 'startfailure' && s != 'released')
                        if ($scope.disks.length == 0) $scope.loaddisks();
                }
            }, false, Module.getSection() != 'base' || quiet);
        };

        $scope.start = function () {
            $scope.processing = true;
            Message.setInfo('正在向云服务器发送启动指令，请稍候...');
            Request.get('/ecs/startinstance', {
                'access_key_id': access_key_id,
                'instance_name=': $scope.instance_name
            }, function (data) {
                if (data.code == 0) {
                    $scope.instance.Status = data.data.InstanceStatus;
                    Timeout(function () {
                        $scope.load(true);
                    }, 1000, module);
                }
                $scope.processing = false;
            });
        };
        $scope.stop = function () {
            $scope.confirm_title = '关闭服务器操作确认';
            $scope.confirm_body = '是否确定要关闭服务器？';
            $scope.confirm_forcebutton = '强制关闭';
            $scope.confirm_button = '确认关闭';
            $scope.confirm = function () {
                dostop();
            };
            $scope.confirm_force = function () {
                dostop(true);
            };
            $('#confirm').modal();
        };
        var dostop = function (force) {
            $scope.processing = true;
            Message.setInfo('正在向云服务器发送关闭指令，请稍候...');
            Request.post('/ecs/stopinstance', {
                'access_key_id': access_key_id,
                'instance_name': $scope.instance_name,
                'force': force ? '&force=yes' : ''
            }, function (data) {
                if (data.code == 0) {
                    $scope.instance.Status = data.data.InstanceStatus;
                    Timeout(function () {
                        $scope.load(true);
                    }, 1000, module);
                }
                $scope.processing = false;
            });
        };
        $scope.reboot = function () {
            $scope.confirm_title = '重启服务器操作确认';
            $scope.confirm_body = '是否确定要重启服务器？';
            $scope.confirm_forcebutton = '强制重启';
            $scope.confirm_button = '确认重启';
            $scope.confirm = function () {
                doreboot();
            };
            $scope.confirm_force = function () {
                doreboot(true);
            };
            $('#confirm').modal();
        };
        var doreboot = function (force) {
            $scope.processing = true;
            Message.setInfo('正在向云服务器发送重启指令，请稍候...');
            Request.post('/ecs/rebootinstance', {
                'access_key_id': access_key_id,
                'instance_name': $scope.instance_name,
                'force': force ? '&force=yes' : ''
            }, function (data) {
                if (data.code == 0) {
                    $scope.instance.Status = data.data.InstanceStatus;
                    Timeout(function () {
                        $scope.load(true);
                    }, 1000, module);
                }
                $scope.processing = false;
            });
        };

        $scope.imageloading = false;
        $scope.images = [];
        $scope.image_code = '';
        $scope.image_total_number = 0;
        $scope.image_page_number = 1;
        $scope.image_page_size = 10;
        $scope.loadimages = function (pagedir, quiet) {
            $scope.imageloading = true;
            if (pagedir) $scope.image_page_number = parseInt($scope.image_page_number) + parseInt(pagedir);
            var query = 'access_key_id=' + access_key_id + '&region_code=' + $scope.instance.RegionCode;
            query += '&page_number=' + $scope.image_page_number + '&page_size=' + $scope.image_page_size;
            Request.get('/ecs/images?' + query, function (data) {
                if (data.code == 0) {
                    data = data.data;
                    $scope.images = data.images;
                    $scope.image_total_number = data.total_number;
                    $scope.image_page_number = data.page_number;
                    $scope.image_page_size = data.page_size;
                    if ($scope.images.length > 0)
                        $scope.image_code = $scope.images[0].ImageCode;
                }
                $scope.imageloading = false;
            }, false, Module.getSection() != 'reset' || quiet);
        };

        $scope.reset = function (image) {
            $scope.curimage = image;
            $('#resetconfirm').modal();
        };
        $scope.doreset = function (force) {
            $scope.processing = true;
            Message.setInfo('正在向云服务器发送重置系统指令，请稍候...');
            Request.post('/ecs/resetinstance', {
                'access_key_id': access_key_id,
                'instance_name': $scope.instance_name,
                'image_code': $scope.curimage.ImageCode
            }, function (data) {
                if (data.code == 0) {
                    $scope.instance.Status = data.data.InstanceStatus;
                    Timeout(function () {
                        $scope.load(true);
                    }, 1000, module);
                }
                $scope.processing = false;
            });
        };

        $scope.diskloading = false;
        $scope.disks = [];
        $scope.loaddisks = function () {
            $scope.diskloading = true;
            Request.get('/ecs/disks?' + query, function (data) {
                if (data.code == 0) {
                    data = data.data;
                    $scope.disks = data.disks;
                }
                $scope.diskloading = false;
            }, false, Module.getSection() != 'disks');
        };

        $scope.snaploading = false;
        $scope.snapshots = [];
        $scope.loadsnapshots = function (disk, quiet) {
            $scope.snaploading = true;
            if (disk) $scope.curdisk = disk;
            Request.get('/ecs/snapshots?' + query + '&disk_code=' + $scope.curdisk.DiskCode, function (data) {
                if (data.code == 0) {
                    data = data.data;
                    $scope.snapshots = data.snapshots;
                }
                $scope.snaploading = false;
            }, false, Module.getSection() != 'disks' || quiet);
        };

        $scope.createsnapshot = function () {
            var s = $scope.instance.Status.toLowerCase();
            if (s != 'stopped' && s != 'running') {
                Message.setError('只允许在云服务器停止或正常运行状态下创建快照！');
                return;
            }
            $scope.confirm_title = '创建快照操作确认';
            $scope.confirm_body = '是否要立即创建一份快照？';
            $scope.confirm_button = '立即创建';
            $scope.confirm = function () {
                docreatesnapshot();
            };
            $scope.confirm_forcebutton = false;
            $scope.confirm_force = false;
            $('#confirm').modal();
        };
        var docreatesnapshot = function () {
            $scope.processing = true;
            Message.setInfo('正在发送快照创建指令，请稍候...');
            Request.post('/ecs/createsnapshot', {
                'access_key_id': access_key_id,
                'instance_name': $scope.instance_name,
                'disk_code': $scope.curdisk.DiskCode
            }, function (data) {
                if (data.code == 0) {
                    $scope.loadsnapshots(false, true);
                }
                $scope.processing = false;
            });
        };

        $scope.cancelsnapshot = function (snapshot) {
            var s = $scope.instance.Status.toLowerCase();
            if (s != 'stopped' && s != 'running') {
                Message.setError('只允许在云服务器停止或正常运行状态下取消快照创建！');
                return;
            }
            $scope.cursnapshot = snapshot;
            $scope.confirm_title = '取消快照创建操作确认';
            $scope.confirm_body = '是否要取消正在创建的快照？';
            $scope.confirm_button = '确认取消';
            $scope.confirm = function () {
                docancelsnapshot();
            };
            $scope.confirm_forcebutton = false;
            $scope.confirm_force = false;
            $('#confirm').modal();
        };
        var docancelsnapshot = function () {
            $scope.processing = true;
            Message.setInfo('正在发送快照取消指令，请稍候...');
            Request.post('/ecs/cancelsnapshot', {
                'access_key_id': access_key_id,
                'instance_name': $scope.instance_name,
                'snapshot_code': $scope.cursnapshot.SnapshotCode
            }, function (data) {
                if (data.code == 0) {
                    $scope.loadsnapshots(false, true);
                }
                $scope.processing = false;
            });
        };

        $scope.deletesnapshot = function (snapshot) {
            var s = $scope.instance.Status.toLowerCase();
            if (s != 'stopped' && s != 'running') {
                Message.setError('只允许在云服务器停止或正常运行状态下删除快照！');
                return;
            }
            $scope.cursnapshot = snapshot;
            $scope.confirm_title = '删除快照操作确认';
            $scope.confirm_body = '是否要删除这个快照？';
            $scope.confirm_button = '确认删除';
            $scope.confirm = function () {
                dodeletesnapshot();
            };
            $scope.confirm_forcebutton = false;
            $scope.confirm_force = false;
            $('#confirm').modal();
        };
        var dodeletesnapshot = function () {
            $scope.processing = true;
            Message.setInfo('正在发送快照删除指令，请稍候...');
            Request.post('/ecs/deletesnapshot', {
                'access_key_id': access_key_id,
                'instance_name': $scope.instance_name,
                'disk_code': $scope.curdisk.DiskCode,
                'snapshot_code': $scope.cursnapshot.SnapshotCode
            }, function (data) {
                if (data.code == 0) {
                    $scope.loadsnapshots(false, true);
                }
                $scope.processing = false;
            });
        };

        $scope.rollbacksnapshot = function (snapshot) {
            var s = $scope.instance.Status.toLowerCase();
            if (s != 'stopped' && s != 'running') {
                Message.setError('只允许在云服务器停止状态下回滚快照！');
                return;
            }
            $scope.cursnapshot = snapshot;
            $scope.confirm_title = '回滚快照操作确认';
            $scope.confirm_body = '是否要将磁盘回滚到这个快照版本？';
            $scope.confirm_button = '确认回滚';
            $scope.confirm = function () {
                dorollbacksnapshot();
            };
            $scope.confirm_forcebutton = false;
            $scope.confirm_force = false;
            $('#confirm').modal();
        };
        var dorollbacksnapshot = function () {
            $scope.processing = true;
            Message.setInfo('正在发送快照回滚指令，请稍候...');
            Request.post('/ecs/rollbacksnapshot', {
                'access_key_id': access_key_id,
                'instance_name': $scope.instance_name,
                'disk_code': $scope.curdisk.DiskCode,
                'snapshot_code': $scope.cursnapshot.SnapshotCode
            }, function (data) {
                if (data.code == 0) {
                    $scope.loadsnapshots(false, true);
                }
                $scope.processing = false;
            });
        };

        $scope.loadintranet = function (quiet) {
            Request.get('/ecs/accessinfo?instance_name=' + $scope.instance_name, function (data) {
                if (data.code == 0) {
                    $scope.accessinfo = data.data;
                }
            }, false, quiet);
        };

        $scope.saveintranet = function () {
            Request.post('/ecs/accessinfo', {
                'instance_name': $scope.instance_name,
                'accesskey': $scope.accessinfo.accesskey,
                'accessnet': $scope.accessinfo.accessnet,
                'accessport': $scope.accessinfo.accessport
            }, function (data) {
                if (data.code == 0) {
                    $scope.loadintranet(true);
                }
            });
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

            $scope.accessinfo.accesskey = b64encode(randstring);
        };

        $scope.intranet_install = function () {
            if (!$scope.ssh_ip) $scope.ssh_ip = $scope.instance.PublicIpAddress.AllocateIpAddress;
            if (!$scope.ssh_port) $scope.ssh_port = '22';
            if (!$scope.ssh_user) $scope.ssh_user = 'root';
            $scope.sshconfirm_title = '安装/升级 Intranet 到此服务器上';
            $scope.sshconfirm_button = '安装或升级';
            $scope.sshconfirm = doinstallintranet;
            $('#sshconfirm').modal();
        };
        var doinstallintranet = function () {
            $scope.processing = true;
            Message.setInfo('正在安装 Intranet 到远程服务器，请稍候...');
            Backend.call(
                $scope,
                module,
                '/backend/intranet_install',
                '/backend/intranet_install_' + $scope.ssh_ip, {
                    'ssh_ip': $scope.ssh_ip,
                    'ssh_port': $scope.ssh_port,
                    'ssh_user': $scope.ssh_user,
                    'ssh_password': $scope.ssh_password,
                    'instance_name': $scope.instance_name,
                    'accessnet': $scope.ssh_ip == $scope.instance.PublicIpAddress.AllocateIpAddress ? 'public' : 'inner'
                }, {
                    'success': function (data) {
                        $scope.loadintranet(true);
                        $scope.processing = false;
                    },
                    'error': function () {
                        $scope.processing = false;
                    }
                }
            );
        };

        $scope.intranet_uninstall = function () {
            if (!$scope.ssh_ip) $scope.ssh_ip = $scope.instance.PublicIpAddress.AllocateIpAddress;
            if (!$scope.ssh_port) $scope.ssh_port = '22';
            if (!$scope.ssh_user) $scope.ssh_user = 'root';
            $scope.sshconfirm_title = '在此服务器上卸载 Intranet';
            $scope.sshconfirm_button = '开始卸载';
            $scope.sshconfirm = douninstallintranet;
            $('#sshconfirm').modal();
        };
        var douninstallintranet = function () {
            $scope.processing = true;
            Message.setInfo('正在从远程服务器卸载 Intranet，请稍候...');
            Backend.call(
                $scope,
                module,
                '/backend/intranet_uninstall',
                '/backend/intranet_uninstall_' + $scope.ssh_ip, {
                    'ssh_ip': $scope.ssh_ip,
                    'ssh_port': $scope.ssh_port,
                    'ssh_user': $scope.ssh_user,
                    'ssh_password': $scope.ssh_password,
                    'instance_name': $scope.instance_name
                }, {
                    'success': function (data) {
                        $scope.loadintranet(true);
                        $scope.processing = false;
                    },
                    'error': function () {
                        $scope.processing = false;
                    }
                }
            );
        };

        $scope.syncaccesskey = function () {
            if (!$scope.ssh_ip) $scope.ssh_ip = $scope.instance.PublicIpAddress.AllocateIpAddress;
            if (!$scope.ssh_port) $scope.ssh_port = '22';
            if (!$scope.ssh_user) $scope.ssh_user = 'root';
            $scope.sshconfirm_title = '同步密钥到远程服务器';
            $scope.sshconfirm_button = '开始同步';
            $scope.sshconfirm = doupdateintranet;
            $('#sshconfirm').modal();
        };
        var doupdateintranet = function () {
            $scope.processing = true;
            Message.setInfo('正在同步密钥到远程，请稍候...');
            Backend.call(
                $scope,
                module,
                '/backend/intranet_update',
                '/backend/intranet_update_' + $scope.ssh_ip, {
                    'ssh_ip': $scope.ssh_ip,
                    'ssh_port': $scope.ssh_port,
                    'ssh_user': $scope.ssh_user,
                    'ssh_password': $scope.ssh_password,
                    'instance_name': $scope.instance_name
                }, {
                    'success': function (data) {
                        $scope.loadintranet(true);
                        $scope.processing = false;
                    },
                    'error': function () {
                        $scope.processing = false;
                    }
                }
            );
        };
    }
];

var ECSAccountCtrl = [
    '$scope', '$rootScope', '$location', 'Module', 'Request',
    function ($scope, $rootScope, $location, Module, Request) {
        var module = 'ecs.account';
        Module.init(module, '帐号管理');
        $scope.accounts = [];
        $scope.loaded = false;

        $scope.load = function (quiet) {
            Request.get('/ecs/account', function (data) {
                if (data.code == 0) {
                    $scope.accounts = data.data;
                }
                $scope.loaded = true;
            }, false, quiet);
        };

        $scope.addconfirm = function (account) {
            $scope.newaccount = {
                'name': '',
                'access_key_id': '',
                'access_key_secret': '',
                'status': true
            };
            $('#addconfirm').modal();
        };
        $scope.add = function () {
            Request.post('/ecs/account', {
                'action': 'add',
                'name': $scope.newaccount.name,
                'access_key_id': $scope.newaccount.access_key_id,
                'access_key_secret': $scope.newaccount.access_key_secret,
                'status': $scope.newaccount.status
            }, function () {
                $scope.load(true);
            });
        };

        $scope.editconfirm = function (account) {
            $scope.curaccount = account;
            $scope.curaccount.old_access_key_id = account.access_key_id;
            $('#editconfirm').modal();
        };
        $scope.update = function () {
            Request.post('/ecs/account', {
                'action': 'update',
                'old_access_key_id': $scope.curaccount.old_access_key_id,
                'name': $scope.curaccount.name,
                'access_key_id': $scope.curaccount.access_key_id,
                'access_key_secret': $scope.curaccount.access_key_secret,
                'status': $scope.curaccount.status
            }, function () {
                $scope.load(true);
            });
        };

        $scope.removeconfirm = function (account) {
            $scope.curaccount = account;
            $('#removeconfirm').modal();
        };
        $scope.remove = function () {
            Request.post('/ecs/account', {
                'action': 'delete',
                'access_key_id': $scope.curaccount.access_key_id
            }, function () {
                $scope.load(true);
            });
        };
    }
];