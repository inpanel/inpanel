angular.module('vpsmate.filters', []).
filter('iftrue', function(){
	return function(input, cond) {
		return cond ? input : '';
	};
}).
filter('ifmatch', function(){
	return function(input, cond) {
		return cond[0].match(new RegExp('^'+cond[1]+'$')) ? input : '';
	};
}).
filter('ifnotmatch', function(){
	return function(input, cond) {
		return cond[0].match(new RegExp('^'+cond[1]+'$')) ? '' : input;
	};
}).
filter('ifin', function(){
	return function(input, cond) {
		return typeof cond[1][cond[0]] != 'undefined' ? input : '';
	};
}).
filter('ifnotin', function(){
	return function(input, cond) {
		return typeof cond[1][cond[0]] != 'undefined' ? '' : input;
	};
}).
filter('ifverget', function(){	// version great or equal then
	return function(input, cond) {
		if (!cond[0] || !cond[1]) return '';
		var v1parts = cond[0].split('.');
		var v2parts = cond[1].split('.');
		for (var i=0; i<v1parts.length; i++) {
			if (v2parts.length == i) {
				return input;
			}
			if (v1parts[i] == v2parts[i]) {
				continue;
			}
			else if (v1parts[i] > v2parts[i]) {
				return input;
			}
			else {
				return '';
			}
		}
		if (v1parts.length != v2parts.length) {
			return '';
		}
		return input;
	};
}).
filter('urlencode', function(){
	return function(input) {
		return input ? encodeURIComponent(input) : '';
	};
}).
filter('netiface.updown', function(){
	return function(input) {
		return input == 'up'
			? '<span class="label label-success">启用</span>'
			: '<span class="label label-warning">停用</span>';
	};
}).
filter('netiface.encap', function(){
	return function(input) {
		if (input == 'Local Loopback') return '本地环路';
		if (input == 'Ethernet') return '以太网';
		if (input == 'Point-to-Point Protocol') return '点对点';
		if (input == 'UNSPEC') return '未识别';
		return input;
	};
}).
filter('loadavg.overload', function(){
	return function(input, cpucount) {
		if (!input) return '';
		var overload = input-cpucount;
		overload = parseInt(overload*100/cpucount);
		if (overload<0) {
			return '<span class="label label-success">'+Math.abs(overload)+'%空闲</span>';
		} else {
			if (overload>100) {
				return '<span class="label label-important">'+overload+'%过载</span>';
			} else {
				return '<span class="label label-warning">'+overload+'%过载</span>';
			}
		}
	};
}).
filter('uptime.idlerate', function(){
	return function(input) {
		if (!input) return '';
		var rate = parseInt(input);
		if (rate<10) {
			return '<span class="label label-important">'+input+'空闲</span>';
		} else if (rate<25) {
			return '<span class="label label-warning">'+input+'空闲</span>';
		} else {
			return '<span class="label label-success">'+input+'空闲</span>';
		}
	};
}).
filter('space.used', function(){
	return function(input) {
		if (!input) return '';
		var rate = parseInt(input);
		if (rate>90) {
			return '<span class="label label-important">'+input+'</span>';
		} else if (rate>75) {
			return '<span class="label label-warning">'+input+'</span>';
		} else {
			return '<span class="label label-success">'+input+'</span>';
		}
	};
}).
filter('space.free', function(){
	return function(input) {
		if (!input) return '';
		var rate = parseInt(input);
		if (rate<10) {
			return '<span class="label label-important">'+input+'</span>';
		} else if (rate<25) {
			return '<span class="label label-warning">'+input+'</span>';
		} else {
			return '<span class="label label-success">'+input+'</span>';
		}
	};
}).
filter('service.status', function(){
	return function(input) {
		if (!input) return '<span class="label">未安装</span>';
		return input == 'running'
			 ? '<span class="label label-success">运行中</span>'
			 : '<span class="label label-important">已停止</span>';
	};
}).
filter('user.lock', function(){
	return function(input) {
		return input
			? '<span class="label">锁定</span>'
			: '<span class="label label-success">正常</span>';
	};
}).
filter('site.status', function(){
	return function(input) {
		return input == 'on'
			 ? '<span class="label label-success">启用</span>'
			 : '<span class="label label-important">停用</span>';
	};
}).
filter('site.engine', function(){
	return function(input) {
		if (input == 'static')
			return '静态';
		else if (input == 'fastcgi')
			return 'FastCGI';
		else if (input == 'scgi')
			return 'SCGI';
		else if (input == 'uwsgi')
			return 'uWSGI';
		else if (input == 'redirect')
			return '跳转';
		else if (input == 'rewrite')
			return '重写';
		else if (input == 'proxy')
			return '反代';
		else if (input == 'return')
			return '错误';
		else
			return input;
	};
}).
filter('site.port', function(){
	return function(input) {
		if (input == '80')
			return 'http';
		else if (input == '443')
			return 'https';
		else
			return ''
	};
}).
filter('site.default_server', function(){
	return function(input) {
		return !input ? '<span class="label label-info">默认</span>' : '';
	};
}).
filter('bytes2human', function(){
	return function(n) {
		var symbols = ['G', 'M', 'K'];
		var x = symbols.length;
		var units = [];
		for (var i=0; i<x; i++) {
			units[i] = 1 << (x-i)*10;
		}
		for (var i=0; i<x; i++)
			if (n >= units[i])
				return Math.round((n/units[i])*10)/10 + symbols[i]; 
		return n+'B';
	};
}).
filter('mysql.user', function(){
	return function(input) {
		return input == '' ? '<span class="text-error">任意</span>' : input;
	};
}).
filter('mysql.haspasswd', function(){
	return function(input) {
		return input == 'N' ? '<span class="text-error">否</span>' : '是';
	};
}).
filter('mysql.grant', function(){
	return function(input) {
		return input == 'N' ? '否' : '是';
	};
}).
filter('mysql.privtype', function(){
	return function(input, dbname) {
		if (input == '*' || input == '') return '全局指定';
		if (input == dbname) return '按数据库指定';
		return '通配符';
	};
}).
filter('mysql.privtype_en', function(){
	return function(input, dbname) {
		if (input == '*' || input == '') return 'global';
		if (input == dbname) return 'bydb';
		return 'wildcard';
	};
}).
filter('mysql.privs', function(){
	return function(user, type) {
		if (!user) return '---';
		var privs = [
			'Select_priv',
			'Insert_priv',
			'Update_priv',
			'Delete_priv',
			'Create_priv',
			'Alter_priv',
			'Index_priv', 
			'Drop_priv',
			'Create_tmp_table_priv',
			'Show_view_priv', 
			'Create_routine_priv',
			'Alter_routine_priv',
			'Execute_priv',
			'Create_view_priv',
			'Event_priv',
			'Trigger_priv',
			'Lock_tables_priv', 
			'References_priv'
		];
		var global_privs = [
			'File_priv',
			'Super_priv',
			'Process_priv',
			'Reload_priv',
			'Shutdown_priv',
			'Show_db_priv',
			'Repl_client_priv',
			'Repl_slave_priv',
			'Create_user_priv'
			//'Create_tablespace_priv'
		];
		if (type=='global') privs = privs.concat(global_privs);

		var privs_count = 0;
		for (var i=0; i<privs.length; i++) {
			if (user[privs[i]] == 'Y') privs_count++;
		}
		if (privs_count == 0) {
			return type == 'global' ? '无全局权限' : '无权限';
		} else if (privs_count == privs.length) {
			return '所有权限';
		} else {
			return '部分权限';
		}
	};
});