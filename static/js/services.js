angular.module('vpsmate.services', []).
factory('Auth', ['$rootScope', '$http', '$location', function($scope, $http, $location) {
	var Auth = {};
	Auth.required = function(callback, errCallback){
		$http.post('/authstatus').success(function(data){
			if (callback) callback.call(null, data.authed == 'yes');
			if (data.authed == 'no') {
				$scope.loginto = $location.path();
				$scope.loginto_section = $location.search().s;
				if ($scope.loginto == '/' || $scope.loginto == '/logout') {
					$scope.loginto = '/main';
					$scope.loginto_section = '';
				}
				$location.path('/');
				$location.search('s', null);
			}
		}).error(function(data, status){
			if (errCallback) errCallback.call(null, status);
		});
	};
	Auth.getlastactive = function(callback){
		$http.get('/authstatus?'+Math.random()).success(function(data){
			if (callback) callback.call(null, data.lastactive);
		});
	};
	return Auth;
}]).
factory('Module', ['$rootScope', '$location', function($scope, $location) {
	var Module = {}
	Module.init = function(module, htmlTitle){
		$scope.module = module;
		$scope.htmlTitle = htmlTitle;
	};
	Module.initSection = function(defaultSec){
		var section = $location.search().s;
		$scope.activeTabName = section ? section : defaultSec;
	};
	Module.getSection = function() {
		return $location.search().s;
	};
	Module.setSection = function(sec) {
		$scope.activeTabName = sec;
	};
	Module.getParam = function(p) {
		return $location.search()[p];
	};
	return Module;
}]).
factory('Timeout', ['$rootScope', '$timeout', function($scope, $timeout) {
	var Timeout = function(func, secs, module, singleton, timeout_name){
		if (module && $scope.module != module) return;
		if (singleton && $scope[timeout_name]) return;
		if (!timeout_name) timeout_name = 'timeout';
		$scope[timeout_name] = $timeout(function(){
			if ($scope[timeout_name]) delete $scope[timeout_name];
			if (!module || $scope.module == module) func.call();
		}, secs);
	};
	return Timeout;
}]).
factory('Message', ['$rootScope', '$timeout', function($scope, $timeout) {
	var Message = {};
	$scope.showSuccessMsg = false;
	$scope.showErrorMsg = false;
	$scope.showWarningMsg = false;
	$scope.showInfoMsg = false;
	$scope.msgTimeout = 0;
	
	var delayClearMsg = function(){
		if ($scope.msgTimeout) $timeout.cancel($scope.msgTimeout);
		$scope.msgTimeout = $timeout(function(){
			$scope.showSuccessMsg = false;
			$scope.showErrorMsg = false;
			$scope.showInfoMsg = false;
			$scope.msgTimeout = 0;
		}, 5000);
	};
	
	Message.setSuccess = function(msg, keepMsg) {
		$scope.successMessage = msg;
		if (msg) {
			$scope.showSuccessMsg = true;
			$scope.showErrorMsg = false;
			$scope.showInfoMsg = false;
			if (!keepMsg) delayClearMsg();
		} else {
			$scope.showSuccessMsg = false;
			$scope.showErrorMsg = false;
			$scope.showInfoMsg = false;
		}
	};
	
	Message.setError = function(msg, keepMsg) {
		$scope.errorMessage = msg;
		if (msg) {
			$scope.showSuccessMsg = false;
			$scope.showErrorMsg = true;
			$scope.showInfoMsg = false;
			if (!keepMsg) delayClearMsg();
		} else {
			$scope.showSuccessMsg = false;
			$scope.showErrorMsg = false;
			$scope.showInfoMsg = false;
		}
	};

	Message.setInfo = function(msg, keepMsg) {
		$scope.infoMessage = msg;
		if (msg) {
			$scope.showSuccessMsg = false;
			$scope.showErrorMsg = false;
			$scope.showInfoMsg = true;
			if (!keepMsg) delayClearMsg();
		} else {
			$scope.showSuccessMsg = false;
			$scope.showErrorMsg = false;
			$scope.showInfoMsg = false;
		}
	};
	
	Message.setWarning = function(msg, keepMsg) {
		$scope.warningMessage = msg;
		if (msg) {
			$scope.showWarningMsg = true;
			if (!keepMsg) delayClearMsg();
		} else {
			$scope.showWarningMsg = false;
		}
	};
	
	return Message;
}]).
factory('Request', ['$http', '$rootScope', '$location', '$timeout', 'Message', function($http, $scope, $location, $timeout, Message) {
	var Request = {};

	var _successFuncBinder = function(callback, quiet){
		return function(data){
			$scope.processing = false;
			if (!quiet && data.msg) {
				if (data.code == 0) {
					Message.setSuccess(data.msg);
				} else if(data.code == -1) {
					Message.setError(data.msg);
				} else if(data.code == 1) {
					Message.setWarning(data.msg);
				} else if(data.code == 2) {
					Message.setInfo(data.msg);
				}
			}
			if (callback) callback.call(null, data);
		};
	};

	var _errorFuncBinder = function(callback, quiet){
		return function(data, status) {
			$scope.processing = false;
			if (!quiet && callback) {
				if (!callback.call(null, data, status)) return;
			}
			if (status == 403) {
				Message.setError('登录无效或超时，请重新登录。', true);
				$scope.loginto = $location.path();
				$scope.loginto_section = $location.search().s;
				if ($scope.loginto == '/' || $scope.loginto == '/logout') {
					$scope.loginto = '/main';
					$scope.loginto_section = '';
				}
				$location.path('/');
				$location.search('s', null);
			} else {
				Message.setError('发生未知错误！');
			}
		};
	};
	
	Request.setProcessing = function(processing){
		$scope.processing = processing;
	};

	Request.get = function(url, callback, errcallback, quiet){
		$scope.processing = true;
		var rurl = $scope.$proxyroot+url;
		if (rurl.indexOf('?') > 0)
			rurl += '&'+Math.random();
		else
			rurl += '?'+Math.random();
		$http.get(rurl)
			.success(_successFuncBinder(callback, quiet))
			.error(_errorFuncBinder(errcallback, quiet));
	};

	Request.post = function(url, data, callback, errcallback, quiet){
		$scope.processing = true;
		$http.post($scope.$proxyroot+url, data)
			.success(_successFuncBinder(callback, quiet))
			.error(_errorFuncBinder(errcallback, quiet));
	};

	return Request;
}]).
factory('Backend', ['Timeout', 'Request', function(Timeout, Request) {
	var Backend = {};
	
	Backend.call = function($scope, module, url, statusUrl, data, callback, quiet){
		$scope.waiting = true;
		Request.post(url, data, function(data){
			if (data.code == -1) {
				if (callback) {
					if (typeof callback.error == 'function')
						callback.error.call(null, data.data);
				}
				return;
			}
			var getStatus = function(){
				Request.get(statusUrl, function(data){
					if (data.status == 'finish'){
						$scope.waiting = false;
						if (data.code == 0) {
							if (callback) {
								if (typeof callback == 'function')
									callback.call(null, data);
								else if (typeof callback.success == 'function')
									callback.success.call(null, data);
							}
						} else {
							if (callback) {
								if (typeof callback == 'function')
									callback.call(null, data);
								else if (typeof callback.error == 'function')
									callback.error.call(null, data);
							}
						}
					} else {
						if (callback) {
							if (typeof callback.wait == 'function')
								callback.wait.call(null, data);
						}
						Timeout(getStatus, 500, module);
					}
				}, false, quiet);
			};
			Timeout(getStatus, 500, module);
		}, function(data){
			if (callback) {
				if (typeof callback.error == 'function')
					callback.error.call(null, data);
			}
		});
	};

	return Backend;
}]);
