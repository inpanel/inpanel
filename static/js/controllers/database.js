var DatabaseCtrl = [
'$scope', 'Module', '$rootScope', 'Request', 'Message', 'Backend',
function($scope, Module, $rootScope, Request, Message, Backend){
	var module = 'database';
	Module.init(module, '数据库管理');
	$scope.loaded = false;

	var section = Module.getSection();
	$scope.has_dbserver = false;
	$scope.mysql_supported = false;
	
	$scope.load = function(){
		Request.get('/query/service.mysqld', function(data){
			if (data['service.mysqld'] && data['service.mysqld'].status) $scope.mysql_supported = true;
			$scope.has_dbserver = $scope.mysql_supported;
			if ($scope.has_dbserver) {
				if (section) {
					if (section == 'mysqld' && $scope.mysql_supported)
						Module.setSection('mysqld');
					else
						Module.setSection($scope.mysql_supported ? 'mysql' : 'mysql');
				} else {
					Module.setSection($scope.mysql_supported ? 'mysql' : 'mysql');
				}
			}
			$scope.loaded = true;
		});
	};
	
	$scope.validate_password = function(){
		$scope.processing = true;
		Request.post('/operation/mysql', {
			'action': 'checkpwd',
			'password': $rootScope.$mysql.password
		}, function(data){
			if (data.code == 0) {
				$rootScope.$mysql.password_validated = true;
				$scope.loaddbs();
				$scope.loadusers();
			}
			$scope.processing = false;
		});
	};
	$scope.dbloading = true;
	$scope.loaddbs = function(){
		$scope.dbloading = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_databases',
			'/backend/mysql_databases',
			{
				'password': $rootScope.$mysql.password
			}, {
				'success': function(data){
					$scope.dbs = data.data;
					$scope.dbloading = false;
				},
				'error': function(){
					$scope.dbloading = false;
				}
			}
		);
	};
	$scope.userloading = true;
	$scope.loadusers = function(){
		$scope.userloading = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_users',
			'/backend/mysql_users',
			{
				'password': $rootScope.$mysql.password
			}, {
				'success': function(data){
					$scope.users = data.data;
					$scope.userloading = false;
				},
				'error': function(){
					$scope.userloading = false;
				}
			}
		);
	};
	
	if ($rootScope.$mysql.password_validated) {
		$scope.loaddbs();
		$scope.loadusers();
	}
}];

var DatabaseMySQLNewDBCtrl = [
'$scope', 'Module', '$rootScope', '$location', 'Request', 'Message', 'Backend',
function($scope, Module, $rootScope, $location, Request, Message, Backend){
	var module = 'database.mysql.db.new';
	Module.init(module, '新建数据库');
	$scope.loaded = true;

	$scope.collation = 'utf8_general_ci';
	$scope.validate_password = function(){
		$scope.processing = true;
		Request.post('/operation/mysql', {
			'action': 'checkpwd',
			'password': $rootScope.$mysql.password
		}, function(data){
			if (data.code == 0) {
				$rootScope.$mysql.password_validated = true;
			}
			$scope.processing = false;
		});
	};
	$scope.newdb = function(){
		$scope.processing = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_create',
			'/backend/mysql_create_'+$scope.dbname,
			{
				'password': $rootScope.$mysql.password,
				'dbname': $scope.dbname,
				'collation': $scope.collation
			}, {
				'success': function(data){
					$location.path('/database/mysql/db/edit/'+encodeURIComponent($scope.dbname));
					$scope.processing = false;
				},
				'error': function(){
					$scope.processing = false;
				}
			}
		);
	};
}];

var DatabaseMySQLEditDBCtrl = [
'$scope', 'Module', '$rootScope', '$routeParams', '$location', 'Request', 'Message', 'Backend',
function($scope, Module, $rootScope, $routeParams, $location, Request, Message, Backend){
	var section = $routeParams.section;
	$scope.dbname = decodeURIComponent(section);

	var module = 'database.mysql.db.edit';
	Module.init(module, '管理数据库 '+$scope.dbname);
	Module.initSection('users');
	$scope.loaded = true;

	$scope.validate_password = function(){
		$scope.processing = true;
		Request.post('/operation/mysql', {
			'action': 'checkpwd',
			'password': $rootScope.$mysql.password
		}, function(data){
			if (data.code == 0) {
				$rootScope.$mysql.password_validated = true;
				$scope.loaddbinfo();
			}
			$scope.processing = false;
		});
	};

	$scope.dbloading = true;
	$scope.loaddbinfo = function(){
		$scope.dbloading = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_dbinfo',
			'/backend/mysql_dbinfo_'+$scope.dbname,
			{
				'password': $rootScope.$mysql.password,
				'dbname': $scope.dbname
			}, {
				'success': function(data){
					$scope.dbinfo = data.data;
					$scope.dbloading = false;
					$scope.loadusers();
				},
				'error': function(){
					$scope.dbloading = false;
				}
			}
		);
	};
	
	$scope.userloading = true;
	$scope.loadusers = function(){
		$scope.userloading = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_users',
			'/backend/mysql_users_'+$scope.dbname,
			{
				'password': $rootScope.$mysql.password,
				'dbname': $scope.dbname
			}, {
				'success': function(data){
					$scope.users = data.data;
					$scope.userloading = false;
				},
				'error': function(){
					$scope.userloading = false;
				}
			}
		);
	};
	
	$scope.setcollation = function(){
		$scope.processing = true;
		Request.post('/operation/mysql', {
			'action': 'alter_database',
			'password': $rootScope.$mysql.password,
			'dbname': $scope.dbname,
			'collation': $scope.dbinfo.collation
		}, function(){
			$scope.processing = false;
		});
	};
	$scope.rename = function(){
		$scope.processing = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_rename',
			'/backend/mysql_rename_'+$scope.dbname,
			{
				'password': $rootScope.$mysql.password,
				'dbname': $scope.dbname,
				'newname': $scope.dbinfo.name
			}, {
				'success': function(data){
					$location.path('/database/mysql/db/edit/'+encodeURIComponent($scope.dbinfo.name));
					$scope.processing = false;
				},
				'error': function(){
					$scope.processing = false;
				}
			}
		);
	};
	$scope.selectexportfolder = function(){
		$scope.selector.onlydir = true;
		$scope.selector.onlyfile = false;
		$scope.selector.load($scope.exportpath ? $scope.exportpath : '/root');
		$scope.selector.selecthandler = function(path){
			$('#selector').modal('hide');
			$scope.exportpath = path;
		};
		$('#selector').modal();
	};
	$scope.exportdb = function(){
		$scope.processing = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_export',
			'/backend/mysql_export_'+$scope.dbname,
			{
				'password': $rootScope.$mysql.password,
				'dbname': $scope.dbname,
				'path': $scope.exportpath
			}, function(data){
				$scope.processing = false;
			}
		);
	};
	$scope.dropdb = function(){
		$scope.processing = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_drop',
			'/backend/mysql_drop_'+$scope.dbname,
			{
				'password': $rootScope.$mysql.password,
				'dbname': $scope.dbname
			}, function(data){
				if (data.code == 0) {
					$location.path('/database');
					$location.search('s', 'mysql');
				}
				$scope.processing = false;
			}
		);
	};

	if ($rootScope.$mysql.password_validated) {
		$scope.loaddbinfo();
	}
}];

var DatabaseMySQLNewUserCtrl = [
'$scope', 'Module', '$rootScope', '$location', 'Request', 'Message', 'Backend',
function($scope, Module, $rootScope, $location, Request, Message, Backend){
	var module = 'database.mysql.user.new';
	Module.init(module, '添加新用户');
	$scope.loaded = true;
	
	$scope.dbname = Module.getParam('dbname');

	$scope.validate_password = function(){
		$scope.processing = true;
		Request.post('/operation/mysql', {
			'action': 'checkpwd',
			'password': $rootScope.$mysql.password
		}, function(data){
			if (data.code == 0) {
				$rootScope.$mysql.password_validated = true;
			}
			$scope.processing = false;
		});
	};
	$scope.newuser = function(){
		if (!$scope.emptypassword) {
			if ($scope.password != $scope.passwordc) {
				Message.setError('新密码和确认密码不一致！');
				return;
			}
		}
		var username = $scope.user+'@'+$scope.host;
		$scope.processing = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_createuser',
			'/backend/mysql_createuser_'+username,
			{
				'password': $rootScope.$mysql.password,
				'user': $scope.user,
				'host': $scope.host,
				'pwd': $scope.emptypassword?'':$scope.password
			}, {
				'success': function(data){
					$location.path('/database/mysql/user/edit/'+encodeURIComponent(username));
					if ($scope.dbname) $location.search('dbname', $scope.dbname);
					$scope.processing = false;
				},
				'error': function(){
					$scope.processing = false;
				}
			}
		);
	};
	$scope.genpassword = function(){
		// REF: http://stackoverflow.com/questions/9719570/generate-random-password-string-with-requirements-in-javascript
		var chars = "ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz";
		var string_length = 16;
		var randomstring = '';
		var charCount = 0;
		var numCount = 0;
		for (var i=0; i<string_length; i++) {
			// If random bit is 0, there are less than 3 digits already saved, and there are not already 5 characters saved, generate a numeric value. 
			if((Math.floor(Math.random() * 2) == 0) && numCount < 3 || charCount >= 5) {
				var rnum = Math.floor(Math.random() * 10);
				randomstring += rnum;
				numCount += 1;
			} else {
				// If any of the above criteria fail, go ahead and generate an alpha character from the chars string
				var rnum = Math.floor(Math.random() * chars.length);
				randomstring += chars.substring(rnum,rnum+1);
				charCount += 1;
			}
		}
		$scope.randpassword = $scope.password = $scope.passwordc = randomstring;
	};
}];

var DatabaseMySQLEditUserCtrl = [
'$scope', 'Module', '$rootScope', '$routeParams', '$location', 'Request', 'Message', 'Backend',
function($scope, Module, $rootScope, $routeParams, $location, Request, Message, Backend){
	var section = $routeParams.section;
	$scope.username = decodeURIComponent(section);
	var fs = $scope.username.split('@');
	$scope.user = fs[0];
	$scope.host = fs[1];

	var module = 'database.mysql.user.edit';
	Module.init(module, '管理用户 '+$scope.username);
	Module.initSection('privs');
	$scope.loaded = true;

	$scope.validate_password = function(){
		$scope.processing = true;
		Request.post('/operation/mysql', {
			'action': 'checkpwd',
			'password': $rootScope.$mysql.password
		}, function(data){
			if (data.code == 0) {
				$rootScope.$mysql.password_validated = true;
				$scope.loadprivs();
				$scope.loaddbs();
			}
			$scope.processing = false;
		});
	};
	
	$scope.privsloading = true;
	$scope.loadprivs = function(){
		$scope.privsloading = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_userprivs',
			'/backend/mysql_userprivs_'+$scope.username,
			{
				'password': $rootScope.$mysql.password,
				'username': $scope.username
			}, {
				'success': function(data){
					$scope.privs = data.data;
					$scope.privsloading = false;
					// edit or create new privs
					var dbname = Module.getParam('dbname');
					var privtype = Module.getParam('privtype');
					if (dbname) {
						$scope.privs_dbname = dbname;
						$scope.editprivs(false, privtype);
					}
				},
				'error': function(){
					$scope.privsloading = false;
				}
			}
		);
	};
	
    $scope.$watch('selectall', function(value) {
        angular.forEach($scope.curprivs, function(priv, key) {
            if (key.indexOf('_priv') > 0) $scope.curprivs[key] = value ? 'Y' : 'N';
        });
    });
	var priv_tmpl = {
		'Select_priv': 'N',
		'Insert_priv': 'N',
		'Update_priv': 'N',
		'Delete_priv': 'N',
		'Create_priv': 'N',
		'Alter_priv': 'N',
		'Index_priv': 'N', 
		'Drop_priv': 'N',
		'Create_tmp_table_priv': 'N',
		'Show_view_priv': 'N', 
		'Create_routine_priv': 'N',
		'Alter_routine_priv': 'N',
		'Execute_priv': 'N',
		'Create_view_priv': 'N',
		'Event_priv': 'N',
		'Trigger_priv': 'N',
		'Grant_priv': 'N',
		'Lock_tables_priv': 'N', 
		'References_priv': 'N'
	};
	$scope.editprivs = function(privs, privtype){
		if (privtype == 'global') {
			$scope.orgprivs = $scope.privs.global;
			$scope.curprivs = angular.copy($scope.privs.global);
		} else {
			if (!privs) {
				if (!$scope.privs_dbname) return;
				// check if the dbname already exists
				var dbfound = false;
				for (var i=0; i<$scope.privs.bydb.length; i++) {
					if ($scope.privs.bydb[i].Db == $scope.privs_dbname) {
						$scope.orgprivs = $scope.privs.bydb[i];
						$scope.curprivs = angular.copy($scope.privs.bydb[i])
						dbfound = true;
						break;
					}
				}
				if (!dbfound) {
					$scope.orgprivs = null;
					$scope.curprivs = angular.copy(priv_tmpl);
					$scope.curprivs.Db = $scope.privs_dbname;
					$scope.curprivs.flag = 'new';
				}
			} else {
				$scope.orgprivs = privs;
				$scope.curprivs = angular.copy(privs);
			}
		}
		if (!$scope.curprivs.Db)
			$scope.privsedit_title = '设置 '+$scope.username+' 的全局权限';
		else
			$scope.privsedit_title = '设置 '+$scope.username+' 在数据库 '+$scope.curprivs.Db+' 的权限';
		$('#privsedit').modal();
	};
	
	$scope.updateprivs = function(){
		Backend.call(
			$scope,
			module,
			'/backend/mysql_updateuserprivs',
			'/backend/mysql_updateuserprivs_'+encodeURIComponent($scope.username+($scope.curprivs.Db?'_'+$scope.curprivs.Db:'')),
			{
				'password': $rootScope.$mysql.password,
				'username': $scope.username,
				'privs': angular.toJson($scope.curprivs),
				'dbname': $scope.curprivs.Db
			}, {
				'success': function(data){
					if ($scope.curprivs.flag == 'new') {
						// insert to the privs list
						$scope.privs.bydb.push($scope.curprivs);
					} else {
						// just update this item
						angular.copy($scope.curprivs, $scope.orgprivs);
					}
					// return to database management
					var dbname = Module.getParam('dbname');
					if (dbname) {
						$location.path('/database/mysql/db/edit/'+encodeURIComponent(dbname));
					}
				}
			}
		);
	};

	$scope.loaddbs = function(){
		$scope.dbloading = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_databases',
			'/backend/mysql_databases',
			{
				'password': $rootScope.$mysql.password
			}, {
				'success': function(data){
					$scope.dbs = data.data;
				}
			},
			true
		);
	};
	
	$scope.setpassword = function(){
		if (!$scope.emptypassword) {
			if ($scope.newpassword != $scope.newpasswordc) {
				Message.setError('新密码和确认密码不一致！');
				return;
			}
		}
		$scope.processing = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_setuserpassword',
			'/backend/mysql_setuserpassword_'+$scope.username,
			{
				'password': $rootScope.$mysql.password,
				'username': $scope.username,
				'pwd': $scope.emptypassword?'':$scope.newpassword
			}, {
				'success': function(data){
					$scope.processing = false;
					if ($scope.username == 'root@localhost') { 
						// reset cached mysql password
						$rootScope.$mysql = {
							'password': '',
							'password_validated': false
						};
					}
				},
				'error': function(){
					$scope.processing = false;
				}
			}
		);
	};
	
	$scope.dropuser = function(){
		$scope.processing = true;
		Backend.call(
			$scope,
			module,
			'/backend/mysql_dropuser',
			'/backend/mysql_dropuser_'+$scope.username,
			{
				'password': $rootScope.$mysql.password,
				'username': $scope.username
			}, function(data){
				if (data.code == 0) {
					$location.path('/database');
					$location.search('s', 'mysql');
				}
				$scope.processing = false;
			}
		);
	};

	if ($rootScope.$mysql.password_validated) {
		$scope.loadprivs();
		$scope.loaddbs();
	}	
}];