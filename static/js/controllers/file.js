var FileCtrl = [
'$scope', '$routeParams', 'Module', 'Message', 'Request', 'Backend',
function($scope, $routeParams, Module, Message, Request, Backend){
	var module = 'file';
	Module.init(module, '文件管理');

	var route_path = $routeParams.path;
	var route_file = $routeParams.file;
	var remember_path = true;
	var remember_file = true;

	$scope.path = $scope.lastpath = '/root';
	$scope.curpath = '';
	$scope.showhidden = false;
	$scope.clipboard = {
		'srcpath': '',
		'count': 0,
		'items': {}	// name: copy|cut|link
	};
	$scope.confirm = $scope.cancel = function(){};

	var parse_path = function(){
		// parse dir to array
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
	
	$scope.loaded = false;
	$scope.load = function(){
		if (route_path || route_file) {	// load the specified path and file
			$scope.loaded = true;
			remember_path = false;
			remember_file = false;
			if (route_file){
				route_path = route_file.split('/')
				route_file = route_path.pop()
				route_path = route_path.join('/');
				if (!route_path) route_path = '/';
			}
			$scope.listdir(route_path, true, function(){
				if (route_file) $scope.editfile(route_file);
			});
		} else {	// load from history
			Request.post('/operation/file', {
				'action': 'last'
			}, function(data){
				if (data.code == 0) {
					$scope.loaded = true;
					var lastfile = data.data['lastfile'];
					var lastdir = data.data['lastdir'];
					$scope.listdir(lastdir, true, function(){
						if (lastfile && lastfile.indexOf(lastdir) === 0) {
							lastfile = lastfile.replace(lastdir+'/', '')
							if (lastfile.indexOf('/') == -1) $scope.editfile(lastfile);
						}
					});
				}
			}, false, true);
		}
	};

	$scope.fileloading = false;
	$scope.listdir = function(path, clearselect, callback){
		if (path) $scope.path = path;
		if ($scope.path == '')
			$scope.path = '/root';
		else if ($scope.path != '/' && $scope.path.substr(-1) == '/')
			$scope.path = $scope.path.substr(0, $scope.path.length-1);
		$scope.path = $scope.path.replace('//', '/');

		var curpath = $scope.path;
		$scope.fileloading = true;
		Request.post('/operation/file', {
			'action': 'listdir',
			'path': curpath,
			'showhidden': $scope.showhidden,
			'remember': remember_path
		}, function(data){
			if (data.code == 0) {
				$scope.items = data.data;
				$scope.curpath = curpath;
				$scope.lastpath = curpath;
				if (clearselect) {
					$scope.selects = {};
					$scope.selectall = false;
				}
			} else {
				$scope.path = $scope.lastpath;
			}
			$scope.fileloading = false;
			parse_path();
			if (callback) callback.call();
		}, false, true);
	};
	$scope.getitem = function(name, oldname){
		if (!oldname)
			oldname = name;
		else
			delete $scope.selects[oldname];
		Request.post('/operation/file', {
			'action': 'getitem',
			'path': $scope.curpath+'/'+name
		}, function(data){
			if (data.code == 0) {
				var iteminfo = data.data;
				// update to item list
				var found = false;
				for (var i=0; i<$scope.items.length; i++){
					if ($scope.items[i].name == oldname) {
						$scope.items[i] = iteminfo;
						found = true;
						break;
					}
				}
				// insert new item to proper position
				if (!found){
					var inserted = false;
					var i = 0;
					if (iteminfo.isdir || iteminfo.islnk && iteminfo.link_isdir) {
						for (; i<$scope.items.length; i++){
							var item = $scope.items[i];
							if (item.isdir || item.islnk && item.link_isdir) {
								if ($scope.items[i].name.localeCompare(iteminfo.name) > 1) {
									$scope.items.splice(i, 0, iteminfo);
									inserted = true;
									break;
								}
							} else {
								break;
							}
						}
					} else {
						for (; i<$scope.items.length; i++){
							var item = $scope.items[i];
							if (item.isdir || item.islnk && item.link_isdir) continue;
							if ($scope.items[i].name.localeCompare(iteminfo.name) > 1) {
								$scope.items.splice(i, 0, iteminfo);
								inserted = true;
								break;
							}
						}
					}
					if (!inserted) $scope.items.splice(i, 0, iteminfo);	// insert at the end of list
				}
			} else {	// item not found
				// delete to item list
				for (var i=0; i<$scope.items.length; i++){
					if ($scope.items[i].name == name) {
						$scope.items.splice(i, 1);
						break;
					}
				}
			}
		}, false, true);
	};
	$scope.upandlist = function(){
		var patharr = $scope.curpath.split('/');
		patharr.pop();
		$scope.listdir(patharr.join('/')+'/', true);
	};
	$scope.editfile = function(path){
		Request.post('/operation/file', {
			'action': 'fread',
			'path': $scope.curpath+'/'+path,
			'remember': remember_file
		}, function(data){
			if (data.code == 0) {
				Message.setSuccess('');
				var filedata = data.data;
				$scope.filename = filedata.filename;
				$scope.filepath = filedata.filepath;
				$scope.filecharset = filedata.charset;
				$scope.filecharset_org = filedata.charset;
				editor.setValue('');
				$('#list').hide();
				$('#edit').show();
				editor.setOption('mode', filedata.mimetype);
				editor.setValue(filedata.content);
				hasChange = false;
			}
		});
	};
	$scope.return2list = $scope.canceledit = function(){
		if (hasChange) {
			$scope.confirm_title = '是否放弃修改？';
			$scope.confirm_body = $scope.filepath + ' 已被修改，是否放弃修改？';
			$('#confirm').modal();
			$scope.cancel = function(){};
			$scope.confirm = function(){
				$('#edit').hide();
				$('#list').show();
				Request.post('/operation/file', {'action': 'fclose'}, false, false, true);
			};
		} else {
			$('#edit').hide();
			$('#list').show();
			Request.post('/operation/file', {'action': 'fclose'}, false, false, true);
		}
	};
	$scope.savefile = function(){
		if (!hasChange && $scope.filecharset == $scope.filecharset_org) {
			Message.setInfo('文件未修改，无须保存！');
			return;
		}
		Request.post('/operation/file', {
			'action': 'fwrite',
			'path': $scope.filepath,
			'charset': $scope.filecharset,
			'content': editor.getValue()
		}, function(data){
			if (data.code == 0) {
				hasChange = false;
				$scope.getitem($scope.filename);
			}
		});
	};
	$scope.newfolder = function(){
		$scope.newname_title = '新建文件夹';
		$scope.newname_label = '文件夹名称';
		$scope.newname_name = '';
		$('#newname').modal();
		$scope.newname = function(){
			Request.post('/operation/file', {
				'action': 'createfolder',
				'path': $scope.curpath,
				'name': $scope.newname_name
			}, function(data){
				if (data.code == 0) {
					$scope.getitem($scope.newname_name);
				}
			});
		};
	};
	$scope.newfile = function(){
		$scope.newname_title = '新建文件';
		$scope.newname_label = '文件名称';
		$scope.newname_name = '';
		$('#newname').modal();
		$scope.newname = function(){
			Request.post('/operation/file', {
				'action': 'createfile',
				'path': $scope.curpath,
				'name': $scope.newname_name
			}, function(data){
				if (data.code == 0) {
					$scope.getitem($scope.newname_name);
				}
			});
		};
	};
	$scope.upload = function(){
		$('#upload').modal();
	};
	$scope.doupload = function(){
		var pathinfo = $('#uploadform').find('input[name=ufile]').val().split(/[\\\/]/);
		var name = pathinfo[pathinfo.length-1];
		Request.post('/operation/file', {
			'action': 'getitem',
			'path': $scope.curpath+'/'+name
		}, function(data){
			if (data.code == 0) {
				$scope.confirm_title = '上传文件覆盖确认';
				$scope.confirm_body = '<p>系统检测到当前目录下已存在同名文件 '+name+'。</p><p>确认要覆盖这个文件吗？</p>';
				$('#confirm').modal();
				$scope.confirm = function(){
					$('#uploadform').submit();
				};
			} else {
				$('#uploadform').submit();
			}
		}, false, true);
	};
	$scope.download = function(){
		$('#download').modal();
		$scope.dodownload = function(){
			Backend.call(
				$scope,
				module,
				'/backend/wget',
				'/backend/wget_'+encodeURIComponent(encodeURIComponent($scope.downloadurl)),
				{
					'url': $scope.downloadurl,
					'path': $scope.curpath
				},
				{
					'success': function(data){
						$scope.listdir();
					}
				}
			);
		};
	};
	$scope.togglehidden = function(){
		$scope.showhidden = !$scope.showhidden;
		$scope.listdir();
	};
	$scope.rename = function(oldname){
		$scope.newname_title = '重命名';
		$scope.newname_label = '新名称';
		$scope.newname_name = oldname;
		$('#newname').modal();
		$scope.newname = function(){
			Request.post('/operation/file', {
				'action': 'rename',
				'path': $scope.curpath+'/'+oldname,
				'name': $scope.newname_name
			}, function(data){
				if (data.code == 0) {
					$scope.getitem($scope.newname_name, oldname);
				}
			});
		};
	};
	var bindclipfunc = function(type){
		return function(name, selected){
			var cb = $scope.clipboard;
			if (cb.srcpath != $scope.curpath) {
				cb.items = {};
				cb.count = 0;
			}
			if (typeof selected == 'undefined') {
				if (typeof cb.items[name] == 'undefined') {
					cb.srcpath = $scope.curpath;
					cb.items[name] = type;
					cb.count++;
				} else if (cb.items[name] == type)  {
					delete cb.items[name];
					cb.count--;
				} else if (typeof selected == 'undefined') {
					cb.items[name] = type;
				}
			} else {
				if (selected) {
					if (typeof cb.items[name] == 'undefined') {
						cb.srcpath = $scope.curpath;
						cb.count++;
					}
					cb.items[name] = type;
				} else {
					if (typeof cb.items[name] != 'undefined') {
						delete cb.items[name];
						cb.count--;
					}
				}
			}
		};
	}
	$scope.togglecopy = bindclipfunc('copy');
	$scope.togglecut = bindclipfunc('cut');
	$scope.togglelink = bindclipfunc('link');
	$scope.paste = function(){
		pasteeach();
	};
	var pastedo = function(type, srcpath, despath, name){
		if (type == 'copy') {
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
						delete $scope.clipboard.items[name];
						$scope.selects = {};
						$scope.listdir();
						pasteeach();
					},
					'error': function(data){
						$scope.listdir();
					}
				}
			);
		} else if (type == 'cut') {
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
						delete $scope.clipboard.items[name];
						$scope.selects = {};
						$scope.listdir();
						pasteeach();
					},
					'error': function(data){
						$scope.listdir();
					}
				}
			);
		} else if (type == 'link') {
			Request.post('/operation/file', {
				'action': 'link',
				'srcpath': srcpath,
				'despath': despath
			}, function(data){
				if (data.code == 0) {
					$scope.selects = {};
					$scope.listdir();
					delete $scope.clipboard.items[name];
					pasteeach();
				}
			});
		}
	};
	var pasteeach = function(newname){
		// check if some file/folder/link already exists
		var name = '';
		for (name in $scope.clipboard.items) break;
		if (!name) return;
		var type = $scope.clipboard.items[name];
		Request.post('/operation/file', {
			'action': 'exist',
			'name': newname ? newname : name,
			'path': $scope.curpath
		}, function(data){
			if (data.code == 0) {
				var srcpath = $scope.clipboard.srcpath+'/'+name;
				var despath = $scope.curpath+'/'+(newname ? newname : name);
				if (data.data) {
					$scope.overwrite_filename = (newname ? newname : name);
					$scope.overwrite_option = 'rename';
					$scope.overwrite_newname = (newname ? newname : name)+'.new';
					$('#overwriteconfirm').modal();
					$scope.overwrite = function(){
						if ($scope.overwrite_option == 'rename') {
							pasteeach($scope.overwrite_newname);
						} else {
							pastedo(type, srcpath, despath, name);
						}
					};
					//$scope.cancel = function(){
					//	delete $scope.clipboard.items[name];
					//};
					//$scope.confirm = function(){
					//	pastedo(type, srcpath, despath, name);
					//};
				} else {	// no despath exists
					pastedo(type, srcpath, despath, name);
				}
			}
		});
	};
	$scope.move2trash = function(name){
		Request.post('/operation/file', {
			'action': 'delete',
			'paths': $scope.curpath+'/'+name
		}, function(data){
			if (data.code == 0) {
				$scope.getitem(name);
				// deal with .filename.bak
				var bakname = '.'+name+'.bak';
				for (var i=0;i<$scope.items.length;i++) {
					if ($scope.items[i].name == bakname) {
						$scope.getitem(bakname);
						break;
					}
				}
			}
		});
	};
	$scope.compressconfirm = function(name, isreg){
		$scope.compress_isreg = isreg;
		$scope.compress_type = isreg ? '.gz' : '.tar.gz';
		$scope.compress_zipname = name;
		$scope.compress_name = name;
		$scope.compress_names = [];
		$('#compressconfirm').modal();
	};
	$scope.compress = function(){
		var zippath = $scope.curpath+'/'+$scope.compress_zipname+$scope.compress_type;
		var srcpath = $scope.curpath+'/'+$scope.compress_name;
		Backend.call(
			$scope,
			module,
			'/backend/compress',
			'/backend/compress_'+zippath+'_'+srcpath, 
			{
				'zippath': zippath,
				'paths': srcpath
			},
			{
				'success': function(data){
					var newname = $scope.compress_zipname+$scope.compress_type;
					if ($scope.compress_type == '.gz')
						$scope.getitem(newname, $scope.compress_name);
					else
						$scope.getitem(newname);
				}
			}
		);
	};
	$scope.decompress = function(name){
		var ns = name.split('.');
		var f1 = ns.pop();
		var f2 = ns.pop();
		if (f1=='gz' && f2!='tar') {
			var zippath = $scope.curpath+'/'+name;
			Backend.call(
				$scope,
				module,
				'/backend/decompress',
				'/backend/decompress_'+zippath+'_', 
				{
					'zippath': zippath
				},
				{
					'success': function(data){
						$scope.getitem(name.substr(0, name.length-3), name);
					}
				}
			);
			return;
		}
		$scope.selector_title = '请选择要解压到的目录';
		$scope.selector.onlydir = true;
		$scope.selector.onlyfile = false;
		$scope.selector.load($scope.curpath);
		$scope.selector.selecthandler = function(path){
			$('#selector').modal('hide');
			// check if file exists in the path
			Message.setInfo('正在检测目录...', true);
			Request.post('/operation/file', {
				'action': 'listdir',
				'path': path,
				'showhidden': true,
				'remember': false
			}, function(data){
				if (data.code == 0) {
					Message.setInfo('');
					var confirm = function(){
						var zippath = $scope.curpath+'/'+name;
						Backend.call(
							$scope,
							module,
							'/backend/decompress',
							'/backend/decompress_'+zippath+'_'+path, 
							{
								'zippath': zippath,
								'despath': path
							},
							{
								'success': function(data){
									if ($scope.curpath == path) $scope.listdir();
								}
							}
						);
					}
					if (data.data.length>0) {
						$scope.confirm_title = '解压确认';
						$scope.confirm_body = '<p>系统检测到目录 '+path+' 下存在文件，继续解压将可能覆盖这些文件。</p><p>确认要继续解压吗？</p>';
						$('#confirm').modal();
						$scope.confirm = confirm;
					} else {
						confirm();
					}
				} else {
					Message.setError('检测目录失败！');
				}
			}, false, true);
		};
		$('#selector').modal();
	};

    $scope.$watch('selectall', function(value) {
        angular.forEach($scope.items, function(item) {
            $scope.selects[item.name] = value;
        });
    });
	$scope.multicopy = function(){
		var itemfound = false;
		angular.forEach($scope.selects, function(selected, item){
			$scope.togglecopy(item, selected);
			if (selected) itemfound = true;
		});
		if (!itemfound) {
			Message.setError('请先选择文件或目录！');
			return;
		}
	};
	$scope.multicut = function(){
		var itemfound = false;
		angular.forEach($scope.selects, function(selected, item){
			$scope.togglecut(item, selected);
			if (selected) itemfound = true;
		});
		if (!itemfound) {
			Message.setError('请先选择文件或目录！');
			return;
		}
	};
	$scope.multidel = function(){
		var paths = [];
		angular.forEach($scope.selects, function(selected, item){
			if (selected) paths.push($scope.curpath+'/'+item);
		});
		if (paths.length == 0) {
			Message.setError('请先选择文件或目录！');
			return;
		}
		Request.post('/operation/file', {
			'action': 'delete',
			'paths': paths.join(',')
		}, function(data){
			if (data.code == 0) {
				$scope.selects = {};
				$scope.listdir();
			}
		});
	};
	$scope.tarconfirm = function(){
		var names = [];
		angular.forEach($scope.selects, function(selected, item){
			if (selected) names.push(item);
		});
		if (names.length == 0) {
			Message.setError('请先选择文件或目录！');
			return;
		}
		if (names.length == 1) {
			$scope.compressconfirm(names[0], false);
			return
		}
		$scope.compress_isreg = false;
		$scope.compress_type = '.tar.gz';
		$scope.compress_zipname = $scope.curpath.split('/').pop();
		$scope.compress_name = '多个项目';
		$scope.compress_names = names;
		$('#compressconfirm').modal();
	};
	$scope.tar = function(){
		var zippath = $scope.curpath+'/'+$scope.compress_zipname+$scope.compress_type;
		var srcpaths = [];
		for (var i=0; i<$scope.compress_names.length; i++) {
			srcpaths.push($scope.curpath+'/'+$scope.compress_names[i]);
		}
		if (srcpaths.length == 0) {
			Message.setError('请先选择文件或目录！');
			return;
		}
		Backend.call(
			$scope,
			module,
			'/backend/compress',
			'/backend/compress_'+zippath+'_'+srcpaths.join(','), 
			{
				'zippath': zippath,
				'paths': srcpaths.join(',')
			},
			{
				'success': function(data){
					$scope.listdir();
				}
			}
		);
	};
	
	$scope.chownconfirm = function(name, user, group, isdir){
		if (!name) {
			var names = [];
			angular.forEach($scope.selects, function(selected, item){
				if (selected) names.push(item);
			});
			if (names.length == 0) {
				Message.setError('请先选择文件或目录！');
				return;
			}
		}
		if (!$scope.users) {
			Request.post('/operation/user', {
				'action': 'listuser',
				'fullinfo': false
			}, function(data){
				if (data.code == 0) {
					$scope.users = data.data;
				}
			}, false, true);
		}
		if (!$scope.groups) {
			Request.post('/operation/user', {
				'action': 'listgroup',
				'fullinfo': false
			}, function(data){
				if (data.code == 0) {
					$scope.groups = data.data;
				}
			}, false, true);
		}
		if (name) {
			$scope.chown_user = user;
			$scope.chown_group = group;
			$scope.chown_names = [name];
			$scope.chown_recursively = true;
			$scope.chown_hasdir = isdir;
		} else {
			$scope.chown_names = names;
			$scope.chown_recursively = true;
			$scope.chown_hasdir = true;
		}
		$('#chownconfirm').modal();
	};
	$scope.chown = function(){
		var paths = [];
		for (var i=0; i<$scope.chown_names.length; i++)
			paths.push($scope.curpath+'/'+$scope.chown_names[i]);
		paths = paths.join(',');
		Backend.call(
			$scope,
			module,
			'/backend/chown',
			'/backend/chown_'+paths, 
			{
				'paths': paths,
				'user': $scope.chown_user,
				'group': $scope.chown_group,
				'recursively': $scope.chown_recursively
			},
			{
				'success': function(data){
					if ($scope.chown_names.length == 1)
						$scope.getitem($scope.chown_names[0]);
					else
						$scope.listdir();
				}
			}
		);
	};
	
	$scope.chmodconfirm = function(name, perms, isdir){
		if (!name) {
			var names = [];
			angular.forEach($scope.selects, function(selected, item){
				if (selected) names.push(item);
			});
			if (names.length == 0) {
				Message.setError('请先选择文件或目录！');
				return;
			}
			perms = '0744';
		}
		perms = parseInt(perms, 8);
		$scope.chmod_permbits = [
			[(perms&0400)!=0, (perms&0200)!=0, (perms&0100)!=0],
			[(perms&0040)!=0, (perms&0020)!=0, (perms&0010)!=0],
			[(perms&0004)!=0, (perms&0002)!=0, (perms&0001)!=0],
		];
		$scope.chmod_recursively = true;
		if (name) {
			$scope.chmod_names = [name];
			$scope.chmod_hasdir = isdir;
		} else {
			$scope.chmod_names = names;
			$scope.chmod_hasdir = true;
		}
		$('#chmodconfirm').modal();
	};
	$scope.chmod = function(){
		var perms = 0000;
		for (var i=0; i<3; i++)
			for (var j=0; j<3; j++)
				perms |= ($scope.chmod_permbits[i][j]<<(8-i*3-j));
		perms = perms.toString(8);
		var paths = [];
		for (var i=0; i<$scope.chmod_names.length; i++)
			paths.push($scope.curpath+'/'+$scope.chmod_names[i]);
		paths = paths.join(',');
		Backend.call(
			$scope,
			module,
			'/backend/chmod',
			'/backend/chmod_'+paths, 
			{
				'paths': paths,
				'perms': perms,
				'recursively': $scope.chmod_recursively
			},
			{
				'success': function(data){
					if ($scope.chmod_names.length == 1)
						$scope.getitem($scope.chmod_names[0]);
					else
						$scope.listdir();
				}
			}
		);
	};

	var hasChange = false;
	var editor = CodeMirror(document.getElementById('editor'), {
		value: '',
		lineNumbers: true,
		lineWrapping: true,
		matchBrackets: true,
		onCursorActivity: function() {
			editor.setLineClass(hlLine, null, null);
			hlLine = editor.setLineClass(editor.getCursor().line, null, 'activeline');
			// disable match highlight in IE, or it will slow down the page
			if (!$.browser.msie) editor.matchHighlight('CodeMirror-matchhighlight');
		},
		onChange: function() {
			hasChange = true;
		}
	});
	var hlLine = editor.setLineClass(0, 'activeline');
}];

var FileTrashCtrl = [
'$scope', '$routeParams', 'Module', 'Message', 'Request', 'Backend',
function($scope, $routeParams, Module, Message, Request, Backend){
	var module = 'file.trash';
	Module.init(module, '回收站管理');

	$scope.loaded = true;

	$scope.confirm = function(){};

	$scope.fileloading = false;
	$scope.tlist = function(){	
		$scope.fileloading = true;
		Request.post('/operation/file', {
			'action': 'tlist'
		}, function(data){
			if (data.code == 0) {
				$scope.items = data.data;
				$scope.fileloading = false;
			}
		});
	};
	$scope.restore = function(mount, uuid){
		Request.post('/operation/file', {
			'action': 'trestore',
			'mount': mount,
			'uuid': uuid
		}, function(data){
			if (data.code == 0) {
				$scope.tlist();
			}
		});
	};
	$scope.tdeleteconfirm = function(name, mount, uuid){
		$scope.confirm_title = '删除确认';
		$scope.confirm_body = '<p>删除后文件将不可恢复！</p><p>确认要删除 '+name+' 吗？</p>';
		$('#confirm').modal();
		$scope.confirm = function(){
			$scope.tdelete(mount, uuid);
		};
	};
	$scope.tdelete = function(mount, uuid){
		Request.post('/operation/file', {
			'action': 'titem',
			'mount': mount,
			'uuid': uuid
		}, function(data){
			if (data.code == 0) {
				var path = data.data.realpath;
				Backend.call(
					$scope,
					module,
					'/backend/remove',
					'/backend/remove_'+path,
					{
						'paths': path
					},
					function(){
						Request.post('/operation/file', {
							'action': 'tdelete',
							'mount': mount,
							'uuid': uuid
						}, function(data){
							if (data.code == 0) {
								$scope.tlist();
							}
						});
					}
				);
			}
		});
	};
	$scope.tcleanconfirm = function(){
		$scope.confirm_title = '清空确认';
		$scope.confirm_body = '<p>清空回收站后，回收站中的所有文件都将被删除且不可恢复！<p>\
								<p>确认要清空回收站吗？</p>';
		$('#confirm').modal();
		$scope.confirm = function(){
			$scope.tclean();
		};
	};
	$scope.tclean = function(){
		Request.post('/operation/file', {
			'action': 'trashs'
		}, function(data){
			if (data.code == 0) {
				var trashs = data.data.join(',');
				Backend.call(
					$scope,
					module,
					'/backend/remove',
					'/backend/remove_'+trashs,
					{
						'paths': trashs
					},
					function(){
						Message.setSuccess('清空回收站完成！');
						$scope.tlist();
					}
				);
			}
		});
	};
}];