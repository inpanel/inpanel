
var PluginsCACMEtrl = [
    '$scope', 'Module',
    function ($scope, Module) {
        var module = 'plugins.acme';
        Module.init(module, 'ACME');
        $scope.loaded = false;

        $scope.load = function () {
            $scope.loaded = true;
        };
    }
];