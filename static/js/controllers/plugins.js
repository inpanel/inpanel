var PluginsHome = [
    '$scope', 'Module',
    function ($scope, Module) {
        var module = 'plugins';
        Module.init(module, '应用管理');
        $scope.loaded = false;

        $scope.load = function () {
            $scope.loaded = true;
            $scope.init_plugins();
        };
        $scope.init_plugins = function () {
            // app.directive("runoobDirective", function() {
            //     return {
            //         template : "<h1>自定义指令!</h1>"
            //     };
            // });
            // angular.module('inpanel.directives', []).directive('acme', function () {
            inpanel.directive("acme", function() {
                return {
                    restrict: 'A',
                    transclude: true,
                    scope: {},
                    replace: true,
                    templateUrl: template_path + '/plugins/acme/static/index.html',
                    controller: ['$scope', '$rootScope', function ($scope, $rootScope) {
                        $rootScope.navbar_loaded = true;
                    }]
                };
            })
            // var plugins_list = [
            //     'acme'
            // ];
            // plugins_list.forEach(function (i) {
            //     var directives_name = 'plugins' + i;
            //     angular.module('inpanel.directives', []).directive(directives_name, function () {
            //         return {
            //             restrict: 'A',
            //             transclude: true,
            //             scope: {},
            //             replace: true,
            //             templateUrl: template_path + '/plugins/' + i + '/index.html',
            //             controller: ['$scope', '$rootScope', function ($scope, $rootScope) {
            //                 $rootScope.navbar_loaded = true;
            //             }]
            //         };
            //     })
            // });
            console.log('加载路由')
            // inpanel.config(['$routeProvider', function ($routeProvider) {
            //     var _r = function (t, c, a) {
            //         var r = {
            //             templateUrl: template_path + t + '.html?_v=' + _v,
            //             controller: c,
            //             reloadOnSearch: false
            //         };
            //         if (!a) r.resolve = Auth;
            //         return r;
            //     };
            //     $routeProvider.
            //     when('/plugins/acme', {redirectTo: '/plugins/acme/index'}).
            //     when('/plugins/acme/index', PluginsRouters);
            // }]);
        };
    }
];

var PluginsRouters = function () {
    var t = 'acme/index'; // acme/index.html
    var c = [
        '$scope', 'Module', function ($scope, Module) {
            var module = 'plugins';
            var section = Module.getSection();
            Module.init(module, '应用管理');
            $scope.loaded = false;
            console.log($scope, section);
            $scope.load = function () {
                $scope.loaded = true;
            };
        }
    ];
    var p = {
        templateUrl: template_path + '/plugins/' + t + '.html?_v=' + _v,
        controller: c,
        reloadOnSearch: false,
        resolve: Auth
    };
    console.log(p);
    return p;
};

var PluginsCtrl = [
    '$scope', 'Module',
    function ($scope, Module) {
        var module = 'plugins';
        var section = Module.getSection();
        Module.init(module, '应用管理');
        $scope.loaded = false;
        console.log('插件', section);
        $scope.load = function () {
            $scope.loaded = true;
        };
    }
];

