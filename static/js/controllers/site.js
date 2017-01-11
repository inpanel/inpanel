var SiteCtrl = ['$scope', 'Module', '$routeParams', 'Request', 'Message', 'Backend',
function($scope, Module, $routeParams, Request, Message, Backend){
	var module = 'site';
	Module.init(module, '网站管理');
	$scope.loaded = false;

	var section = Module.getSection();
	$scope.has_httpserver = false;
	$scope.nginx_supported = false;
	$scope.apache_supported = false;
	$scope.site_packages = [];
	
	$scope.load = function(){
		Request.get('/query/service.nginx,service.httpd', function(data){
			if (data['service.nginx'] && data['service.nginx'].status) $scope.nginx_supported = true;
			if (data['service.httpd'] && data['service.httpd'].status) $scope.apache_supported = true;
			$scope.has_httpserver = $scope.nginx_supported || $scope.apache_supported;
			if ($scope.has_httpserver) {
				if (section) {
					if (section == 'nginx' && $scope.nginx_supported)
						Module.setSection('nginx');
					else if (section == 'apache' && $scope.apache_supported)
						Module.setSection('apache');
					else if (section == 'package')
						Module.setSection('package');
					else
						Module.setSection($scope.nginx_supported ? 'nginx' : 'apache');
				} else {
					Module.setSection($scope.nginx_supported ? 'nginx' : 'apache');
				}
			}
			$scope.loaded = true;
			$scope.loadsites();
		});
		Request.get('/sitepackage/getlist', function(data){
			if (data.code == 0) {
				$scope.site_packages = data.data;
			}
		});
	};
	
	$scope.package_install_setting = function(pkg){
		$scope.curpkg = pkg;
		$scope.curver = pkg.versions[0];
		$scope.pkgver = $scope.curver.code;
		$scope.installpath = '/var/www';
		$('#pkg_install_setting').modal();
	};
	$scope.package_version_select = function(v){
		$scope.pkgver = v.code;
		$scope.curver = v;
	};
	$scope.selectinstallpath = function(i){
		$scope.selector_title = '请选择安装目录';
		$scope.selector.onlydir = true;
		$scope.selector.onlyfile = false;
		$scope.selector.load($scope.installpath);
		$scope.selector.selecthandler = function(path){
			$('#selector').modal('hide');
			$scope.installpath = path;
		};
		$('#selector').modal();
	};
	$scope.package_install = function(){
		// check whether the installpath is exists and whether it is empty
		Message.setInfo('正在检测安装目录...', true);
		Request.post('/operation/file', {
			'action': 'listdir',
			'path': $scope.installpath,
			'showhidden': true,
			'remember': false
		}, function(data){
			if (data.code == 0) {
				Message.setInfo('');
				if (data.data.length>0) {
					$scope.confirm_title = '安装确认';
					$scope.confirm_body = '<p>系统检测到目录 '+$scope.installpath+' 下存在文件，继续安装将可能会覆盖原文件。</p><p>确认要继续安装吗？</p>';
					$('#confirm').modal();
					$scope.confirm = package_get_downloadurl;
				} else {
					package_get_downloadurl();
				}
			} else {
				Message.setError('安装失败！'+data.msg);
			}
		}, false, true);
	};
	function package_get_downloadurl() {
		Message.setInfo('正在请求安装文件...');
		Request.get('/sitepackage/getdownloadtask?name='+$scope.curpkg.code+'&version='+$scope.pkgver, function(data){
			if (data.code == 0) {
				$scope.downloadurl = data.data.url;
				$scope.downloadpath = data.data.path;
				$scope.extractpath = data.data.temp;

				Backend.call(
					$scope,
					module,
					'/backend/wget',
					'/backend/wget_'+encodeURIComponent(encodeURIComponent($scope.downloadurl)),
					{
						'url': $scope.downloadurl,
						'path': $scope.downloadpath
					},
					{
						'success': function(data){
							// decompress it
							var zippath = $scope.downloadpath;
							var despath = $scope.extractpath;
							Backend.call(
								$scope,
								module,
								'/backend/decompress',
								'/backend/decompress_'+zippath+'_'+despath, 
								{
									'zippath': zippath,
									'despath': despath
								},
								{
									'success': function(data){
										// move the right folder to site path
										var corepath = $scope.curver.core_path;
										var srcpath = $scope.extractpath+'/'+corepath+'/*';
										var despath = $scope.installpath;
										Backend.call(
											$scope,
											module,
											'/backend/copy',
											'/backend/copy_'+srcpath+'_'+despath, 
											{
												'srcpath': srcpath,
												'despath': despath
											},
											{
												'success': function(data){
													// install ok, remove the temp folder
													Message.setInfo('正在清理安装临时文件...');
													Backend.call(
														$scope,
														module,
														'/backend/remove',
														'/backend/remove_'+$scope.extractpath,
														{
															'paths': $scope.extractpath
														},
														function(){
															// set user.group to apache.apache
															Message.setInfo('正在设置目录权限...');
															Backend.call(
																$scope,
																module,
																'/backend/chown',
																'/backend/chown_'+$scope.installpath, 
																{
																	'paths': $scope.installpath,
																	'user': 'apache',
																	'group': 'apache',
																	'recursively': true
																},
																{
																	'success': function(data){
																		Message.setSuccess($scope.curpkg.name+' v'+$scope.pkgver+' 安装完成！');
																	}
																}
															);
														},
														true
													);
												},
												'error': function(data){
													Message.setError('复制安装文件过程中出现错误，安装取消！')
												}
											}
										);
										
									}
								}
							);
						},
						'error': function(data){
							Message.setError('下载安装包过程中出现错误，安装取消！')
						}
					},
					false
				);
			}
		});

	}
	
	$scope.loadsites = function(){
		if ($scope.nginx_supported) $scope.loadnginx();
		if ($scope.apache_supported) $scope.loadapache();
	}
	
	$scope.nginxloading = false;
	$scope.loadnginx = function(){
		$scope.nginxloading = true;
		Request.post('/operation/nginx', {
			'action': 'getservers'
		}, function(data){
			if (data.code == 0) {
				$scope.servers = data.data;
				$scope.nginxloading = false;
			}
		});
	};

	$scope.loadapache = function(){
	};
	
	$scope.nginx_enableserver = function(ip, port, server_name){
		Request.post('/operation/nginx', {
			'action': 'enableserver',
			'ip': ip,
			'port': port,
			'server_name': server_name
		}, function(data){
			if (data.code == 0) {
				$scope.loadnginx();
			}
		});
	};
	$scope.nginx_disableserver = function(ip, port, server_name){
		Request.post('/operation/nginx', {
			'action': 'disableserver',
			'ip': ip,
			'port': port,
			'server_name': server_name
		}, function(data){
			if (data.code == 0) {
				$scope.loadnginx();
			}
		});
	};
	$scope.nginx_deleteserverconfirm = function(ip, port, server_name){
		$scope.nginx_ip = ip;
		$scope.nginx_port = port;
		$scope.nginx_server_name = server_name;
		$('#nginx_deleteserverconfirm').modal();
	};
	$scope.nginx_deleteserver = function(){
		Request.post('/operation/nginx', {
			'action': 'deleteserver',
			'ip': $scope.nginx_ip,
			'port': $scope.nginx_port,
			'server_name': $scope.nginx_server_name
		}, function(data){
			if (data.code == 0) {
				$scope.loadnginx();
			}
		});
	};
}];

var SiteNginxCtrl = [
'$scope', 'Module', '$routeParams', '$location', 'Request', 'Backend', 'Timeout',
function($scope, Module, $routeParams, $location, Request, Backend, Timeout){
	var section = $routeParams.section;
	var action = section == 'new' ? 'new' : 'edit';
	var site = action == 'edit' ? section.substr(5) : '';
	var server_ip, server_port, server_name;
	if (action == 'edit') {
		site = site.split('_');
		if (site.length == 3) {
			server_ip = site[0];
			server_port = site[1];
			server_name = site[2];
		} else if (site.length == 4 && site[3]=='') {
			server_ip = site[0];
			server_port = site[1];
			server_name = '_';
		} else {
			$location.path('/site');
			return;
		}
	}

	var module = 'site.nginx';
	Module.init(module, action == 'new' ? '新建站点（Nginx）' : '编辑站点（Nginx）');
	$scope.loaded = false;
	$scope.showglobaladv = false;
	$scope.curloc = -1;
	$scope.setloc = function(i){$scope.curloc = i;};
	$scope.action = action;

	var server_tmpl = {
		server_names: [],
		listens: [],
		charset: '',
		index: 'index.html index.htm index.php',
		locations: [],
		limit_rate: '',
		limit_conn: '',
		ssl_crt: '',
		ssl_key: '',
		rewrite_enable: false,
		rewrite_rules: ''
	};
	var server_name_tmpl = {
		'name': '',
		'default_name': false
	};
	var listen_tmpl = {
		'ip': '',
		'port': '80',
		'ssl': false,
		'default_server': false
	};
	var location_tmpl = {
		urlpath: '/',
		engine: 'static',
		'static': {
			root: '/var/www/',
			autocreate: true,
			autoindex: false,
			rewrite_enable: false,
			rewrite_detect_file: true,
			rewrite_rules: ''
		},
		fastcgi: {
			root: '/var/www/',
			autocreate: true,
			fastcgi_pass: '127.0.0.1:9000',
			rewrite_enable: false,
			rewrite_detect_file: true,
			rewrite_rules: ''
		},
		proxy: {
			protocol: 'http',
			host: '',
			realip: true,
			charset: '',
			backends: [],
			balance: 'ip_hash',
			keepalive: '10',
			proxy_cache_enable: false,
			proxy_cache: '',
			proxy_cache_min_uses: '',
			proxy_cache_methods_post: false,
			proxy_cache_key: {
				schema: true,
				host: false,
				proxy_host: true,
				uri: true,
			},
			proxy_cache_valid: [],
			proxy_cache_use_stale: {
				error: false,
				timeout: false,
				invalid_header: false,
				updating: false,
				http_500: false,
				http_502: false,
				http_503: false,
				http_504: false,
				http_404: false
			},
			proxy_cache_lock: false,
			proxy_cache_lock_timeout: '5'
		},
		redirect: {
			url: '',
			type: '301',
			option: 'keep'
		},
		error: {
			code: '404'
		}
	};
	var backend_tmpl = {
		server: '',
		weight: '',
		fail_timeout: '10',
		max_fails: '3'
	};
	var proxy_cache_valid_tmpl = {
		code: 'any',
		time: '1',
		time_unit: 'h'
	};
	$scope.setting = angular.copy(server_tmpl);
	$scope.gen_by_vpsmate = action == 'new' ? true : false;

	var global_rewrite_templates = {
		'301_1': 'rewrite ^ http://example.com$request_uri? permanent',
		'301_2': 'rewrite ^ http://example.com/ permanent',
		'302_1': 'rewrite ^ http://example.com$request_uri? redirect',
		'302_2': 'rewrite ^ http://example.com/ redirect'
	};
	$scope.$watch('rewrite_template', function(value){
		$scope.setting.rewrite_rules = value ? global_rewrite_templates[value] : '';
	});
	
	// check nginx version
	$scope.load = function(){
		// nginx version check may take too long time, so we don't want to wait for it
		if (action == 'new')
			$scope.loaded = true;
		else
			$scope.getserver();

		Backend.call(
			$scope,
			module,
			'/backend/yum_info',
			'/backend/yum_info_nginx',
			{
				'pkg': 'nginx',
				'repo': 'installed'
			}, {
				'success': function(data){
					$scope.nginx_version = data.data[0].version;
				},
				'error': function(data){
					$scope.nginx_version = '';
					//$scope.loaded = true;
				}
			},
			true
		);

		$scope.loadproxycaches();
	};
	
	// load proxy cache list
	$scope.proxy_caches = [];
	$scope.loadproxycaches = function() {
		Request.post('/operation/nginx', {
			'action': 'gethttpsettings',
			'items': 'proxy_cache_path[]'
		}, function(data){
			if (data.code == 0) {
				var proxy_caches = $.browser.msie ? [''] : [];	// temp patch for ie8
				var ps = data.data.proxy_cache_path;
				if (ps) {
					for (var i=0; i<ps.length; i++) {
						proxy_caches.push(ps[i].name);
					}
				}
				$scope.proxy_caches = proxy_caches;
			}
		}, false, true);
	};

	// get server info (in edit mode)
	$scope.getserver = function(quiet){
		Request.post('/operation/nginx', {
			'action': 'getserver',
			'ip': server_ip,
			'port': server_port,
			'server_name': server_name
		}, function(data){
			if (data.code == 0) {
				var d = data.data;
				// init setting
				var s = $scope.setting;
				$scope.gen_by_vpsmate = d._vpsmate;
				for (i in d.server_names) {
					var name = d.server_names[i];
					s.server_names.push({'name': name, 'default_name': name=='_'});
				}
				for (i in d.listens) {
					var listen = d.listens[i];
					var t = angular.copy(listen_tmpl);
					if (typeof listen.ip != 'undefined') t.ip = listen.ip;
					if (typeof listen.port != 'undefined') t.port = listen.port;
					if (typeof listen.ssl != 'undefined') t.ssl = listen.ssl;
					if (typeof listen.default_server != 'undefined') t.default_server = listen.default_server;
					s.listens.push(t);
				}
				if (d.index) s.index = d.index;
				if (d.charset) s.charset = d.charset;
				if (d.limit_rate) s.limit_rate = d.limit_rate;
				if (d.limit_conn) s.limit_conn = d.limit_conn;
				if (d.ssl_crt) s.ssl_crt = d.ssl_crt;
				if (d.ssl_key) s.ssl_key = d.ssl_key;
				if (d.rewrite_rules) {
					s.rewrite_rules = d.rewrite_rules.join('\n');
					if (s.rewrite_rules) s.rewrite_enable = true;
				}
				if (d.locations) {
					for (i in d.locations) {
						var loc = d.locations[i];
						var t = angular.copy(location_tmpl);
						if (typeof loc.urlpath != 'undefined') {
							t.urlpath = loc.urlpath;
							t.oldurlpath = t.urlpath;
						}
						// detect engine
						if (typeof loc.error_code != 'undefined') {
							t.engine = 'error';
							t.error.code = loc.error_code;
						} else if (typeof loc.fastcgi_pass != 'undefined') {
							t.engine = 'fastcgi';
							t.fastcgi.fastcgi_pass = loc.fastcgi_pass;
							if (loc.root) t.fastcgi.root = loc.root;
							t.fastcgi.rewrite_detect_file = loc.rewrite_detect_file ? true : false;
							if (loc.rewrite_rules) {
								t.fastcgi.rewrite_rules = loc.rewrite_rules.join(';\n');
								if (t.fastcgi.rewrite_rules) {
									t.fastcgi.rewrite_rules += ';';
									t.fastcgi.rewrite_enable = true;
								}
							}
						} else if (typeof loc.proxy_protocol != 'undefined') {
							t.engine = 'proxy';
							t.proxy.protocol = loc.proxy_protocol;
							if (typeof loc.proxy_host != 'undefined') t.proxy.host = loc.proxy_host;
							if (typeof loc.proxy_realip != 'undefined') t.proxy.realip = loc.proxy_realip;
							if (typeof loc.proxy_balance != 'undefined') t.proxy.balance = loc.proxy_balance;
							if (typeof loc.proxy_keepalive != 'undefined') t.proxy.keepalive = loc.proxy_keepalive;
							for (i in loc.proxy_backends) {
								var backend = loc.proxy_backends[i];
								var b = angular.copy(backend_tmpl);
								if (typeof backend.server != 'undefined') b.server = backend.server;
								if (typeof backend.weight != 'undefined') b.weight = backend.weight;
								if (typeof backend.fail_timeout != 'undefined') b.fail_timeout = backend.fail_timeout;
								if (typeof backend.max_fails != 'undefined') b.max_fails = backend.max_fails;
								t.proxy.backends.push(b);
							}
							if (typeof loc.proxy_cache != 'undefined') {
								t.proxy.proxy_cache_enable = true;
								t.proxy.proxy_cache = loc.proxy_cache;
								if (typeof loc.proxy_cache_min_uses != 'undefined') t.proxy.proxy_cache_min_uses = loc.proxy_cache_min_uses;
								if (typeof loc.proxy_cache_methods != 'undefined') t.proxy.proxy_cache_methods_post = loc.proxy_cache_methods == 'POST';
								if (typeof loc.proxy_cache_key != 'undefined') {
									var lks = loc.proxy_cache_key.split('$');
									var tks = t.proxy.proxy_cache_key;
									for (var i=0; i<lks.length; i++) {
										if (lks[i] == 'schema') tks.schema = true;
										else if (lks[i] == 'host') tks.host = true;
										else if (lks[i] == 'proxy_host') tks.proxy_host = true;
										else if (lks[i] == 'request_uri') tks.uri = true;
									}
								}
								if (typeof loc.proxy_cache_valid != 'undefined') {
									var valids = loc.proxy_cache_valid;
									for (var i=0; i<valids.length; i++) {
										t.proxy.proxy_cache_valid.push({
											code: valids[i].code,
											time: parseInt(valids[i].time)+'',
											time_unit: valids[i].time.substr(valids[i].time.length-1),
										});
									}
								}
								if (typeof loc.proxy_cache_use_stale != 'undefined') {
									var lts = loc.proxy_cache_use_stale;
									var tts = t.proxy.proxy_cache_use_stale;
									for (var i=0; i<lts.length; i++) {
										if (lts[i] == 'error') tts.error = true;
										else if (lts[i] == 'timeout') tts.timeout = true;
										else if (lts[i] == 'invalid_header') tts.invalid_header = true;
										else if (lts[i] == 'updating') tts.updating = true;
										else if (lts[i] == 'http_500') tts.http_500 = true;
										else if (lts[i] == 'http_502') tts.http_502 = true;
										else if (lts[i] == 'http_503') tts.http_503 = true;
										else if (lts[i] == 'http_504') tts.http_504 = true;
										else if (lts[i] == 'http_404') tts.http_404 = true;
									}
								}
								if (typeof loc.proxy_cache_lock != 'undefined') {
									t.proxy.proxy_cache_lock = loc.proxy_cache_lock;
									if (typeof loc.proxy_cache_lock_timeout != 'undefined')
										t.proxy.proxy_cache_lock_timeout = loc.proxy_cache_lock_timeout;
								}
							}
						} else if (typeof loc.redirect_url != 'undefined') {
							t.engine = 'redirect';
							t.redirect.url = loc.redirect_url;
							if (typeof loc.redirect_type != 'undefined') t.redirect.type = loc.redirect_type;
							if (typeof loc.redirect_option != 'undefined') t.redirect.option = loc.redirect_option;
						} else if (typeof loc.root != 'undefined') {
							t.engine = 'static';
							t['static'].root = loc.root;
							t['static'].rewrite_detect_file = loc.rewrite_detect_file ? true : false;
							if (typeof loc.autoindex != 'undefined') t['static'].autoindex = loc.autoindex;
							if (loc.rewrite_rules) {
								t['static'].rewrite_rules = loc.rewrite_rules.join(';\n');
								if (t['static'].rewrite_rules) {
									t['static'].rewrite_rules += ';';
									t['static'].rewrite_enable = true;
								}
							}
						}
						if (t.proxy.backends.length==0) t.proxy.backends.push(angular.copy(backend_tmpl));
						s.locations.push(t);
					}
				}
				$scope.curloc = 0;
				$scope.loaded = true;
			} else {
				Timeout(function(){
					$location.path('/site');
				}, 1000, module);
			}
		}, false, quiet);
	};
	
	// server name operation
	$scope.deleteservername = function(i){
		$scope.setting.server_names.splice(i, 1);
	};
	$scope.addservername = function(){
		$scope.setting.server_names.push(angular.copy(server_name_tmpl));
	};
	
	// listen operation
	$scope.deletelisten = function(i){
		$scope.setting.listens.splice(i, 1);
	};
	$scope.addlisten = function(){
		$scope.setting.listens.push(angular.copy(listen_tmpl));
	};
	
	// location operation
	$scope.deletelocation = function(i){
		$scope.setting.locations.splice(i, 1);
		$scope.curloc--;
		if ($scope.curloc<0&&$scope.setting.locations.length>0) $scope.curloc = 0;
	};
	$scope.addlocation = function(){
		var locs = $scope.setting.locations;
		locs.splice($scope.curloc+1, 0, angular.copy(location_tmpl));
		$scope.proxy_addbackend($scope.curloc+1);
		$scope.curloc++;
	};
	
	// proxy operation
	$scope.proxy_deletebackend = function(loc_i, i){
		$scope.setting.locations[loc_i].proxy.backends.splice(i, 1);
	};
	$scope.proxy_addbackend = function(loc_i){
		$scope.setting.locations[loc_i].proxy.backends.push(angular.copy(backend_tmpl));
		$scope.proxy_addvalid(loc_i);
	};
	$scope.proxy_deletevalid = function(loc_i, i){
		$scope.setting.locations[loc_i].proxy.proxy_cache_valid.splice(i, 1);
	};
	$scope.proxy_addvalid = function(loc_i){
		$scope.setting.locations[loc_i].proxy.proxy_cache_valid.push(angular.copy(proxy_cache_valid_tmpl));
	};
	
	// automatically set the root path of static and fastcgi engine
	$scope.$watch('setting.server_names[0].name', function(value, oldvalue){
		var server_name = value;
		var old_server_name = oldvalue;
		var locs = $scope.setting.locations;
		for (var i=0; i<locs.length; i++) {
			if (locs[i].urlpath == '/') {
				var prefix = location_tmpl['static'].root;
				var expected_path = prefix + '/' + old_server_name;
				expected_path = expected_path.replace('//', '/');
				if (locs[i]['static'].root == expected_path) {
					var root = prefix + '/' +server_name;
					locs[i]['static'].root = root.replace('//', '/');
				}
				var prefix = location_tmpl.fastcgi.root;
				var expected_path = prefix + '/' + old_server_name;
				expected_path = expected_path.replace('//', '/');
				if (locs[i].fastcgi.root == expected_path) {
					var root = prefix + '/' +server_name;
					locs[i].fastcgi.root = root.replace('//', '/');
				}
			}
		}
	});
	
	// operations when url path change
	$scope.urlpathchange = function(loc) {
		if (loc.urlpath.length==0) loc.urlpath = '/';
		if (loc.engine == 'fastcgi' && loc.fastcgi.rewrite_enable) {
			// parse rewrite rules and automatically replace the path start with the old path
			var r = new RegExp('([\\^\\s])('+(loc.oldurlpath+'/').replace('//', '/').replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')+')', 'gm');
			loc.fastcgi.rewrite_rules = loc.fastcgi.rewrite_rules.replace(r, '$1'+(loc.urlpath+'/').replace('//', '/'));
			loc.oldurlpath = loc.urlpath;
		}
	};
	
	// site folder selector
	$scope.selectstaticfolder = function(i){
		$scope.selector_title = '请选择站点目录';
		$scope.selector.onlydir = true;
		$scope.selector.onlyfile = false;
		$scope.selector.load($scope.setting.locations[i]['static'].root);
		$scope.selector.selecthandler = function(path){
			$('#selector').modal('hide');
			$scope.setting.locations[i]['static'].root = path;
		};
		$('#selector').modal();
	};
	$scope.selectfastcgifolder = function(i){
		$scope.selector_title = '请选择站点目录';
		$scope.selector.onlydir = true;
		$scope.selector.onlyfile = false;
		$scope.selector.load($scope.setting.locations[i].fastcgi.root);
		$scope.selector.selecthandler = function(path){
			$('#selector').modal('hide');
			$scope.setting.locations[i].fastcgi.root = path;
		};
		$('#selector').modal();
	};
	// ssl selector
	$scope.selectsslcrt = function(i){
		$scope.selector_title = '请选择CRT文件（*.crt）';
		$scope.selector.onlydir = false;
		$scope.selector.onlyfile = true;
		$scope.selector.load('/root');
		$scope.selector.selecthandler = function(path){
			$('#selector').modal('hide');
			$scope.setting.ssl_crt = path;
		};
		$('#selector').modal();
	};
	$scope.selectsslkey = function(i){
		$scope.selector_title = '请选择密钥文件（*.key）';
		$scope.selector.onlydir = false;
		$scope.selector.onlyfile = true;
		$scope.selector.load('/root');
		$scope.selector.selecthandler = function(path){
			$('#selector').modal('hide');
			$scope.setting.ssl_key = path;
		};
		$('#selector').modal();
	};
	
	// submit
	$scope.addserver = function(){
		Request.post('/operation/nginx', {
			'action': 'addserver',
			'version': $scope.nginx_version,
			'setting': angular.toJson($scope.setting)
		}, function(data){
			if (data.code == 0) {
				var s = $scope.setting;
				$scope.loaded = false;
				var name = (s.listens[0].ip?s.listens[0].ip:'*')+'_'+s.listens[0].port+'_'+s.server_names[0].name;
				Timeout(function(){
					$location.path('/site/nginx/edit_'+encodeURIComponent(name));
				}, 1000, module);
			}
		});
	};
	$scope.updateserver = function(){
		Request.post('/operation/nginx', {
			'action': 'updateserver',
			'ip': server_ip,
			'port': server_port,
			'server_name': server_name,
			'version': $scope.nginx_version,
			'setting': angular.toJson($scope.setting)
		}, function(data){
			if (data.code == 0) {
				var s = $scope.setting;
				$scope.loaded = false;
				var name = (s.listens[0].ip?s.listens[0].ip:'*')+'_'+s.listens[0].port+'_'+s.server_names[0].name;
				Timeout(function(){
					var new_path = '/site/nginx/edit_'+encodeURIComponent(name);
					if (new_path != $location.path()) $location.path(new_path);
					else $scope.restore();
				}, 1000, module);
			}
		});
	};
	$scope.restore = function(){
		$scope.setting = angular.copy(server_tmpl);
		$scope.getserver();
	};
	
	// initially add
	if (section == 'new') {
		$scope.addservername();
		$scope.addlisten();
		$scope.addlocation();
	}
}];