var TaskCtrl = ['$scope', 'Module',
    function ($scope, Module) {
        var module = 'task';
        Module.init(module, '计划任务');
        $scope.loaded = false;

        var section = Module.getSection();
        $scope.load = function () {
            $scope.loaded = true;
            if (section && section == 'base') {
                $scope.loadBase();
            } else if (section && section == 'cron') {
                $scope.loadCron();
            } else {
                $scope.loadBase();
            }
        }
        $scope.loadBase = function () {
            $scope.sec('base');
            Module.setSection('base');
        };
        $scope.loadCron = function () {
            $scope.sec('cron');
            Module.setSection('cron');
        };
    }
];

var TaskCronListCtrl = [
    '$scope', 'Module',
    function ($scope, Module) {
        var module = 'task.cron.list';
        Module.init(module, '当前 Cron 作业');
        $scope.loaded = false;
        $scope.load = function () {
            $scope.loaded = true;
        }
    }
];

var TaskCronNewCtrl = [
    '$scope', 'Module', 'Request',
    function ($scope, Module, Request) {
        var module = 'task.cron.new';
        Module.init(module, '添加新 Cron 作业');
        $scope.loaded = false;

        $scope.common_options = '';
        $scope.cron_time = {
            minute: '',
            hour: '',
            day: '',
            month: '',
            weekday: ''
        };
        $scope.options = {
            minute: '',
            hour: '',
            day: '',
            month: '',
            weekday: ''
        };

        $scope.task_time = '';
        $scope.task_user = '';
        $scope.task_email = '';
        $scope.task_command = '';
        $scope.load = function () {
            $scope.loaded = true;
            if (!$scope.users) {
                Request.post('/operation/user', {
                    'action': 'listuser',
                    'fullinfo': false
                }, function (data) {
                    if (data.code == 0) {
                        $scope.users = data.data;
                    }
                }, false, true);
            }
        };

        $scope.$watch('cron_time', function (n) {
            $scope.task_time = n.minute + ' ' + n.hour + ' ' + n.day + ' ' + n.month + ' ' + n.weekday;
        }, true);
        $scope.select_common_option = function () {
            var option = $scope.common_options;
            console.log($scope.common_options);
            if (option && option != '') {
                var option_array = option.split(' ');

                $scope.cron_time.minute = option_array[0];
                $scope.cron_time.hour = option_array[1];
                $scope.cron_time.day = option_array[2];
                $scope.cron_time.month = option_array[3];
                $scope.cron_time.weekday = option_array[4];

                $scope.options.minute = option_array[0];
                $scope.options.hour = option_array[1];
                $scope.options.day = option_array[2];
                $scope.options.month = option_array[3];
                $scope.options.weekday = option_array[4];
            } else {
                for (var i in $scope.cron_time) {
                    $scope.cron_time[i] = ''
                }
                for (var j in $scope.options) {
                    $scope.options[j] = ''
                }
            }
        };
        $scope.input_single_option = function (type) {
            if (typeof type === 'undefined' || type === '') {
                return
            };
            $scope.options[type] = $scope.cron_time[type];
        };
        $scope.select_single_option = function (type) {
            if (typeof type === 'undefined' || type === '') {
                return
            };
            $scope.cron_time[type] = $scope.options[type];
        };
        $scope.addCronJobs = function () {
            var data = {
                action: 'add_cron_jobs',
                command: $scope.task_time + ' ' + $scope.task_command
            }
            console.log(data)
            // Request.post('/operation/task', {
            //     action: 'add',
            //     username: $scope.username,
            //     password: $scope.password ? hex_md5($scope.password) : '',
            //     passwordc: $scope.passwordc ? hex_md5($scope.passwordc) : '',
            //     passwordcheck: $scope.passwordcheck
            // }, function(data) {
            //     if (data.code == 0) $scope.loadAuthInfo();
            // });
        };
    }
];