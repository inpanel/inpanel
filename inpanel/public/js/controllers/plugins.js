var PluginsHome = [
    '$scope', 'Module', 'Request',
    function ($scope, Module, Request) {
        var module = 'plugins';
        Module.init(module, '插件管理');
        $scope.loaded = false;
        $scope.plugins = [];

        $scope.load = function () {
            $scope.loaded = true;
            $scope.loadPlugins();
        };

        $scope.loadPlugins = function () {
            Request.get('/api/plugins/list', function (res) {
                if (res.code === 0) {
                    $scope.plugins = res.data;
                }
            });
        };

        $scope.togglePlugin = function (plugin) {
            Request.post('/api/plugins/toggle', {
                id: plugin.id,
                enable: !plugin.enabled
            }, function (res) {
                if (res.code === 0) {
                    plugin.enabled = res.data.enabled;
                }
            });
        };

        $scope.uninstallPlugin = function (plugin) {
            if (!confirm('确定要卸载插件 ' + plugin.name + ' 吗？')) {
                return;
            }
            Request.post('/api/plugins/uninstall', {
                id: plugin.id
            }, function (res) {
                if (res.code === 0) {
                    $scope.loadPlugins();
                }
            });
        };
    }
];

var PluginDetailCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'plugins';
        var pluginId = $routeParams.name;
        Module.init(module, '插件详情');
        $scope.loaded = false;
        $scope.pluginId = pluginId;
        $scope.pluginInfo = {};
        $scope.pluginConfig = {};
        $scope.activeTab = 'home';
        $scope.loadedScripts = [];

        $scope.load = function () {
            $scope.loaded = true;
            $scope.loadPluginInfo();
            $scope.loadPluginConfig();
        };

        $scope.loadPluginInfo = function () {
            Request.get('/api/plugins/info?id=' + pluginId, function (res) {
                if (res.code === 0) {
                    $scope.pluginInfo = res.data;
                }
            });
        };

        $scope.loadPluginConfig = function () {
            Request.get('/api/plugins/config?id=' + pluginId, function (res) {
                if (res.code === 0) {
                    $scope.pluginConfig = res.data;
                }
            });
        };

        $scope.sec = function (tab) {
            $scope.activeTab = tab;
        };

        $scope.refreshPlugin = function () {
            $scope.loadPluginInfo();
            $scope.loadPluginConfig();
            $scope.loadPluginAssets();
        };

        $scope.loadPluginAssets = function() {
            $scope.unloadPluginAssets();
            
            var scriptUrl = '/page/plugins/' + pluginId + '/script.js?' + Date.now();
            var script = document.createElement('script');
            script.src = scriptUrl;
            script.type = 'text/javascript';
            script.onload = function() {
                console.log('Plugin script loaded:', scriptUrl);
            };
            script.onerror = function() {
                console.warn('Plugin script load failed:', scriptUrl);
            };
            document.body.appendChild(script);
            $scope.loadedScripts.push(script);
        };

        $scope.unloadPluginAssets = function() {
            for (var i = 0; i < $scope.loadedScripts.length; i++) {
                var script = $scope.loadedScripts[i];
                if (script.parentNode) {
                    script.parentNode.removeChild(script);
                }
            }
            $scope.loadedScripts = [];
        };

        $scope.saveConfig = function () {
            var data = { id: pluginId };
            for (var key in $scope.pluginConfig) {
                data[key] = $scope.pluginConfig[key];
            }
            Request.post('/api/plugins/config', data, function (res) {
                if (res.code === 0) {
                    alert('配置保存成功');
                }
            });
        };
    }
];

var PluginConfigCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'plugins';
        var pluginId = $routeParams.name;
        Module.init(module, '插件配置');
        $scope.loaded = false;
        $scope.pluginId = pluginId;
        $scope.pluginConfig = {};
        $scope.configSchema = {};

        $scope.load = function () {
            $scope.loaded = true;
            $scope.loadPluginConfig();
            $scope.loadConfigSchema();
        };

        $scope.loadPluginConfig = function () {
            Request.get('/api/plugins/config?id=' + pluginId, function (res) {
                if (res.code === 0) {
                    $scope.pluginConfig = res.data;
                }
            });
        };

        $scope.loadConfigSchema = function () {
            Request.get('/api/plugins/info?id=' + pluginId, function (res) {
                if (res.code === 0) {
                    $scope.configSchema = res.data.config_schema || {};
                }
            });
        };

        $scope.saveConfig = function () {
            var data = { id: pluginId };
            for (var key in $scope.pluginConfig) {
                data[key] = $scope.pluginConfig[key];
            }
            Request.post('/api/plugins/config', data, function (res) {
                if (res.code === 0) {
                    alert('配置保存成功');
                }
            });
        };
    }
];

var PluginInfoCtrl = [
    '$scope', '$routeParams', 'Module', 'Request',
    function ($scope, $routeParams, Module, Request) {
        var module = 'plugins';
        var pluginId = $routeParams.name;
        Module.init(module, '插件信息');
        $scope.loaded = false;
        $scope.pluginInfo = {};

        $scope.load = function () {
            $scope.loaded = true;
            $scope.loadPluginInfo();
        };

        $scope.loadPluginInfo = function () {
            Request.get('/api/plugins/info?id=' + pluginId, function (res) {
                if (res.code === 0) {
                    $scope.pluginInfo = res.data;
                }
            });
        };
    }
];