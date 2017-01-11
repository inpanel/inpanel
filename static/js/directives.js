angular.module('vpsmate.directives', []).
directive('navbar', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$scope', '$rootScope', function($scope, $rootScope){
			$rootScope.navbar_loaded = true;
		}],
		template: '<div class="navbar">\
				<div class="navbar-inner">\
					<div class="container">\
						<button type="button" class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">\
							<span class="icon-bar"></span>\
							<span class="icon-bar"></span>\
							<span class="icon-bar"></span>\
						</button>\
						<a class="brand" href="#/main">VPSMate</a>\
						<div class="nav-collapse collapse">\
							<ul class="nav">\
								<li ng-class="\'active\' | ifmatch:[currentItem,\'main\']"><a href="#/main">首页</a></li>\
								<li ng-class="\'active\' | ifmatch:[currentItem,\'service(\..*)?\']"><a href="#/service">服务管理</a></li>\
								<li ng-class="\'active\' | ifmatch:[currentItem,\'file\']"><a href="#/file">文件管理</a></li>\
								<li ng-class="\'active\' | ifmatch:[currentItem,\'site(\..*)?\']"><a href="#/site">网站管理</a></li>\
								<li ng-class="\'active\' | ifmatch:[currentItem,\'database\']"><a href="#/database">数据库管理</a></li>\
								<!--<li ng-class="\'active\' | ifmatch:[currentItem,\'ftp\']"><a href="#/ftp">FTP管理</a></li>-->\
								<!--<li ng-class="\'active\' | ifmatch:[currentItem,\'secure\']"><a href="#/secure">安全管理</a></li>\
								<li ng-class="\'active\' | ifmatch:[currentItem,\'backup\']"><a href="#/backup">备份管理</a></li>\
								<li ng-class="\'active\' | ifmatch:[currentItem,\'log\']"><a href="#/log">日志管理</a></li>-->\
								<li ng-class="\'active\' | ifmatch:[currentItem,\'task\']"><a href="#/task">计划任务</a></li>\
								<li ng-class="\'active\' | ifmatch:[currentItem,\'utils(\..*)?\']"><a href="#/utils">系统工具</a></li>\
							</ul>\
							<ul class="nav pull-right">\
								<li ng-class="\'active\' | ifmatch:[currentItem,\'setting(\..*)?\']"><a href="#/setting">设置</a></li>\
								<li class="divider-vertical"></li>\
								<li ng-class="\'active\' | ifmatch:[currentItem,\'logout\']"><a href="#/logout">退出</a></li>\
							</ul>\
						</div>\
					</div>\
				</div>\
			</div>',
		replace: true
	};
}).
directive('loading', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$scope', function($scope){
			if (!$scope.loadingText) $scope.loadingText = '模块加载中，请稍候......';
		}],
		template: '<div style="padding:30px 0 10px 30px;">\
			<h6>{{loadingText}}</h6>\
			<div class="progress progress-striped active" style="width:230px">\
			<div class="bar" style="width:100%;"></div>\
			</div></div>',
		replace: true
	};
}).
directive('message', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$scope', '$rootScope', function($scope, $rootScope){
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
		}],
		template: '<div id="{{id}}" style="position:fixed;left:0;bottom:0;width:100%;z-index:100">\
			<div class="container">\
				<div class="alert alert-error" style="display:none;margin-bottom:3px" ng-show="$rootScope.showErrorMsg">\
				<button ng-click="$rootScope.showErrorMsg=false" type="button" class="close">&times;</button>\
				<span ng-bind-html-unsafe="$rootScope.errorMessage"></span></div>\
				<div class="alert alert-success" style="display:none;margin-bottom:3px" ng-show="$rootScope.showSuccessMsg">\
				<button ng-click="$rootScope.showSuccessMsg=false" type="button" class="close">&times;</button>\
				<span ng-bind-html-unsafe="$rootScope.successMessage"></span></div>\
				<div class="alert alert-warning" style="display:none;margin-bottom:3px" ng-show="$rootScope.showWarningMsg">\
				<button ng-click="$rootScope.showWarningMsg=false" type="button" class="close">&times;</button>\
				<span ng-bind-html-unsafe="$rootScope.warningMessage"></span></div>\
				<div class="alert alert-info" style="display:none;margin-bottom:3px" ng-show="$rootScope.showInfoMsg">\
				<button ng-click="$rootScope.showInfoMsg=false" type="button" class="close">&times;</button>\
				<span ng-bind-html-unsafe="$rootScope.infoMessage"></span></div>\
			</div>\
			</div>',
		replace: true
	};
}).
directive('srvminiop', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$scope', function($scope){
			$scope.$scope = $scope.$parent;
		}],
		template: '<div><div class="btn-group" ng-show="$scope.info[\'service.\'+service]">\
					<button class="btn btn-small" ng-class="\'active\' | iftrue:$scope.info[\'service.\'+service].autostart" data-toggle="button" title="自动启动"\
						ng-disabled="$scope.waiting" ng-click="$scope.toggleAutostart(name, service)">\
						<i class="icon-check"></i>\
					</button>\
					<button class="btn btn-small" ng-show="$scope.info[\'service.\'+service].status==\'stopped\'" title="启动" ng-disabled="$scope.waiting"\
						ng-click="$scope.start(name, service)">\
						<i class="icon-play"></i>\
					</button>\
					<button class="btn btn-small" ng-show="$scope.info[\'service.\'+service].status==\'running\'" title="停止" ng-disabled="$scope.waiting"\
						ng-click="$scope.stop(name, service)">\
						<i class="icon-stop"></i>\
					</button>\
					<button class="btn btn-small" ng-disabled="$scope.info[\'service.\'+service].status==\'stopped\'||$scope.waiting" title="重启"\
						ng-click="$scope.restart(name, service)">\
						<i class="icon-refresh"></i>\
					</button>\
					<a class="btn btn-small" href="#/service/{{urlname}}" ng-show="$scope.info[\'service.\'+service]!=null" title="设置">\
						<i class="icon-wrench"></i>\
					</a>\
				</div>\
				<a class="btn btn-small" href="#/service/{{urlname}}" ng-show="!$scope.info[\'service.\'+service]">安装服务</a></div>',
		replace: true
	};
}).
directive('srvbase', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$rootScope', '$scope', 'Request', 'Backend', function($rootScope, $scope, Request, Backend){
			$scope.$scope = $scope.$parent;
			$scope.pkginfo = null;
			
			$scope.$parent.checkVersion = function(){
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_info',
					'/backend/yum_info_'+$scope.pkg,
					{
						'pkg': $scope.pkg,
						'repo': 'installed'
					}, {
						'success': function(data){
							$scope.$parent.pkginfo = $scope.pkginfo = data.data[0];
						},
						'error': function(data){
							$scope.pkginfo = {'name': '获取失败！'};
						}
					},
					true
				);
			};
			
			$scope.toggleAutostart = function(){
				Request.post('/operation/chkconfig', {
					'name': $scope.name,
					'service': $scope.service,
					'autostart': !$scope.$parent.autostart
				}, function(data){
					$scope.$parent.checkInstalled();
				});
			};

			var serviceop = function(action){
				return function(){
					Backend.call(
						$scope.$parent,
						$rootScope.module,
						'/backend/service_'+action,
						'/backend/service_'+action+'_'+$scope.service,
						{
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
		}],
		template: '<table class="table table-button" style="width:600px;">\
				<thead>\
					<tr>\
						<th colspan="2">{{name}} 服务操作</th>\
					</tr>\
				</thead>\
				<tbody>\
					<tr>\
						<td style="width:120px;">当前软件版本：</td>\
						<td>\
							<span ng-show="!pkginfo">正在获取...</span>\
							<span style="display:none" ng-show="pkginfo">\
							{{pkginfo.name}} {{\'v\'+pkginfo.version+\'-\'+pkginfo.release | iftrue:pkginfo.version}} {{"("+pkginfo.from_repo+")" | iftrue:pkginfo.from_repo}}\
							</span>\
						</td>\
					</tr>\
					<tr>\
						<td style="width:120px;">当前服务状态：</td>\
						<td ng-bind-html-unsafe="$scope.status | service.status"></td>\
					</tr>\
					<tr>\
						<td>开机是否启动：</td>\
						<td>\
							<button class="btn btn-small" ng-class="\'active\' | iftrue:$scope.autostart" data-toggle="button"\
								ng-click="toggleAutostart()">\
								<i class="icon-check"></i> 开机自动启动\
							</button>\
						</td>\
					</tr>\
					<tr>\
						<td>启动/停止服务：</td>\
						<td>\
							<button class="btn btn-small" ng-show="$scope.status==\'stopped\'" ng-disabled="$scope.waiting"\
								ng-click="start()">\
								<i class="icon-play"></i> 启动服务\
							</button>\
							<button class="btn btn-small" ng-show="$scope.status==\'running\'" ng-disabled="$scope.waiting"\
								ng-click="stop()">\
								<i class="icon-stop"></i> 停止服务\
							</button>\
							<button class="btn btn-small" ng-disabled="$scope.status==\'stopped\'||$scope.waiting"\
								ng-click="restart()">\
								<i class="icon-refresh"></i> 重启服务\
							</button>\
						</td>\
					</tr>\
				</tbody>\
				</table>',
		replace: true
	};
}).
directive('srvinstall', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Backend', function($rootScope, $scope, Request, Timeout, Backend){
			$scope.$scope = $scope.$parent;

			var repolist = [];
			$scope.installing = false;
			$scope.installMsg = '';
			
			// check repolist
			$scope.startInstall = function(){
				$scope.installMsg = '正在检测软件源...';
				$scope.installing = true;
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_repolist',
					'/backend/yum_repolist',
					{}, {
						'wait': function(data){
							$scope.installMsg = data.msg;
						},
						'success': function(data){
							$scope.installMsg = data.msg;
							repolist = data.data;
							$scope.installRepo();
						},
						'error': function(data){
							$scope.installMsg = data.msg;
							Timeout(function(){$scope.installing = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};
			
			// install expected repolist
			$scope.installRepo = function(){
				var newrepo_found = false;
				for (var i=0; i<$scope.expected_repolist.length; i++) {
					var repo_found = false;
					for (var j=0; j<repolist.length; j++) {
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
						'/backend/yum_installrepo_'+$scope.expected_repolist[i],
						{
							'repo': $scope.expected_repolist[i]
						}, {
							'wait': function(data){
								$scope.installMsg = data.msg;
							},
							'success': function(data){
								$scope.installMsg = data.msg;
								repolist.push($scope.expected_repolist[i]);
								$scope.installRepo();
							},
							'error': function(data){
								$scope.installMsg = data.msg;
								Timeout(function(){$scope.installing = false;}, 3000, $rootScope.module);
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
			$scope.checkVersion = function(){
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_info',
					'/backend/yum_info_'+$scope.pkg,
					{
						'pkg': $scope.pkg
					}, {
						'wait': function(data){
							$scope.installMsg = data.msg;
						},
						'success': function(data){
							$scope.installMsg = data.msg;
							$scope.pkgs = data.data;
							$scope.showVerList = true;
						},
						'error': function(data){
							$scope.installMsg = data.msg;
							Timeout(function(){$scope.installing = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};
			
			// install specified version of pkg in specified repository
			$scope.install = function(repo, name, version, release){
				$scope.installMsg = '开始安装...';
				$scope.showVerList = false;
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_install',
					'/backend/yum_install_'+repo+'_'+name+'_'+version+'_'+release,
					{
						'repo': repo,
						'pkg': name,
						'version': version,
						'release': release
					}, {
						'wait': function(data){
							$scope.installMsg = data.msg;
						},
						'success': function(data){
							$scope.installMsg = data.msg;
							$scope.$parent.activeTabName = 'base';
							Timeout(function(){
								$scope.installing = false;
								$scope.$parent.checkInstalled();
							}, 3000, $rootScope.module);
						},
						'error': function(data){
							$scope.installMsg = data.msg;
							Timeout(function(){$scope.installing = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};

			// uninstall specified version of pkg in specified repository
			$scope.uninstall = function(repo, name, version, release){
				$scope.installMsg = '正在清理...';
				$scope.showVerList = false;
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_uninstall',
					'/backend/yum_uninstall_'+name+'_'+version+'_'+release,
					{
						'repo': repo,
						'pkg': name,
						'version': version,
						'release': release
					}, {
						'wait': function(data){
							$scope.installMsg = data.msg;
						},
						'success': function(data){
							$scope.installMsg = data.msg;
							Timeout(function(){
								$scope.installing = false;
								$scope.$parent.checkInstalled();
							}, 3000, $rootScope.module);
						},
						'error': function(data){
							$scope.installMsg = data.msg;
							Timeout(function(){$scope.installing = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};
		}],
		template: '<div class="well" style="width:600px;display:none" ng-show="!$scope.installed&&!$scope.checking">\
				<div ng-show="!installing">\
					<p>系统检测到 {{name}} 当前尚未安装。</p>\
					<p>是否要开始安装？</p>\
				</div>\
				<div ng-show="installing" ng-bind-html-unsafe="installMsg"></div>\
				<p ng-show="!installing"><button class="btn btn-small" style="margin-top:10px" ng-click="startInstall()">开始安装</button></p>\
				<table class="table table-condensed" style="margin-top:20px;display:none" ng-show="showVerList&&pkgs.length>0">\
					<thead>\
						<tr>\
							<th>版本</th>\
							<th style="width:70px">大小</th>\
							<th style="width:70px">软件源</th>\
							<th style="width:80px"></th>\
						</tr>\
					</thead>\
					<tbody>\
						<tr ng-repeat="pkg in pkgs">\
							<td>{{pkg.name}} v{{pkg.version}}-{{pkg.release}}</td>\
							<td>{{pkg.size}}</td>\
							<td>{{\'已安装\'|iftrue:pkg.repo==\'installed\'}}{{pkg.repo|iftrue:pkg.repo!=\'installed\'}}</td>\
							<td>\
								<button class="btn btn-mini" ng-show="pkg.repo==\'installed\'" ng-click="uninstall(pkg.repo, pkg.name, pkg.version, pkg.release)">清除此版本</button>\
								<button class="btn btn-mini" ng-show="pkg.repo!=\'installed\'" ng-click="install(pkg.repo, pkg.name, pkg.version, pkg.release)">安装此版本</button>\
							</td>\
						</tr>\
					</tbody>\
				</table>\
			</div>',
		replace: true
	};
}).
directive('srvupdate', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Backend', function($rootScope, $scope, Request, Timeout, Backend){
			$scope.$scope = $scope.$parent;

			$scope.updating = false;
			$scope.updateMsg = '';
			
			// check pkg version
			$scope.startUpdate = function(){
				$scope.updating = true;
				$scope.updateMsg = '正在检测当前版本信息...';
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_info',
					'/backend/yum_info_'+$scope.pkg,
					{
						'pkg': $scope.pkg,
						'repo': 'installed'
					}, {
						'wait': function(data){
							$scope.updateMsg = data.msg;
						},
						'success': function(data){
							$scope.updateMsg = data.msg;
							$scope.pkginfo = data.data[0];
							$scope.checkVersion($scope.pkginfo.name);
						},
						'error': function(data){
							$scope.updateMsg = data.msg;
							Timeout(function(){$scope.updating = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};

			// check and list versions of the pkg
			$scope.showVerList = false;
			$scope.checkVersion = function(name){
				$scope.updateMsg = '正在检测新版本...';
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_info',
					'/backend/yum_info_'+name,
					{
						'pkg': name,
						'option': 'update'
					}, {
						'wait': function(data){
							$scope.updateMsg = data.msg;
						},
						'success': function(data){
							$scope.updateMsg = data.msg;
							$scope.pkgs = data.data;
							$scope.showVerList = true;
						},
						'error': function(data){
							$scope.updateMsg = data.msg;
							Timeout(function(){$scope.updating = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};
			
			// update pkg
			$scope.update = function(repo, name, version, release){
				$scope.updateMsg = '开始升级...';
				$scope.showVerList = false;
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_update',
					'/backend/yum_update_'+repo+'_'+name+'_'+version+'_'+release,
					{
						'repo': repo,
						'pkg': name,
						'version': version,
						'release': release
					}, {
						'wait': function(data){
							$scope.updateMsg = data.msg;
						},
						'success': function(data){
							$scope.updateMsg = data.msg;
							$scope.$parent.activeTabName = 'base';
							Timeout(function(){
								$scope.updating = false;
								$scope.$parent.checkInstalled();
							}, 3000, $rootScope.module);
						},
						'error': function(data){
							$scope.updateMsg = data.msg;
							Timeout(function(){$scope.updating = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};
		}],
		template: '<div class="well" style="width:600px;display:none" ng-show="$scope.installed&&!$scope.checking">\
				<div ng-show="!updating">\
					<p>在此检测并查找可用的新版本并升级。</p>\
				</div>\
				<div ng-show="updating" ng-bind-html-unsafe="updateMsg"></div>\
				<p ng-show="!updating"><button class="btn btn-small" style="margin-top:10px" ng-click="startUpdate()">检测新版本</button></p>\
				<table class="table table-condensed" style="margin-top:20px;display:none" ng-show="showVerList&&pkgs.length>0">\
					<thead>\
						<tr>\
							<th>版本</th>\
							<th style="width:70px">大小</th>\
							<th style="width:70px">软件源</th>\
							<th style="width:90px"></th>\
						</tr>\
					</thead>\
					<tbody>\
						<tr ng-repeat="pkg in pkgs">\
							<td>{{pkg.name}} v{{pkg.version}}-{{pkg.release}}</td>\
							<td>{{pkg.size}}</td>\
							<td>{{\'已安装\'|iftrue:pkg.repo==\'installed\'}}{{pkg.repo|iftrue:pkg.repo!=\'installed\'}}</td>\
							<td>\
								<button class="btn btn-mini" ng-show="pkg.repo!=\'installed\'" ng-click="update(pkg.repo, pkg.name, pkg.version, pkg.release)">升级到此版本</button>\
							</td>\
						</tr>\
					</tbody>\
				</table>\
			</div>',
		replace: true
	};
}).
directive('srvext', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Backend', function($rootScope, $scope, Request, Timeout, Backend){
			$scope.$scope = $scope.$parent;

			$scope.operating = false;
			$scope.showMsg = '';

			$scope.start = function(){
				$scope.operating = true;
				$scope.showMsg = '正在检测版本信息...';
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_info',
					'/backend/yum_info_'+$scope.pkg,
					{
						'pkg': $scope.pkg,
						'repo': 'installed'
					}, {
						'wait': function(data){
							$scope.showMsg = data.msg;
						},
						'success': function(data){
							$scope.showMsg = data.msg;
							$scope.pkginfo = data.data[0];
							$scope.checkExt();
						},
						'error': function(data){
							$scope.showMsg = data.msg;
							Timeout(function(){$scope.operating = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};

			// check and list ext of the pkg
			$scope.showExtList = false;
			$scope.checkExt = function(){
				$scope.operating = true;
				$scope.showExtList = false;
				$scope.showMsg = '正在检测扩展...';
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_ext_info',
					'/backend/yum_ext_info_'+$scope.pkginfo.name,
					{
						'pkg': $scope.pkginfo.name
					}, {
						'wait': function(data){
							$scope.showMsg = data.msg;
						},
						'success': function(data){
							$scope.showMsg = data.msg;
							$scope.exts = data.data;
							$scope.showExtList = true;
						},
						'error': function(data){
							$scope.showMsg = data.msg;
							Timeout(function(){$scope.operating = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};
			
			// install specified version of ext in specified repository
			$scope.install = function(repo, name, version, release){
				$scope.showMsg = '开始安装...';
				$scope.showExtList = false;
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_install',
					'/backend/yum_install_'+repo+'_'+$scope.pkginfo.name+'_'+name+'_'+version+'_'+release,
					{
						'repo': repo,
						'pkg': $scope.pkginfo.name,
						'ext': name,
						'version': version,
						'release': release
					}, {
						'wait': function(data){
							$scope.showMsg = data.msg;
						},
						'success': function(data){
							$scope.showMsg = data.msg;
							Timeout(function(){
								$scope.operating = false;
								$scope.checkExt();
							}, 3000, $rootScope.module);
						},
						'error': function(data){
							$scope.showMsg = data.msg;
							Timeout(function(){$scope.operating = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};

			// uninstall specified version of ext in specified repository
			$scope.uninstall = function(repo, name, version, release){
				$scope.showMsg = '正在删除...';
				$scope.showExtList = false;
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_uninstall',
					'/backend/yum_uninstall_'+$scope.pkginfo.name+'_'+name+'_'+version+'_'+release,
					{
						'repo': repo,
						'pkg': $scope.pkginfo.name,
						'ext': name,
						'version': version,
						'release': release
					}, {
						'wait': function(data){
							$scope.showMsg = data.msg;
						},
						'success': function(data){
							$scope.showMsg = data.msg;
							Timeout(function(){
								$scope.operating = false;
								$scope.checkExt();
							}, 3000, $rootScope.module);
						},
						'error': function(data){
							$scope.showMsg = data.msg;
							Timeout(function(){$scope.operating = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};
		}],
		template: '<div class="well" style="width:600px;display:none" ng-show="$scope.installed&&!$scope.checking">\
				<div ng-show="!operating">\
					<p>点击下面的按钮检测扩展安装情况。</p>\
				</div>\
				<div ng-show="operating" ng-bind-html-unsafe="showMsg"></div>\
				<p ng-show="!operating"><button class="btn btn-small" style="margin-top:10px" ng-click="start()">检测扩展</button></p>\
				<table class="table table-condensed" style="margin-top:20px;display:none" ng-show="showExtList&&exts.length>0">\
					<thead>\
						<tr>\
							<th>扩展名称</th>\
							<th>版本</th>\
							<th style="width:70px">软件源</th>\
							<th style="width:90px"></th>\
						</tr>\
					</thead>\
					<tbody>\
						<tr ng-repeat="ext in exts">\
							<td>{{ext.name}}</td>\
							<td>{{ext.version}}-{{ext.release}}</td>\
							<td>{{\'已安装\'|iftrue:ext.repo==\'installed\'}}{{ext.repo|iftrue:ext.repo!=\'installed\'}}</td>\
							<td>\
								<button class="btn btn-mini" ng-show="ext.repo==\'installed\'" ng-click="uninstall(ext.repo, ext.name, ext.version, ext.release)">删除扩展</button>\
								<button class="btn btn-mini" ng-show="ext.repo!=\'installed\'" ng-click="install(ext.repo, ext.name, ext.version, ext.release)">安装该扩展</button>\
							</td>\
						</tr>\
					</tbody>\
				</table>\
			</div>',
		replace: true
	};
}).
directive('srvuninstall', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$rootScope', '$scope', 'Request', 'Timeout', 'Backend', function($rootScope, $scope, Request, Timeout, Backend){
			$scope.$scope = $scope.$parent;

			$scope.uninstalling = false;
			$scope.uninstallMsg = '';
			
			// check pkg version
			$scope.startUninstall = function(){
				$scope.uninstallMsg = '开始卸载...';
				$scope.uninstalling = true;
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_info',
					'/backend/yum_info_'+$scope.pkg,
					{
						'pkg': $scope.pkg,
						'repo': 'installed'
					}, {
						'wait': function(data){
							$scope.uninstallMsg = data.msg;
						},
						'success': function(data){
							$scope.uninstallMsg = data.msg;
							$scope.pkginfo = data.data[0];
							$scope.showVersion = true;
						},
						'error': function(data){
							$scope.uninstallMsg = data.msg;
							Timeout(function(){$scope.uninstalling = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};
			
			// uninstall specified version of pkg in specified repository
			$scope.uninstall = function(repo, name, version, release){
				$scope.uninstallMsg = '正在卸载...';
				$scope.showVersion = false;
				Backend.call(
					$scope.$parent,
					$rootScope.module,
					'/backend/yum_uninstall',
					'/backend/yum_uninstall_'+name+'_'+version+'_'+release,
					{
						'repo': repo,
						'pkg': name,
						'version': version,
						'release': release
					}, {
						'wait': function(data){
							$scope.uninstallMsg = data.msg;
						},
						'success': function(data){
							$scope.uninstallMsg = data.msg;
							Timeout(function(){
								$scope.uninstalling = false;
								$scope.$parent.checkInstalled();
							}, 3000, $rootScope.module);
						},
						'error': function(data){
							$scope.uninstallMsg = data.msg;
							Timeout(function(){$scope.uninstalling = false;}, 3000, $rootScope.module);
						}
					},
					true
				);
			};
		}],
		template: '<div class="well" style="width:600px;" ng-show="$scope.installed&&!$scope.checking">\
				<div ng-show="!uninstalling">\
					<p>确定要卸载 {{name}} 吗？</p>\
				</div>\
				<div ng-show="uninstalling" ng-bind-html-unsafe="uninstallMsg"></div>\
				<p ng-show="!uninstalling"><button class="btn btn-small" style="margin-top:10px" ng-click="startUninstall()">开始卸载</button></p>\
				<table class="table table-condensed" style="margin-top:20px;display:none" ng-show="showVersion">\
					<thead>\
						<tr><th colspan="2">请确认要卸载的软件信息：</th></tr>\
					</thead>\
					<tbody>\
						<tr><td style="width:80px">名称：</td><td>{{pkginfo.name}}</td></tr>\
						<tr><td>版本：</td><td>{{pkginfo.version}}-{{pkginfo.release}}</td></tr>\
						<tr><td>大小：</td><td>{{pkginfo.size}}</td></tr>\
						<tr ng-show="pkginfo.from_repo"><td>软件源：</td><td>{{pkginfo.from_repo}}</td></tr>\
					</tbody>\
				</table>\
				<p ng-show="showVersion"><button class="btn btn-mini" ng-click="uninstall(pkginfo.repo, pkginfo.name, pkginfo.version, pkginfo.release)">确认并卸载</button>\
			</div>',
		replace: true
	};
}).
directive('srvfile', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$scope', function($scope){
		}],
		template: '\
			<table class="table table-button" style="width:600px;">\
				<tbody>\
					<tr class="warning">\
						<td colspan="3" class="text-error">注意：如果您没有配置文件修改经验，请勿随意修改，否则可能导致服务无法启动。</td>\
					</tr>\
					<tr ng-repeat="item in items">\
						<td style="width:120px;">{{item.name}}</td>\
						<td>\
							<i class="icon-folder-open" ng-show="item.isdir"></i>\
							<i class="icon-file" ng-show="item.isfile"></i>\
							{{item.path}}\
						</td>\
						<td style="width:100px">\
							<a class="btn btn-small" href="#/file?path={{item.path}}" ng-show="item.isdir">\
								打开 <i class="icon-chevron-right"></i>\
							</a>\
							<a class="btn btn-small" href="#/file?file={{item.path}}" ng-show="item.isfile">\
								打开 <i class="icon-chevron-right"></i>\
							</a>\
						</td>\
					</tr>\
				</tbody>\
			</table>',
		replace: true
	};
}).
directive('srvlog', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$scope', function($scope){
		}],
		template: '\
			<table class="table table-button" style="width:600px;">\
				<tbody>\
					<tr class="warning">\
						<td colspan="3" class="text-error">注意：尽量不要对日志文件进行修改，否则可能导致新日志无法写入。</td>\
					</tr>\
					<tr ng-repeat="item in items">\
						<td style="width:120px;">{{item.name}}</td>\
						<td>\
							<i class="icon-folder-open" ng-show="item.isdir"></i>\
							<i class="icon-file" ng-show="item.isfile"></i>\
							{{item.path}}\
						</td>\
						<td style="width:100px">\
							<a class="btn btn-small" href="#/file?path={{item.path}}" ng-show="item.isdir">\
								打开 <i class="icon-chevron-right"></i>\
							</a>\
							<a class="btn btn-small" href="#/file?file={{item.path}}" ng-show="item.isfile">\
								打开 <i class="icon-chevron-right"></i>\
							</a>\
						</td>\
					</tr>\
				</tbody>\
			</table>',
		replace: true
	};
}).
directive('selector', function(){
	return {
		restrict: 'A',
		transclude: true,
		scope: {},
		controller: ['$scope', 'Request', function($scope, Request){
			$scope.$scope = $scope.$parent;
			$scope.onlydir = true;
			$scope.onlyfile = true;
			$scope.path = '/';
			var parse_path = function(){
				// parse dir to array
				if (!$scope.curpath) return;
				var pathnames = $scope.curpath.split('/');
				var pathinfos = [];
				for (var i=1; i<pathnames.length; i++) {
					if (!pathnames[i]) continue;
					var fullpath = pathnames[i-1]+'/'+pathnames[i];
					pathinfos.push({
						'name': pathnames[i],
						'path': fullpath
					});
					pathnames[i] = fullpath;
				}
				$scope.pathinfos = pathinfos;
			};
			$scope.load = function(path){
				if ($scope.onlyfile) {
					$scope.otherdir = true;
					$scope.listdir(path);
				} else {
					$scope.otherdir = false;
					$scope.path = path;
				}
			};
			$scope.listdir = function(path){
				if (path) $scope.path = path;
				if (!$scope.path)
					$scope.path = '/root';
				else if ($scope.path != '/' && $scope.path.substr(-1) == '/')
					$scope.path = $scope.path.substr(0, $scope.path.length-1);
				$scope.path = $scope.path.replace('//', '/');

				var curpath = $scope.path;
				Request.post('/operation/file', {
					'action': 'listdir',
					'path': curpath,
					'showhidden': false,
					'remember': false,
					'onlydir': $scope.onlydir
				}, function(data){
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
		}],
		template: '<div>\
			<div ng-show="onlydir&&!onlyfile&&!otherdir">\
				<p>当前目录为：{{path}}</p>\
				<p>\
					<button class="btn" ng-click="selecthandler(path)">选择当前目录</button>\
					<button class="btn" ng-click="otherdir=true;listdir(path)">选择其它目录</button>\
				</p>\
			</div>\
			<div ng-show="otherdir">\
			<ul class="breadcrumb" style="margin-bottom:0">\
				<li><a ng-click="listdir(\'/\')">根目录</a> <span class="divider">/</span></li>\
				<li ng-repeat="pathinfo in pathinfos" ng-show="pathinfos.length>0"><a ng-click="listdir(pathinfo.path)">{{pathinfo.name}}</a> <span class="divider">/</span></li>\
				<li><button class="btn btn-mini" ng-show="onlydir" ng-click="selecthandler(curpath)">选取该目录</button></li>\
			</ul>\
			<table class="table table-condensed table-hover">\
				<thead>\
					<tr>\
						<th></th>\
						<th style="width:80px"></th>\
					</tr>\
				</thead>\
				<tbody>\
					<tr ng-repeat="item in items">\
						<td>\
							<i class="icon-folder-open" title="文件夹" ng-show="item.isdir"></i>\
							<i class="icon-file" title="文件" ng-show="item.isreg"></i>\
							<i class="icon-asterisk" title="链接" ng-show="item.islnk&&(item.link_isdir||item.link_isreg)"></i>\
							<i class="icon-ban-circle" title="未知" ng-show="!item.isdir&&!item.isreg&&(!item.islnk||(item.islnk&&!item.link_isdir&&!item.link_isreg))"></i>\
							<a class="black" ng-click="listdir(curpath_pre+\'/\'+item.name)" ng-show="item.isdir||(item.islnk&&item.link_isdir)">{{item.name}}</a>\
							<a class="black" ng-show="item.isreg||(item.islnk&&!item.link_isdir)">{{item.name}}</a>\
							<span class="text-info" ng-show="item.islnk">-> {{item.linkto}}</span>\
						</td>\
						<td>\
							<button class="btn btn-mini" ng-show="onlydir&&(item.isdir||(item.islnk&&item.link_isdir))" ng-click="selecthandler(curpath_pre+\'/\'+item.name)">选取该目录</button>\
							<button class="btn btn-mini" ng-show="onlyfile&&(item.isreg||(item.islnk&&item.link_isreg))" ng-click="selecthandler(curpath_pre+\'/\'+item.name)">选取该文件</button>\
						</td>\
					</tr>\
				</tbody>\
			</table>\
			</div>',
		replace: true
	};
}).
directive('autofocus', function(){
	return function($scope, element){
		element[0].focus();
	};
});