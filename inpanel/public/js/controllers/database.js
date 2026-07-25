var DatabaseCtrl = [
    '$scope', 'Module', '$rootScope', 'Request', 'Message', 'Task',
    function($scope, Module, $rootScope, Request, Message, Task) {
        var module = 'database';
        Module.init(module, '数据库管理');
        $scope.loaded = false;

        var section = Module.getSection();
        $scope.has_dbserver = false;
        $scope.mysql_supported = false;
        $scope.redis_supported = false;
        $scope.processing = false;

        // =============================================================
        // 初始化加载：检测 MySQL 和 Redis
        // =============================================================
        $scope.load = function() {
            var checked = 0;
            var totalCheck = 2;
            function checkDone() {
                checked++;
                if (checked >= totalCheck) {
                    $scope.has_dbserver = $scope.mysql_supported || $scope.redis_supported;
                    if ($scope.has_dbserver) {
                        if (section) {
                            var validSections = [];
                            if ($scope.mysql_supported) validSections.push('mysql');
                            if ($scope.redis_supported) validSections.push('redis');
                            if (validSections.indexOf(section) >= 0) {
                                Module.setSection(section);
                            } else {
                                Module.setSection(validSections[0]);
                            }
                        } else {
                            Module.setSection($scope.mysql_supported ? 'mysql' : ($scope.redis_supported ? 'redis' : 'mysql'));
                        }
                    }
                    $scope.loaded = true;
                }
            }
            Request.get('/api/service/detail/mysqld', function(data) {
                if (data.code === 0 && data.data) $scope.mysql_supported = true;
                checkDone();
            });
            Request.get('/api/service/detail/redis', function(data) {
                if (data.code === 0 && data.data) $scope.redis_supported = true;
                checkDone();
            });
        };

        // =============================================================
        // MySQL 部分
        // =============================================================
        $scope.validate_password = function() {
            $scope.processing = true;
            Request.post('/api/operation/mysql', {
                'action': 'checkpwd',
                'password': $rootScope.$mysql.password
            }, function(data) {
                if (data.code == 0) {
                    $rootScope.$mysql.password_validated = true;
                    $scope.loaddbs();
                    $scope.loadusers();
                }
                $scope.processing = false;
            });
        };
        $scope.dbloading = true;
        $scope.loaddbs = function() {
            $scope.dbloading = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.databases',
                '/api/task/mysql.databases', {
                    'password': $rootScope.$mysql.password
                }, {
                    'success': function(data) {
                        $scope.dbs = data.data;
                        $scope.dbloading = false;
                    },
                    'error': function() {
                        $scope.dbloading = false;
                    }
                }
            );
        };
        $scope.userloading = true;
        $scope.loadusers = function() {
            $scope.userloading = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.users',
                '/api/task/mysql.users', {
                    'password': $rootScope.$mysql.password
                }, {
                    'success': function(data) {
                        $scope.users = data.data;
                        $scope.userloading = false;
                    },
                    'error': function() {
                        $scope.userloading = false;
                    }
                }
            );
        };

        if ($rootScope.$mysql.password_validated) {
            $scope.loaddbs();
            $scope.loadusers();
        }

        // =============================================================
        // Redis 部分
        // =============================================================
        if (!$rootScope.$redis) {
            $rootScope.$redis = {
                host: '127.0.0.1',
                port: '6379',
                password: '',
                connected: false
            };
        }

        $scope.redisLoading = { info: false, dbs: false, detail: false, key: false };
        $scope.redisInfo = null;
        $scope.redisDbs = [];
        $scope.redisDetail = { db: null, keys: null, keyInfo: null, keyCount: 0 };

        $scope.redis_connect = function() {
            $scope.processing = true;
            var params = {
                'action': 'checkpwd',
                'password': $rootScope.$redis.password,
                'host': $rootScope.$redis.host || '127.0.0.1',
                'port': $rootScope.$redis.port || '6379'
            };
            Request.post('/api/operation/redis', params, function(data) {
                $scope.processing = false;
                if (data.code == 0) {
                    $rootScope.$redis.connected = true;
                    Message.setSuccess('Redis 连接成功！');
                    $scope.redis_load_info();
                    $scope.redis_load_dbs();
                } else {
                    Message.setError(data.msg || 'Redis 连接失败！');
                }
            });
        };

        $scope.redis_disconnect = function() {
            $rootScope.$redis.connected = false;
            $scope.redisInfo = null;
            $scope.redisDbs = [];
            $scope.redisDetail = { db: null, keys: null, keyInfo: null, keyCount: 0 };
        };

        $scope.redis_load_info = function() {
            if (!$rootScope.$redis.connected) return;
            $scope.redisLoading.info = true;
            var params = {
                'password': $rootScope.$redis.password,
                'host': $rootScope.$redis.host || '127.0.0.1',
                'port': $rootScope.$redis.port || '6379'
            };
            Task.call($scope, module,
                '/api/task/redis.info',
                '/api/task/redis.info', params, {
                    'success': function(data) {
                        $scope.redisInfo = data.data;
                        $scope.redisLoading.info = false;
                    },
                    'error': function() {
                        $scope.redisLoading.info = false;
                    }
                }
            );
        };

        $scope.redis_load_dbs = function() {
            if (!$rootScope.$redis.connected) return;
            $scope.redisLoading.dbs = true;
            var params = {
                'password': $rootScope.$redis.password,
                'host': $rootScope.$redis.host || '127.0.0.1',
                'port': $rootScope.$redis.port || '6379'
            };
            Task.call($scope, module,
                '/api/task/redis.databases',
                '/api/task/redis.databases', params, {
                    'success': function(data) {
                        $scope.redisDbs = data.data || [];
                        $scope.redisLoading.dbs = false;
                    },
                    'error': function() {
                        $scope.redisLoading.dbs = false;
                    }
                }
            );
        };

        $scope.redis_show_db = function(db) {
            if (!$rootScope.$redis.connected) return;
            $scope.redisDetail.db = db;
            $scope.redisDetail.keys = null;
            $scope.redisDetail.keyInfo = null;
            $scope.redisLoading.detail = true;
            var params = {
                'password': $rootScope.$redis.password,
                'host': $rootScope.$redis.host || '127.0.0.1',
                'port': $rootScope.$redis.port || '6379',
                'db': db.index
            };
            Task.call($scope, module,
                '/api/task/redis.dbinfo_' + db.index,
                '/api/task/redis.dbinfo_' + db.index, params, {
                    'success': function(data) {
                        var info = data.data;
                        $scope.redisDetail.keys = info ? info.key_details || [] : [];
                        $scope.redisDetail.keyCount = info ? info.key_count || 0 : 0;
                        $scope.redisLoading.detail = false;
                    },
                    'error': function() {
                        $scope.redisLoading.detail = false;
                    }
                }
            );
        };

        $scope.redis_show_key = function(k) {
            if (!$rootScope.$redis.connected) return;
            $scope.redisDetail.keyInfo = null;
            $scope.redisLoading.key = true;
            var params = {
                'password': $rootScope.$redis.password,
                'host': $rootScope.$redis.host || '127.0.0.1',
                'port': $rootScope.$redis.port || '6379',
                'db': $scope.redisDetail.db ? $scope.redisDetail.db.index : 0,
                'key': k.name
            };
            Task.call($scope, module,
                '/api/task/redis.get_key_' + k.name,
                '/api/task/redis.get_key_' + k.name, params, {
                    'success': function(data) {
                        $scope.redisDetail.keyInfo = data.data;
                        $scope.redisLoading.key = false;
                    },
                    'error': function() {
                        $scope.redisLoading.key = false;
                    }
                }
            );
        };

        $scope.redis_del_key_confirm = function(k) {
            if (!confirm('确定要删除 Key「' + k.name + '」吗？此操作不可恢复！')) return;
            var params = {
                'password': $rootScope.$redis.password,
                'host': $rootScope.$redis.host || '127.0.0.1',
                'port': $rootScope.$redis.port || '6379',
                'db': $scope.redisDetail.db ? $scope.redisDetail.db.index : 0,
                'key': k.name
            };
            $scope.redisLoading.detail = true;
            Task.call($scope, module,
                '/api/task/redis.del_key_' + k.name,
                '/api/task/redis.del_key_' + k.name, params, {
                    'success': function(data) {
                        $scope.redis_show_db($scope.redisDetail.db);
                        $scope.redis_load_dbs();
                    },
                    'error': function() {
                        $scope.redisLoading.detail = false;
                    }
                }
            );
        };

        $scope.redis_flushdb_confirm = function(db) {
            if (!confirm('确定要清空数据库「' + db.name + '」吗？所有数据将被永久删除！')) return;
            var params = {
                'password': $rootScope.$redis.password,
                'host': $rootScope.$redis.host || '127.0.0.1',
                'port': $rootScope.$redis.port || '6379',
                'db': db.index
            };
            $scope.redisLoading.dbs = true;
            Task.call($scope, module,
                '/api/task/redis.flushdb_' + db.index,
                '/api/task/redis.flushdb_' + db.index, params, {
                    'success': function(data) {
                        $scope.redis_load_dbs();
                        $scope.redisDetail = { db: null, keys: null, keyInfo: null, keyCount: 0 };
                    },
                    'error': function() {
                        $scope.redisLoading.dbs = false;
                    }
                }
            );
        };

        $scope.redis_flushall_confirm = function() {
            if (!confirm('确定要清空所有 Redis 数据库吗？所有数据将被永久删除且不可恢复！')) return;
            var params = {
                'password': $rootScope.$redis.password,
                'host': $rootScope.$redis.host || '127.0.0.1',
                'port': $rootScope.$redis.port || '6379'
            };
            $scope.redisLoading.dbs = true;
            Task.call($scope, module,
                '/api/task/redis.flushall',
                '/api/task/redis.flushall', params, {
                    'success': function(data) {
                        $scope.redis_load_dbs();
                        $scope.redisDetail = { db: null, keys: null, keyInfo: null, keyCount: 0 };
                    },
                    'error': function() {
                        $scope.redisLoading.dbs = false;
                    }
                }
            );
        };

        // 页面加载时如果已连接则加载数据
        if ($rootScope.$redis && $rootScope.$redis.connected) {
            $scope.redis_load_info();
            $scope.redis_load_dbs();
        }

        // 判断是否为对象类型（用于 redisInfo 展示）
        $scope.isObject = function(val) {
            return val !== null && typeof val === 'object' && !Array.isArray(val);
        };
    }
];

var DatabaseMySQLNewDBCtrl = [
    '$scope', 'Module', '$rootScope', '$location', 'Request', 'Message', 'Task',
    function($scope, Module, $rootScope, $location, Request, Message, Task) {
        var module = 'database.mysql.db.new';
        Module.init(module, '新建数据库');
        $scope.loaded = true;

        $scope.collation = 'utf8_general_ci';
        $scope.validate_password = function() {
            $scope.processing = true;
            Request.post('/api/operation/mysql', {
                'action': 'checkpwd',
                'password': $rootScope.$mysql.password
            }, function(data) {
                if (data.code == 0) {
                    $rootScope.$mysql.password_validated = true;
                }
                $scope.processing = false;
            });
        };
        $scope.newdb = function() {
            $scope.processing = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.create',
                '/api/task/mysql.create_' + $scope.dbname, {
                    'password': $rootScope.$mysql.password,
                    'dbname': $scope.dbname,
                    'collation': $scope.collation
                }, {
                    'success': function(data) {
                        $location.path('/database/mysql/db/edit/' + encodeURIComponent($scope.dbname));
                        $scope.processing = false;
                    },
                    'error': function() {
                        $scope.processing = false;
                    }
                }
            );
        };
    }
];

var DatabaseMySQLEditDBCtrl = [
    '$scope', 'Module', '$rootScope', '$routeParams', '$location', 'Request', 'Message', 'Task',
    function($scope, Module, $rootScope, $routeParams, $location, Request, Message, Task) {
        var section = $routeParams.section;
        $scope.dbname = decodeURIComponent(section);

        var module = 'database.mysql.db.edit';
        Module.init(module, '管理数据库 ' + $scope.dbname);
        Module.initSection('users');
        $scope.loaded = true;

        $scope.validate_password = function() {
            $scope.processing = true;
            Request.post('/api/operation/mysql', {
                'action': 'checkpwd',
                'password': $rootScope.$mysql.password
            }, function(data) {
                if (data.code == 0) {
                    $rootScope.$mysql.password_validated = true;
                    $scope.loaddbinfo();
                }
                $scope.processing = false;
            });
        };

        $scope.dbloading = true;
        $scope.loaddbinfo = function() {
            $scope.dbloading = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.dbinfo',
                '/api/task/mysql.dbinfo_' + $scope.dbname, {
                    'password': $rootScope.$mysql.password,
                    'dbname': $scope.dbname
                }, {
                    'success': function(data) {
                        $scope.dbinfo = data.data;
                        $scope.dbloading = false;
                        $scope.loadusers();
                    },
                    'error': function() {
                        $scope.dbloading = false;
                    }
                }
            );
        };

        $scope.userloading = true;
        $scope.loadusers = function() {
            $scope.userloading = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.users',
                '/api/task/mysql.users_' + $scope.dbname, {
                    'password': $rootScope.$mysql.password,
                    'dbname': $scope.dbname
                }, {
                    'success': function(data) {
                        $scope.users = data.data;
                        $scope.userloading = false;
                    },
                    'error': function() {
                        $scope.userloading = false;
                    }
                }
            );
        };

        $scope.setcollation = function() {
            $scope.processing = true;
            Request.post('/api/operation/mysql', {
                'action': 'alter_database',
                'password': $rootScope.$mysql.password,
                'dbname': $scope.dbname,
                'collation': $scope.dbinfo.collation
            }, function() {
                $scope.processing = false;
            });
        };
        $scope.rename = function() {
            $scope.processing = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.rename',
                '/api/task/mysql.rename_' + $scope.dbname, {
                    'password': $rootScope.$mysql.password,
                    'dbname': $scope.dbname,
                    'newname': $scope.dbinfo.name
                }, {
                    'success': function(data) {
                        $location.path('/database/mysql/db/edit/' + encodeURIComponent($scope.dbinfo.name));
                        $scope.processing = false;
                    },
                    'error': function() {
                        $scope.processing = false;
                    }
                }
            );
        };
        $scope.selectexportfolder = function() {
            $scope.selector.onlydir = true;
            $scope.selector.onlyfile = false;
            $scope.selector.load($scope.exportpath ? $scope.exportpath : '/root');
            $scope.selector.selecthandler = function(path) {
                $('#selector').modal('hide');
                $scope.exportpath = path;
            };
            $('#selector').modal();
        };
        $scope.exportdb = function() {
            $scope.processing = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.export',
                '/api/task/mysql.export_' + $scope.dbname, {
                    'password': $rootScope.$mysql.password,
                    'dbname': $scope.dbname,
                    'path': $scope.exportpath
                },
                function(data) {
                    $scope.processing = false;
                }
            );
        };
        $scope.dropdb = function() {
            $scope.processing = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.drop',
                '/api/task/mysql.drop_' + $scope.dbname, {
                    'password': $rootScope.$mysql.password,
                    'dbname': $scope.dbname
                },
                function(data) {
                    if (data.code == 0) {
                        $location.path('/database');
                        $scope.sec('mysql');
                    }
                    $scope.processing = false;
                }
            );
        };

        if ($rootScope.$mysql.password_validated) {
            $scope.loaddbinfo();
        }
    }
];

var DatabaseMySQLNewUserCtrl = [
    '$scope', 'Module', '$rootScope', '$location', 'Request', 'Message', 'Task',
    function($scope, Module, $rootScope, $location, Request, Message, Task) {
        var module = 'database.mysql.user.new';
        Module.init(module, '添加新用户');
        $scope.loaded = true;

        $scope.dbname = Module.getParam('dbname');

        $scope.validate_password = function() {
            $scope.processing = true;
            Request.post('/api/operation/mysql', {
                'action': 'checkpwd',
                'password': $rootScope.$mysql.password
            }, function(data) {
                if (data.code == 0) {
                    $rootScope.$mysql.password_validated = true;
                }
                $scope.processing = false;
            });
        };
        $scope.newuser = function() {
            if (!$scope.emptypassword) {
                if ($scope.password != $scope.passwordc) {
                    Message.setError('新密码和确认密码不一致！');
                    return;
                }
            }
            var username = $scope.user + '@' + $scope.host;
            $scope.processing = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.createuser',
                '/api/task/mysql.createuser_' + username, {
                    'password': $rootScope.$mysql.password,
                    'user': $scope.user,
                    'host': $scope.host,
                    'pwd': $scope.emptypassword ? '' : $scope.password
                }, {
                    'success': function(data) {
                        $location.path('/database/mysql/user/edit/' + encodeURIComponent(username));
                        if ($scope.dbname) $location.search('dbname', $scope.dbname);
                        $scope.processing = false;
                    },
                    'error': function() {
                        $scope.processing = false;
                    }
                }
            );
        };
        $scope.genpassword = function() {
            // REF: http://stackoverflow.com/questions/9719570/generate-random-password-string-with-requirements-in-javascript
            var chars = "ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz";
            var string_length = 16;
            var randomstring = '';
            var charCount = 0;
            var numCount = 0;
            for (var i = 0; i < string_length; i++) {
                // If random bit is 0, there are less than 3 digits already saved, and there are not already 5 characters saved, generate a numeric value. 
                if ((Math.floor(Math.random() * 2) == 0) && numCount < 3 || charCount >= 5) {
                    var rnum = Math.floor(Math.random() * 10);
                    randomstring += rnum;
                    numCount += 1;
                } else {
                    // If any of the above criteria fail, go ahead and generate an alpha character from the chars string
                    var rnum = Math.floor(Math.random() * chars.length);
                    randomstring += chars.substring(rnum, rnum + 1);
                    charCount += 1;
                }
            }
            $scope.randpassword = $scope.password = $scope.passwordc = randomstring;
        };
    }
];

var DatabaseMySQLEditUserCtrl = [
    '$scope', 'Module', '$rootScope', '$routeParams', '$location', 'Request', 'Message', 'Task',
    function($scope, Module, $rootScope, $routeParams, $location, Request, Message, Task) {
        var section = $routeParams.section;
        $scope.username = decodeURIComponent(section);
        var fs = $scope.username.split('@');
        $scope.user = fs[0];
        $scope.host = fs[1];

        var module = 'database.mysql.user.edit';
        Module.init(module, '管理用户 ' + $scope.username);
        Module.initSection('privs');
        $scope.loaded = true;

        $scope.validate_password = function() {
            $scope.processing = true;
            Request.post('/api/operation/mysql', {
                'action': 'checkpwd',
                'password': $rootScope.$mysql.password
            }, function(data) {
                if (data.code == 0) {
                    $rootScope.$mysql.password_validated = true;
                    $scope.loadprivs();
                    $scope.loaddbs();
                }
                $scope.processing = false;
            });
        };

        $scope.privsloading = true;
        $scope.loadprivs = function() {
            $scope.privsloading = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.userprivs',
                '/api/task/mysql.userprivs_' + $scope.username, {
                    'password': $rootScope.$mysql.password,
                    'username': $scope.username
                }, {
                    'success': function(data) {
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
                    'error': function() {
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
        $scope.editprivs = function(privs, privtype) {
            if (privtype == 'global') {
                $scope.orgprivs = $scope.privs.global;
                $scope.curprivs = angular.copy($scope.privs.global);
            } else {
                if (!privs) {
                    if (!$scope.privs_dbname) return;
                    // check if the dbname already exists
                    var dbfound = false;
                    for (var i = 0; i < $scope.privs.bydb.length; i++) {
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
                $scope.privsedit_title = '设置 ' + $scope.username + ' 的全局权限';
            else
                $scope.privsedit_title = '设置 ' + $scope.username + ' 在数据库 ' + $scope.curprivs.Db + ' 的权限';
            $('#privsedit').modal();
        };

        $scope.updateprivs = function() {
            Task.call(
                $scope,
                module,
                '/api/task/mysql.updateuserprivs',
                '/api/task/mysql.updateuserprivs_' + encodeURIComponent($scope.username + ($scope.curprivs.Db ? '_' + $scope.curprivs.Db : '')), {
                    'password': $rootScope.$mysql.password,
                    'username': $scope.username,
                    'privs': angular.toJson($scope.curprivs),
                    'dbname': $scope.curprivs.Db
                }, {
                    'success': function(data) {
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
                            $location.path('/database/mysql/db/edit/' + encodeURIComponent(dbname));
                        }
                    }
                }
            );
        };

        $scope.loaddbs = function() {
            $scope.dbloading = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.databases',
                '/api/task/mysql.databases', {
                    'password': $rootScope.$mysql.password
                }, {
                    'success': function(data) {
                        $scope.dbs = data.data;
                    }
                },
                true
            );
        };

        $scope.setpassword = function() {
            if (!$scope.emptypassword) {
                if ($scope.newpassword != $scope.newpasswordc) {
                    Message.setError('新密码和确认密码不一致！');
                    return;
                }
            }
            $scope.processing = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.setuserpassword',
                '/api/task/mysql.setuserpassword_' + $scope.username, {
                    'password': $rootScope.$mysql.password,
                    'username': $scope.username,
                    'pwd': $scope.emptypassword ? '' : $scope.newpassword
                }, {
                    'success': function(data) {
                        $scope.processing = false;
                        if ($scope.username == 'root@localhost') {
                            // reset cached mysql password
                            $rootScope.$mysql = {
                                'password': '',
                                'password_validated': false
                            };
                        }
                    },
                    'error': function() {
                        $scope.processing = false;
                    }
                }
            );
        };

        $scope.dropuser = function() {
            $scope.processing = true;
            Task.call(
                $scope,
                module,
                '/api/task/mysql.dropuser',
                '/api/task/mysql.dropuser_' + $scope.username, {
                    'password': $rootScope.$mysql.password,
                    'username': $scope.username
                },
                function(data) {
                    if (data.code == 0) {
                        $location.path('/database');
                        $scope.sec('mysql');
                    }
                    $scope.processing = false;
                }
            );
        };

        if ($rootScope.$mysql.password_validated) {
            $scope.loadprivs();
            $scope.loaddbs();
        }
    }
];