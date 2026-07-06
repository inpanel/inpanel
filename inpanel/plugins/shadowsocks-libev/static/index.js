var PluginsShadowsocksCtrl = [
    '$scope', 'Module',
    function ($scope, Module) {
        var module = 'plugins.shadowsocks';
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
