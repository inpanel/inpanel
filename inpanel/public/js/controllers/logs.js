var LogsCtrl = [
    '$scope', '$routeParams', 'Module', 'Request', 'Message',
    function ($scope, $routeParams, Module, Request, Message) {
        var module = 'logs';
        Module.init(module, '日志管理');

        $scope.loaded = false;
        $scope.activeTab = 'inpanel';
        $scope.panelSubTab = 'operation';
        $scope.fileSubTab = 'operation';
        $scope.websiteSubTab = 'runtime';
        $scope.sshFilter = 'all';
        $scope.loginFilter = 'all';

        // Panel logs data
        $scope.operationLogs = [];
        $scope.loginLogs = [];
        $scope.errorLogContent = '';
        $scope.taskLogs = [];

        // File logs data
        $scope.filesLogs = [];
        $scope.filesAccessLogs = [];

        // Cron logs data
        $scope.cronLogs = [];

        // SSH logs data
        $scope.sshLogs = [];

        // Website logs data
        $scope.websiteRuntimeContent = '';
        $scope.websiteErrorContent = '';
        $scope.websiteServerType = 'nginx';

        // Service logs data
        $scope.serviceList = [];
        $scope.selectedService = null;
        $scope.selectedLogPath = '';
        $scope.serviceLogContent = '';

        // 根据 URL 路由参数设置初始 tab
        var initTab = function () {
            var routeTab = $routeParams.tab;
            if (routeTab) {
                var validTabs = ['inpanel', 'ssh', 'website', 'service', 'files', 'cron'];
                if (validTabs.indexOf(routeTab) >= 0) {
                    $scope.activeTab = routeTab;
                }
            }
        };

        $scope.load = function () {
            $scope.loaded = true;
            initTab();
            $scope.switchTab($scope.activeTab);
        };

        $scope.switchTab = function (tab) {
            $scope.activeTab = tab;
            if (tab === 'inpanel') {
                $scope.loadPanelLogs($scope.panelSubTab);
            } else if (tab === 'ssh') {
                $scope.loadSSHLogs();
            } else if (tab === 'website') {
                $scope.loadWebsiteLogs($scope.websiteSubTab);
            } else if (tab === 'service') {
                $scope.loadServiceList();
            } else if (tab === 'files') {
                $scope.fileSubTab = 'operation';
                $scope.loadFilesLogs();
            } else if (tab === 'cron') {
                $scope.loadCronLogs();
            }
        };

        // ========== Panel Logs ==========

        $scope.switchPanelSubTab = function (subTab) {
            $scope.panelSubTab = subTab;
            $scope.loadPanelLogs(subTab);
        };

        $scope.loadPanelLogs = function (subTab) {
            if (subTab === 'operation') {
                $scope.loadOperationLogs();
            } else if (subTab === 'login') {
                $scope.loadLoginLogs();
            } else if (subTab === 'error') {
                $scope.loadErrorLog();
            } else if (subTab === 'task') {
                $scope.loadTaskLogs();
            }
        };

        $scope.loadOperationLogs = function () {
            Request.get('/api/logs/operation', function (data) {
                if (data.code === 0) {
                    $scope.operationLogs = data.data;
                }
            });
        };

        $scope.loadLoginLogs = function () {
            Request.get('/api/logs/login?status=' + $scope.loginFilter, function (data) {
                if (data.code === 0) {
                    $scope.loginLogs = data.data;
                }
            });
        };

        $scope.filterLoginLogs = function (filter) {
            $scope.loginFilter = filter;
            $scope.loadLoginLogs();
        };

        $scope.loadErrorLog = function () {
            Request.get('/api/logs/error', function (data) {
                if (data.code === 0) {
                    $scope.errorLogContent = data.data.content;
                }
            });
        };

        $scope.loadTaskLogs = function () {
            Request.get('/api/logs/task', function (data) {
                if (data.code === 0) {
                    $scope.taskLogs = data.data;
                }
            });
        };

        // ========== File Logs ==========

        $scope.switchFileSubTab = function (subTab) {
            $scope.fileSubTab = subTab;
            if (subTab === 'operation') {
                $scope.loadFilesLogs();
            } else if (subTab === 'access') {
                $scope.loadFilesAccessLogs();
            }
        };

        $scope.loadFilesLogs = function () {
            Request.get('/api/logs/files', function (data) {
                if (data.code === 0) {
                    $scope.filesLogs = data.data;
                }
            });
        };

        $scope.loadFilesAccessLogs = function () {
            Request.get('/api/logs/files_access', function (data) {
                if (data.code === 0) {
                    $scope.filesAccessLogs = data.data;
                }
            });
        };

        // ========== Cron Logs ==========

        $scope.loadCronLogs = function () {
            Request.get('/api/logs/cron', function (data) {
                if (data.code === 0) {
                    $scope.cronLogs = data.data;
                }
            });
        };

        // ========== SSH Logs ==========

        $scope.loadSSHLogs = function () {
            Request.get('/api/logs/ssh?status=' + $scope.sshFilter, function (data) {
                if (data.code === 0) {
                    $scope.sshLogs = data.data;
                }
            });
        };

        $scope.filterSSHLogs = function (filter) {
            $scope.sshFilter = filter;
            $scope.loadSSHLogs();
        };

        // ========== Website Logs ==========

        $scope.switchWebsiteSubTab = function (subTab) {
            $scope.websiteSubTab = subTab;
            $scope.loadWebsiteLogs(subTab);
        };

        $scope.loadWebsiteLogs = function (subTab) {
            if (subTab === 'runtime') {
                Request.get('/api/logs/website_runtime?type=' + $scope.websiteServerType, function (data) {
                    if (data.code === 0) {
                        $scope.websiteRuntimeContent = data.data.content;
                    }
                });
            } else if (subTab === 'error') {
                Request.get('/api/logs/website_error?type=' + $scope.websiteServerType, function (data) {
                    if (data.code === 0) {
                        $scope.websiteErrorContent = data.data.content;
                    }
                });
            }
        };

        $scope.refreshWebsiteLogs = function () {
            $scope.loadWebsiteLogs($scope.websiteSubTab);
        };

        $scope.exportWebsiteLogs = function () {
            var content = $scope.websiteSubTab === 'runtime' ? $scope.websiteRuntimeContent : $scope.websiteErrorContent;
            var type = 'website_' + $scope.websiteSubTab;
            Request.post('/api/logs/export', {
                type: type,
                content: content
            }, function (data) {
                // Export handled via download
            }, false, true);
        };

        // ========== Service Logs ==========

        $scope.loadServiceList = function () {
            Request.get('/api/logs/service_list', function (data) {
                if (data.code === 0) {
                    $scope.serviceList = data.data;
                    if (data.data.length > 0) {
                        $scope.selectService(data.data[0]);
                    }
                }
            });
        };

        $scope.selectService = function (service) {
            $scope.selectedService = service;
            if (service.logs && service.logs.length > 0) {
                $scope.selectedLogPath = service.logs[0].path;
                $scope.loadServiceLogContent(service.id, service.logs[0].path);
            } else {
                $scope.serviceLogContent = '';
            }
        };

        $scope.selectServiceLogFile = function (logInfo) {
            $scope.selectedLogPath = logInfo.path;
            $scope.loadServiceLogContent($scope.selectedService.id, logInfo.path);
        };

        $scope.loadServiceLogContent = function (serviceId, logPath) {
            Request.get('/api/logs/service_log?id=' + encodeURIComponent(serviceId) + '&path=' + encodeURIComponent(logPath || ''), function (data) {
                if (data.code === 0) {
                    $scope.serviceLogContent = data.data.content;
                }
            });
        };

        // ========== Export ==========

        $scope.exportLog = function (type, content) {
            if (!content) {
                Message.setError('没有可导出的内容！');
                return;
            }
            Request.post('/api/logs/export', {
                action: 'export',
                type: type,
                content: content
            }, function (data) {
                // Response is a file download
            });
        };

        // ========== Refresh ==========

        $scope.refreshCurrent = function () {
            if ($scope.activeTab === 'inpanel') {
                $scope.loadPanelLogs($scope.panelSubTab);
            } else if ($scope.activeTab === 'ssh') {
                $scope.loadSSHLogs();
            } else if ($scope.activeTab === 'website') {
                $scope.loadWebsiteLogs($scope.websiteSubTab);
            } else if ($scope.activeTab === 'files') {
                $scope.loadFilesLogs();
            } else if ($scope.activeTab === 'cron') {
                $scope.loadCronLogs();
            }
        };
    }
];
