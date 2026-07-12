var ContainerCtrl = [
    '$scope', 'Module', 'Request', 'Message', 'Timeout',
    function ($scope, Module, Request, Message, Timeout) {
        var module = 'container';
        Module.init(module, 'Docker 容器管理');
        Module.initSection('overview');
        $scope.loaded = false;

        // 概览数据
        $scope.overview = null;
        // 容器列表
        $scope.containers = [];
        $scope.containersLoading = false;
        $scope.showAllContainers = false;
        // 镜像列表
        $scope.images = [];
        $scope.imagesLoading = false;
        // 仓库搜索
        $scope.searchKeyword = '';
        $scope.searchResults = [];
        $scope.searching = false;
        $scope.pulling = false;
        // 网络列表
        $scope.networks = [];
        $scope.networksLoading = false;

        var section = Module.getSection();
        $scope.load = function () {
            $scope.loaded = true;
            if (section) {
                $scope.sec(section);
                Module.setSection(section);
                $scope.loadSection(section);
            } else {
                $scope.loadOverview();
            }
        };

        $scope.loadSection = function (sec) {
            if (sec == 'overview') {
                $scope.loadOverview();
            } else if (sec == 'containers') {
                $scope.loadContainers();
            } else if (sec == 'images') {
                $scope.loadImages();
            } else if (sec == 'repo') {
                // 仓库页不自动加载
            } else if (sec == 'networks') {
                $scope.loadNetworks();
            }
        };

        $scope.tab_sec = function (sec) {
            $scope.sec(sec);
            Module.setSection(sec);
            $scope.loadSection(sec);
        };

        // 概览
        $scope.loadOverview = function () {
            $scope.overviewLoading = true;
            Request.post('/api/operation/docker', {
                action: 'overview'
            }, function (data) {
                $scope.overviewLoading = false;
                if (data.code == 0) {
                    $scope.overview = data.data;
                }
            }, false, true);
        };

        // Docker 服务控制
        $scope.dockerService = function (op) {
            Request.post('/api/operation/docker', {
                action: 'service',
                op: op
            }, function (data) {
                if (data.code == 0) {
                    Timeout($scope.loadOverview, 1000, module);
                }
            });
        };

        // 容器管理
        $scope.loadContainers = function () {
            $scope.containersLoading = true;
            Request.post('/api/operation/docker', {
                action: 'containers',
                all: $scope.showAllContainers ? 'true' : 'false'
            }, function (data) {
                $scope.containersLoading = false;
                if (data.code == 0) {
                    $scope.containers = data.data;
                }
            }, false, true);
        };

        $scope.toggleAllContainers = function () {
            $scope.showAllContainers = !$scope.showAllContainers;
            $scope.loadContainers();
        };

        $scope.containerControl = function (containerId, op) {
            var opLabel = {'start': '启动', 'stop': '停止', 'restart': '重启', 'remove': '删除'};
            Request.post('/api/operation/docker', {
                action: 'container_control',
                id: containerId,
                op: op
            }, function (data) {
                if (data.code == 0) {
                    Timeout($scope.loadContainers, 500, module);
                }
            });
        };

        // 镜像管理
        $scope.loadImages = function () {
            $scope.imagesLoading = true;
            Request.post('/api/operation/docker', {
                action: 'images'
            }, function (data) {
                $scope.imagesLoading = false;
                if (data.code == 0) {
                    $scope.images = data.data;
                }
            }, false, true);
        };

        $scope.removeImage = function (imageId) {
            Request.post('/api/operation/docker', {
                action: 'remove_image',
                id: imageId
            }, function (data) {
                if (data.code == 0) {
                    $scope.loadImages();
                }
            });
        };

        // 镜像仓库
        $scope.searchImages = function () {
            if (!$scope.searchKeyword) {
                Message.setError('请输入搜索关键词！');
                return;
            }
            $scope.searching = true;
            Request.post('/api/operation/docker', {
                action: 'search_images',
                keyword: $scope.searchKeyword
            }, function (data) {
                $scope.searching = false;
                if (data.code == 0) {
                    $scope.searchResults = data.data;
                }
            }, false, true);
        };

        $scope.pullImage = function (imageName) {
            $scope.pulling = true;
            Request.post('/api/operation/docker', {
                action: 'pull_image',
                name: imageName
            }, function (data) {
                $scope.pulling = false;
                if (data.code == 0) {
                    Message.setSuccess(data.msg);
                }
            });
        };

        // 网络管理
        $scope.loadNetworks = function () {
            $scope.networksLoading = true;
            Request.post('/api/operation/docker', {
                action: 'networks'
            }, function (data) {
                $scope.networksLoading = false;
                if (data.code == 0) {
                    $scope.networks = data.data;
                }
            }, false, true);
        };

        $scope.removeNetwork = function (networkId) {
            Request.post('/api/operation/docker', {
                action: 'remove_network',
                id: networkId
            }, function (data) {
                if (data.code == 0) {
                    $scope.loadNetworks();
                }
            });
        };
    }
];
