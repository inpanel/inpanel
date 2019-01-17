var ApplicationCtrl = [
    '$scope', 'Module',
    function ($scope, Module) {
        var module = 'application';
        Module.init(module, '应用管理');
        $scope.loaded = false;

        $scope.load = function () {
            $scope.loaded = true;
        };
    }
];

var ApplicationShadowsocksCtrl = [
    '$scope', 'Module',
    function ($scope, Module) {
        var module = 'application.shadowsocks';
        Module.init(module, 'Shadowsocks');
        $scope.loaded = false;
        $scope.installed = false;

        $scope.load = function () {
            $scope.loaded = true;
            $scope.check();
        };

        $scope.check = function () {
            $scope.installed = false;
        }
    }
];
var ApplicationCACMEtrl = [
    '$scope', 'Module',
    function ($scope, Module) {
        var module = 'application.acme';
        Module.init(module, 'acme.sh');
        $scope.loaded = false;
        $scope.installed = false;

        $scope.load = function () {
            $scope.loaded = true;
            $scope.check();
        };

        $scope.check = function () {
            $scope.installed = false;
        }
    }
];