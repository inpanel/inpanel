var UtilsCtrl = ['$scope', 'Module', 'Request',
function($scope, Module, Request){
	var module = 'utils';
	Module.init(module, '系统工具');
	$scope.loaded = true;
	
	$scope.rebootconfirm = function(){
		$('#rebootconfirm').modal();
	};
	$scope.reboot = function(){
		Request.post('/operation/reboot');
	};
}];

var UtilsUserCtrl = [
'$scope', '$routeParams', 'Module', 'Timeout', 'Request',
function($scope, $routeParams, Module, Timeout, Request){
	var module = 'utils.user';
	Module.init(module, '用户管理');
	Module.initSection('user');
	$scope.loaded = true;
	
	$scope.loadUsers = function(){
		Request.post('/operation/user', {
			'action': 'listuser'
		}, function(data){
			if (data.code == 0) {
				$scope.users = data.data;
			}
		}, false, true);
	};
	$scope.loadGroups = function(){
		Request.post('/operation/user', {
			'action': 'listgroup'
		}, function(data){
			if (data.code == 0) {
				$scope.groups = data.data;
			}
		}, false, true);
	};
	$scope.useraddconfirm = function(){
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
	$scope.useradd = function(){
		var userdata = $scope.curuser;
		userdata['action'] = 'useradd';
		Request.post('/operation/user', userdata, function(data){
			if (data.code == 0) {
				$scope.loadUsers();
				$scope.loadGroups();
			}
		});
	};
	$scope.usermodconfirm = function(i){
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
	$scope.usermod = function(){
		var userdata = $scope.curuser;
		userdata['action'] = 'usermod';
		Request.post('/operation/user', userdata, function(data){
			if (data.code == 0) {
				$scope.loadUsers();
				$scope.loadGroups();
			}
		});
	};
	$scope.userdelconfirm = function(i){
		var curuser = $scope.users[i];
		$scope.curuser = {
			'pw_name': curuser.pw_name
		};
		$('#userdelconfirm').modal();
	};
	$scope.userdel = function(){
		Request.post('/operation/user', {
			'action': 'userdel',
			'pw_name': $scope.curuser['pw_name']
		}, function(data){
			if (data.code == 0) {
				$scope.loadUsers();
				$scope.loadGroups();
			}
		});
	};
	$scope.groupaddconfirm = function(){
		$scope.curgrp_name = '';
		$('#groupaddconfirm').modal();
	};
	$scope.groupadd = function(){
		Request.post('/operation/user', {
			'action': 'groupadd',
			'gr_name': $scope.curgrp_name
		}, function(data){
			if (data.code == 0) {
				$scope.loadGroups();
			}
		});
	};
	$scope.groupmodconfirm = function(i){
		$scope.curgrp_newname = $scope.curgrp_name = $scope.groups[i].gr_name;
		$('#groupmodconfirm').modal();
	};
	$scope.groupmod = function(){
		Request.post('/operation/user', {
			'action': 'groupmod',
			'gr_name': $scope.curgrp_name,
			'gr_newname': $scope.curgrp_newname
		}, function(data){
			if (data.code == 0) {
				$scope.loadGroups();
			}
		});
	};
	$scope.groupdelconfirm = function(i){
		$scope.curgrp_name = $scope.groups[i].gr_name;
		$('#groupdelconfirm').modal();
	};
	$scope.groupdel = function(){
		Request.post('/operation/user', {
			'action': 'groupdel',
			'gr_name': $scope.curgrp_name
		}, function(data){
			if (data.code == 0) {
				$scope.loadGroups();
			}
		});
	};
	$scope.groupmemsaddconfirm = function(i){
		$scope.curgrp_name = $scope.groups[i].gr_name;
		$scope.curgrp_mem = '';
		$('#groupmemsaddconfirm').modal();
	};
	$scope.groupmemsadd = function(){
		Request.post('/operation/user', {
			'action': 'groupmems_add',
			'gr_name': $scope.curgrp_name,
			'mem': $scope.curgrp_mem
		}, function(data){
			if (data.code == 0) {
				$scope.loadUsers();
				$scope.loadGroups();
			}
		});
	};
	$scope.groupmemsdelconfirm = function(i){
		$scope.curgrp_name = $scope.groups[i].gr_name;
		$scope.curgrp_mems = $scope.groups[i].gr_mem;
		$scope.curgrp_mem = '';
		$('#groupmemsdelconfirm').modal();
	};
	$scope.groupmemsdel = function(){
		Request.post('/operation/user', {
			'action': 'groupmems_del',
			'gr_name': $scope.curgrp_name,
			'mem': $scope.curgrp_mem
		}, function(data){
			if (data.code == 0) {
				$scope.loadUsers();
				$scope.loadGroups();
			}
		});
	};
}];

var UtilsNetworkCtrl = [
'$scope', '$routeParams', 'Module', 'Timeout', 'Message', 'Request', 
function($scope, $routeParams, Module, Timeout, Message, Request){
	var module = 'utils.network';
	Module.init(module, '网络设置');
	Module.initSection('ip');
	$scope.restartMessage = '是否要重启网络？';
	$scope.loaded = true;
	$scope.showRestartBtn = true;
	
	$scope.loadIfNames = function(){
		Request.get('/utils/network/ifnames', function(data){
			$scope.ifnames = data.ifnames;
			$scope.ifname = $scope.ifnames[0];
			// load the default iface's config
			$scope.loadIfConfig($scope.ifname);
		});
	};
	$scope.loadIfConfig = function(ifname){
		$scope.ifname = ifname;
		Request.get('/utils/network/ifconfig/'+ifname, function(data){
			$scope.ip = data['ip'];
			$scope.mask = data['mask'];
			$scope.gw = data['gw'];
		});
	};
	$scope.saveIfConfig = function(){
		Request.post('/utils/network/ifconfig/'+$scope.ifname, {
			'ip': $scope.ip,
			'mask': $scope.mask,
			'gw': $scope.gw
		}, function(data){
			if (data.code == 0) $scope.loadIfConfig($scope.ifname);
		});
	};
	$scope.loadNameservers = function(){
		Request.get('/utils/network/nameservers', function(data){
			$scope.nameservers = data['nameservers'];
		});
	};
	$scope.saveNameservers = function(){
		var nameservers = [];
		$('.nameserver').each(function(){
			var ns = $(this).val();
			if (ns) nameservers.push(ns);
		});
		Request.post('/utils/network/nameservers', {
			'nameservers': nameservers.join(',')
		}, function(data){
			if (data.code == 0) $scope.loadNameservers();
		});
	};
	$scope.addNameserver = function(){
		$scope.nameservers.push('');
	};
	$scope.delNameserver = function(i){
		$scope.nameservers.splice(i,1);
	};
	$scope.restart = function(){
		$scope.restartMessage = '正在重启，请稍候...'
		$scope.showRestartBtn = false;
		Timeout(function(){
			Request.post('/backend/service_restart', {
				service: 'network'
			}, function(data){
				var getRestartStatus = function(){
					Request.get('backend/service_restart_network', function(data){
						if (data.msg) $scope.restartMessage = data.msg;
						if (data.status == 'finish'){
							Message.setSuccess('');
							Timeout(function(){
								$scope.restartMessage = '是否要重启网络？';
								$scope.showRestartBtn = true;
							}, 3000, module);
						}
						else
							Timeout(getRestartStatus, 500, module);
					});
				};
				Timeout(getRestartStatus, 500, module);
			});
		}, 1000, module);
	};
}];

var UtilsTimeCtrl = [
'$scope', '$routeParams', 'Module', 'Timeout', 'Request', 'Backend',
function($scope, $routeParams, Module, Timeout, Request, Backend){
	var module = 'utils.time';
	Module.init(module, '时间设置');
	Module.initSection('datetime');
	$scope.loaded = true;

	$scope.loadDatetime = function(){
		Request.get('/utils/time/datetime', function(data){
			$scope.datetime = data;
			$scope.newDatetime = data.str;
		});
	};
	$scope.saveDatetime = function(){
		Request.post('/backend/datetime', {
			'datetime': $scope.newDatetime
		}, function(data){
			Request.setProcessing(true);
			var getStatus = function(){
				Request.get('backend/datetime', function(data){
					if (data.status != 'finish'){
						Request.setProcessing(true);
						Timeout(getStatus, 500, module);
					}
				});
			};
			Timeout(getStatus, 500, module);
		});
	};
	
	$scope.loadTimezone = function(){
		Request.get('/utils/time/timezone', function(data){
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
	$scope.loadTimezones = function(region, callback){
		if (region) {
			Request.get('/utils/time/timezone_list/'+region, function(data){
				$scope.cities = data.cities;
				if (callback) callback.call();
			});
		} else {
			Request.get('/utils/time/timezone_list', function(data){
				$scope.regions = data.regions;
				var getcities = function(){
					Request.get('/utils/time/timezone_list/'+$scope.timezone_region, function(data){
						$scope.cities = data.cities;
					});
				};
				if ($scope.timezone_region) getcities();
				else Timeout(getcities, 500, module);
			});
		}
	};
	$scope.setTimezone = function(region, city){
		$scope.timezone_region = region;
		$scope.loadTimezones(region, function(){
			$scope.timezone_city = city;
		});
	};
	$scope.saveTimezone = function(){
		var region = $scope.timezone_region;
		var city = $scope.timezone_city;
		Request.post('/utils/time/timezone', {
			'timezone': region+'/'+city
		}, function(data){
			if (data.code == 0) {
				$scope.loadTimezone();
				$scope.loadDatetime();
			}
		});
	};
	
	$scope.synctime = function(){
		var server = 'pool.ntp.org';
		Request.post('/backend/ntpdate', {
			'server': server
		}, function(data){
			Request.setProcessing(true);
			var getStatus = function(){
				Request.get('backend/ntpdate_'+server, function(data){
					if (data.status != 'finish'){
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
	
	$scope.ntpdChecking = true;
	var installInit = function(){
		$scope.installMessage = '时间同步需要使用 NTP 服务，您当前尚未安装该服务。<br>是否安装？';
		$scope.showInstallBtn = true;
	};
	var startInit = function(){
		$scope.startMessage = 'NTP 服务已安装但还未启动，是否启动？';
		$scope.showStartBtn = true;
	};
	var stopInit = function(){
		$scope.stopMessage = 'NTP 服务正在运行，是否停止？';
		$scope.showStopBtn = true;
	};
	installInit();
	startInit();
	stopInit();
	
	$scope.loadSync = function(){
		Request.get('/query/service.ntpd', function(data){
			$scope.ntpdStatus = null;
			if (data['service.ntpd']) {
				$scope.ntpdStatus = data['service.ntpd']['status'];
			}
			$scope.ntpdChecking = false;
		});
	};
	$scope.install = function(){
		$scope.installMessage = '正在安装，请稍候...'
		$scope.showInstallBtn = false;
		Backend.call(
			$scope,
			module,
			'/backend/yum_install',
			'/backend/yum_install_base_ntp', 
			{
				'repo': 'base',
				'pkg': 'ntp'
			},
			{
				'wait': function(data){
					$scope.installMessage = data.msg;
				},
				'success': function(data){
					$scope.installMessage = data.msg;
					Timeout($scope.loadSync, 3000, module);
				},
				'error': function(data){
					$scope.installMessage = data.msg;
					Timeout($scope.loadSync, 3000, module);
				}
			},
			true
		);
	};
	$scope.start = function(){
		$scope.startMessage = '正在启动，请稍候...'
		$scope.showStartBtn = false;
		Backend.call(
			$scope,
			module,
			'/backend/service_start',
			'/backend/service_start_ntpd', 
			{
				name: 'NTP',
				service: 'ntpd'
			},
			{
				'wait': function(data){
					$scope.startMessage = data.msg;
				},
				'success': function(data){
					$scope.startMessage = data.msg;
					Timeout(function(){
						startInit();
						$scope.loadSync();
					}, 3000, module);
				},
				'error': function(data){
					$scope.startMessage = data.msg;
					Timeout(function(){
						startInit();
						$scope.loadSync();
					}, 3000, module);
				}
			},
			true
		);
	};
	$scope.stop = function(){
		$scope.stopMessage = '正在停止，请稍候...'
		$scope.showStopBtn = false;
		Backend.call(
			$scope,
			module,
			'/backend/service_stop',
			'/backend/service_stop_ntpd', 
			{
				name: 'NTP',
				service: 'ntpd'
			},
			{
				'wait': function(data){
					$scope.stopMessage = data.msg;
				},
				'success': function(data){
					$scope.stopMessage = data.msg;
					Timeout(function(){
						stopInit();
						$scope.loadSync();
					}, 3000, module);
				},
				'error': function(data){
					$scope.stopMessage = data.msg;
					Timeout(function(){
						stopInit();
						$scope.loadSync();
					}, 3000, module);
				}
			},
			true
		);
	};
}];

var UtilsPartitionCtrl = [
'$scope', 'Module', 'Timeout', 'Request', 'Message', 'Backend',
function($scope, Module, Timeout, Request, Message, Backend){
	var module = 'utils.partition';
	Module.init(module, '磁盘分区');
	$scope.loaded = false;
	$scope.waiting = true;

	$scope.loadDiskinfo = function(){
		Request.get('/query/server.diskinfo', function(data){
			if (!$scope.loaded) $scope.loaded = true;
			$scope.diskinfo = data['server.diskinfo'];
			$scope.waiting = false;
		});
	};
	$scope.swaponconfirm = function(devname){
		$scope.devname = devname;
		$('#swaponconfirm').modal();
	};
	$scope.swapon = function(){
		Backend.call(
			$scope,
			module,
			'/backend/swapon',
			'/backend/swapon_on_'+$scope.devname,
			{'devname': $scope.devname},
			{'success': $scope.loadDiskinfo}
		);
	};
	$scope.swapoffconfirm = function(devname){
		$scope.devname = devname;
		$('#swapoffconfirm').modal();
	};
	$scope.swapoff = function(){
		Backend.call(
			$scope,
			module,
			'/backend/swapoff',
			'/backend/swapon_off_'+$scope.devname,
			{'devname': $scope.devname},
			{'success': $scope.loadDiskinfo}
		);
	};
	$scope.umountconfirm = function(devname){
		$scope.devname = devname;
		$('#umountconfirm').modal();
	};
	$scope.umount = function(){
		Backend.call(
			$scope,
			module,
			'/backend/umount',
			'/backend/mount_umount_'+$scope.devname,
			{'devname': $scope.devname},
			{'success': $scope.loadDiskinfo}
		);
	};
	$scope.mountconfirm = function(devname, fstype){
		$scope.devname = devname;
		$scope.mountpoint = '';
		$scope.fstype = fstype;
		Request.get('/query/config.fstab('+devname+')', function(data){
			if (data['config.fstab'] && typeof(data['config.fstab']['mount']) != 'undefined') {
				$scope.mountpoint = data['config.fstab']['mount'];
			}
		});
		$('#mountconfirm').modal();
	};
	$scope.selectmountpoint = function(i){
		$scope.selector_title = '请选择挂载点';
		$scope.selector.onlydir = true;
		$scope.selector.onlyfile = false;
		$scope.selector.load($scope.mountpoint ? $scope.mountpoint : '/');
		$scope.selector.selecthandler = function(path){
			$('#selector').modal('hide');
			$scope.mountpoint = path;
		};
		$('#selector').modal();
	};
	$scope.mount = function(){
		Backend.call(
			$scope,
			module,
			'/backend/mount',
			'/backend/mount_mount_'+$scope.devname,
			{
				'devname': $scope.devname,
				'mountpoint': $scope.mountpoint,
				'fstype': $scope.fstype
			},
			{'success': $scope.loadDiskinfo}
		);
	};
	$scope.formatconfirm = function(devname){
		$scope.devname = devname;
		Request.get('/query/tool.supportfs', function(data){
			$scope.supportfs = data['tool.supportfs'];
		});
		$('#formatconfirm').modal();
	};
	$scope.format = function(){
		Backend.call(
			$scope,
			module,
			'/backend/format',
			'/backend/format_'+$scope.devname,
			{
				'devname': $scope.devname,
				'fstype': $scope.fstype
			},
			{'success': $scope.loadDiskinfo}
		);
	};
	$scope.addpartconfirm = function(devname, unpartition){
		$scope.devname = devname;
		$scope.unpartition = unpartition;
		$('#addpartconfirm').modal();
	};
	$scope.addpart = function(){
		$scope.waiting = true;
		Message.setInfo('正在 '+$scope.devname+' 上创建分区，请稍候...', true);
		Request.post('/operation/fdisk', {
			'action': 'add',
			'devname': $scope.devname,
			'size': $scope.size,
			'unit': $scope.unit
		}, function(data){
			if (data.code == 0)
				$scope.loadDiskinfo();
			else
				$scope.waiting = false;
		});
	};
	$scope.delpartconfirm = function(devname){
		$scope.devname = devname;
		$('#delpartconfirm').modal();
	};
	$scope.delpart = function(){
		$scope.waiting = true;
		Message.setInfo('正在删除分区 '+$scope.devname+'，请稍候...', true);
		Request.post('/operation/fdisk', {
			'action': 'delete',
			'devname': $scope.devname
		}, function(data){
			if (data.code == 0)
				$scope.loadDiskinfo();
			else
				$scope.waiting = false;
		});
	};
	$scope.scanpartconfirm = function(devname){
		$scope.devname = devname;
		$('#scanpartconfirm').modal();
	};
	$scope.scanpart = function(){
		$scope.waiting = true;
		Message.setInfo('正在扫描 '+$scope.devname+' 的分区，请稍候...', true);
		Request.post('/operation/fdisk', {
			'action': 'scan',
			'devname': $scope.devname
		}, function(data){
			if (data.code == 0)
				Timeout($scope.loadDiskinfo, 1000, module);
			else
				$scope.waiting = false;
		});
	};
}];

var UtilsAutoFMCtrl = [
'$scope', 'Module', 'Timeout', 'Request', 'Message', 'Backend',
function($scope, Module, Timeout, Request, Message, Backend){
	var module = 'utils.autofm';
	Module.init(module, '自动格式化挂载');
	$scope.loaded = false;
	$scope.waiting = true;
	$scope.diskcount = 0;

	$scope.loadDiskinfo = function(){
		Request.get('/query/server.diskinfo', function(data){
			if (!$scope.loaded) $scope.loaded = true;
			$scope.diskinfo = data['server.diskinfo'];
			$scope.waiting = false;
			$scope.diskcount = 0;
			for (var i in data['server.diskinfo']['partitions']) {
				var p = data['server.diskinfo']['partitions'][i];
				if (p.is_hw&&!p.is_pv&&p.partcount==0&&!p.mount){
					$scope.diskcount++;
				}
			}
		});
	};
	$scope.confirm = function(devname){
		$scope.devname = devname;
		$scope.mountpoint = '';
		$scope.fstype = '';
		// check mount points under /data/
		Request.post('/operation/file', {
			'action': 'listdir',
			'path': '/data',
			'showhidden': true,
			'remember': false
		}, function(data){
			if (data.code == 0) {
				var items = data.data;
				if (items.length==0) {
					$scope.mountpoint = '/data/0';
				} else {
					var names = {};
					for (var i=0; i<items.length; i++) {
						names[items[i].name] = true;
					}
					var diski = 0;
					while (1) {
						if (!names[''+diski]) break;
						diski++;
					}
					$scope.mountpoint = '/data/'+diski;
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
		Request.get('/query/tool.supportfs', function(data){
			var fs = data['tool.supportfs'];
			for (var i=0; i<fs.length; i++){
				if (fs[i]=='swap') fs.splice(i, 1);
				if (fs[i] == 'xfs') $scope.fstype = 'xfs';
				else if (fs[i] == 'ext4') $scope.fstype = 'ext4';
				else if (fs[i] == 'ext3') $scope.fstype = 'ext3';
			}
			$scope.supportfs = fs;
		});
		$('#confirm').modal();
	};
	$scope.selectmountpoint = function(i){
		$scope.selector_title = '请选择挂载点';
		$scope.selector.onlydir = true;
		$scope.selector.onlyfile = false;
		$scope.selector.load($scope.mountpoint);
		$scope.selector.selecthandler = function(path){
			$('#selector').modal('hide');
			$scope.mountpoint = path;
		};
		$('#selector').modal();
	};
	$scope.autofm = function(){
		// check the mount point
		Request.post('/operation/file', {
			'action': 'listdir',
			'path': $scope.mountpoint,
			'showhidden': true,
			'remember': false
		}, function(data){
			if (data.code == 0) {
				var items = data.data;
				if (items.length>0){
					var mount_detect = false;
					for (var i=0; i<items.length; i++) {
						if (items[i].name == 'lost+found') {
							mount_detect = true;
							break;
						}
					}
					if (mount_detect)
						Message.setError('已有其它设备挂载在 '+$scope.mountpoint+' 下，请重新选择挂载点。');
					else
						Message.setError('挂载点 '+$scope.mountpoint+' 下存在文件或目录，无法挂载！请重新选择挂载点。');
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
	$scope.mount = function(){
		Backend.call(
			$scope,
			module,
			'/backend/mount',
			'/backend/mount_mount_'+$scope.devname,
			{
				'devname': $scope.devname,
				'mountpoint': $scope.mountpoint,
				'fstype': $scope.fstype
			},
			{'success': $scope.loadDiskinfo}
		);
	};
	$scope.format = function(){
		Backend.call(
			$scope,
			module,
			'/backend/format',
			'/backend/format_'+$scope.devname,
			{
				'devname': $scope.devname,
				'fstype': $scope.fstype
			},
			{'success': $scope.mount}
		);
	};
}];

var UtilsMoveDataCtrl = [
'$scope', 'Module', 'Timeout', 'Request', 'Message', 'Backend',
function($scope, Module, Timeout, Request, Message, Backend){
	var module = 'utils.movedata';
	Module.init(module, '数据移至数据盘');
	$scope.loaded = false;
	$scope.waiting = true;
	$scope.srcpath = '/var';
	$scope.despath = '/';
	$scope.mountpoint = '/';

	$scope.loadMounts = function(){
		Request.get('/query/server.mounts', function(data){
			if (!$scope.loaded) $scope.loaded = true;
			$scope.mounts = data['server.mounts'];
			$scope.waiting = false;
		});
	};
	$scope.setdespath = function(value){
		$scope.despath = value;
	};
	$scope.selectsrcpath = function(i){
		$scope.selector_title = '请选择要迁移的目录（原始目录）';
		$scope.selector.onlydir = true;
		$scope.selector.onlyfile = false;
		$scope.selector.load($scope.srcpath);
		$scope.selector.selecthandler = function(path){
			$('#selector').modal('hide');
			$scope.srcpath = path;
		};
		$('#selector').modal();
	};
	$scope.selectdespath = function(i){
		$scope.selector_title = '请选择要迁移到的目录（目标目录）';
		$scope.selector.onlydir = true;
		$scope.selector.onlyfile = false;
		$scope.selector.load($scope.despath);
		$scope.selector.selecthandler = function(path){
			$('#selector').modal('hide');
			$scope.despath = path;
		};
		$('#selector').modal();
	};
	$scope.movedata = function(){
		$scope.waiting = true;
		var srcpath = $scope.srcpath.replace(/\/$/, '');
		var srcname = srcpath.split('/').pop();
		var despath = $scope.despath.replace(/\/$/, '')+'/'+srcname;
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
		}, function(data){
			if (data.code == 0) {
				// check if dir or link
				if (!data.data.isdir) {
					Message.setError($scope.srcpath+' 不是有效的目录！（可能是文件或链接）');
					$scope.waiting = false;
					return;
				}
				// check the despath
				Request.post('/operation/file', {
					'action': 'getitem',
					'path': despath
				}, function(data){
					if (data.code == 0) {
						Message.setError('目标目录下已有同名文件或目录 '+despath+'，迁移失败！');
						$scope.waiting = false;
					} else {
						// moving
						Backend.call(
							$scope,
							module,
							'/backend/move',
							'/backend/move_'+srcpath+'_'+despath, 
							{
								'srcpath': srcpath,
								'despath': despath
							},
							{
								'success': function(data){
									Message.setInfo('正在原始目录创建链接...');
									Request.post('/operation/file', {
										'action': 'link',
										'srcpath': despath,
										'despath': srcpath
									}, function(data){
										if (data.code == 0) {
											Message.setSuccess('迁移完成！');
										} else {
											Message.setError('迁移失败！'+data.msg);
										}
										$scope.waiting = false;
									}, false, true);
								},
								'error': function(data){
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
}];