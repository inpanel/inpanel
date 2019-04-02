var releasetime = '2019-04-02 15:49:23 GMT';
var _v = new Date(releasetime.replace(/-/g, '/')).getTime() / 1000;
//if (1) _v += Math.random(); // ie test mode
angular.module('inpanel', ['inpanel.services', 'inpanel.directives', 'inpanel.filters']).
config(['$routeProvider', function ($routeProvider) {
    var _r = function (t, c, a) {
        var r = {
            templateUrl: template_path + '/partials/' + t + '.html?_v=' + _v,
            controller: c,
            reloadOnSearch: false
        };
        if (!a) r.resolve = Auth;
        return r;
    };
    $routeProvider.
    when('/', _r('login', LoginCtrl, true)).
    when('/main', _r('main', MainCtrl)).
    when('/service/nginx', _r('service/nginx', ServiceNginxCtrl)).
    when('/service/apache', _r('service/apache', ServiceApacheCtrl)).
    when('/service/lighttpd', _r('service/lighttpd', ServiceLighttpdCtrl)).
    when('/service/tomcat', _r('service/tomcat', ServiceTomcatCtrl)).
    when('/service/vsftpd', _r('service/vsftpd', ServiceVsftpdCtrl)).
    when('/service/proftpd', _r('service/proftpd', ServiceProFTPDCtrl)).
    when('/service/pureftpd', _r('service/pureftpd', ServicePureFTPdCtrl)).
    when('/service/mysql', _r('service/mysql', ServiceMySQLCtrl)).
    when('/service/mariadb', _r('service/mariadb', ServiceMariaDBCtrl)).
    when('/service/redis', _r('service/redis', ServiceRedisCtrl)).
    when('/service/memcache', _r('service/memcache', ServiceMemcacheCtrl)).
    when('/service/mongodb', _r('service/mongodb', ServiceMongoDBCtrl)).
    when('/service/php', _r('service/php', ServicePHPCtrl)).
    when('/service/sendmail', _r('service/sendmail', ServiceSendmailCtrl)).
    when('/service/ssh', _r('service/ssh', ServiceSSHCtrl)).
    when('/service/iptables', _r('service/iptables', ServiceIPTablesCtrl)).
    when('/service/cron', _r('service/cron', ServiceCronCtrl)).
    when('/service/ntp', _r('service/ntp', ServiceNTPCtrl)).
    when('/service/named', _r('service/named', ServiceNamedCtrl)).
    when('/service/samba', _r('service/samba', ServiceSambaCtrl)).
    when('/service', _r('service/index', ServiceCtrl)).
    when('/file', _r('file/file', FileCtrl)).
    when('/file/go#(:path)', _r('file/file', FileCtrl)).
    when('/file/trash', _r('file/trash', FileTrashCtrl)).
    when('/site', _r('site/index', SiteCtrl)).
    when('/site/nginx/:section', _r('site/nginx/site', SiteNginxCtrl)).
    when('/site/apache/:section', _r('site/apache/site', SiteApacheCtrl)).
    when('/database', _r('database/index', DatabaseCtrl)).
    when('/database/mysql/db/new', _r('database/mysql/dbnew', DatabaseMySQLNewDBCtrl)).
    when('/database/mysql/db/edit/:section', _r('database/mysql/dbedit', DatabaseMySQLEditDBCtrl)).
    when('/database/mysql/user/new', _r('database/mysql/usernew', DatabaseMySQLNewUserCtrl)).
    when('/database/mysql/user/edit/:section', _r('database/mysql/useredit', DatabaseMySQLEditUserCtrl)).
    when('/ftp', _r('ftp', FtpCtrl)).
    when('/utils', _r('utils/index', UtilsCtrl)).
    when('/utils/user', _r('utils/user', UtilsUserCtrl)).
    when('/utils/process', _r('utils/process', UtilsProcessCtrl)).
    when('/utils/network', _r('utils/network', UtilsNetworkCtrl)).
    when('/utils/time', _r('utils/time', UtilsTimeCtrl)).
    when('/utils/cron', _r('utils/cron', UtilsCronCtrl)).
    when('/utils/ssl', _r('utils/ssl', UtilsSSLCtrl)).
    when('/utils/repository', _r('utils/repository', UtilsRepositoryCtrl)).
    when('/storage', _r('storage/index', StorageCtrl)).
    when('/storage/remote/:section', _r('storage/remote', StorageRemoteCtrl)).
    when('/storage/autofm', _r('storage/autofm', StorageAutoFMCtrl)).
    when('/storage/movedata', _r('storage/movedata', StorageMoveDataCtrl)).
    when('/storage/backup', _r('storage/backup', BackupCtrl)).
    when('/ecs', _r('ecs/ecs', ECSCtrl)).
    when('/ecs/index', _r('ecs/index', ECSIndexCtrl)).
    when('/ecs/account', _r('ecs/account', ECSAccountCtrl)).
    when('/ecs/:section', _r('ecs/setting', ECSSettingCtrl)).
    when('/setting', _r('setting', SettingCtrl)).
    when('/secure', _r('secure', SecureCtrl)).
    when('/application', _r('application/index', ApplicationCtrl)).
    when('/application/shadowsocks', _r('application/shadowsocks', ApplicationShadowsocksCtrl)).
    when('/application/acme', _r('application/acme', ApplicationCACMEtrl)).
    when('/log', _r('log', LogCtrl)).
    when('/logout', _r('logout', LogoutCtrl)).
    when('/sorry', _r('sorry', SorryCtrl)).
    otherwise({
        redirectTo: '/sorry'
    });
}]).
run(['$rootScope', '$location', 'Request', function ($rootScope, $location, Request) {
    $rootScope.sec = function (sec) {
        $location.search('s', sec)
    };

    $rootScope.virt = '?';
    $rootScope.checkVirt = function (callback) {
        if ($rootScope.virt != '?') return;
        Request.get('/query/server.virt', function (data) {
            $rootScope.virt = data['server.virt'];
            if (callback) callback.call();
        });
    };

    // store some global data
    $rootScope.$mysql = {
        'password': '',
        'password_validated': false
    };

    $rootScope.$ecs = {
        'access_key_id': '',
        'page_size': 10,
        'page_number': 1
    };
    $rootScope.$proxyroot = location_path;
}]).
value('version', {
    'version': '1.1.1',
    'build': '19',
    'releasetime': releasetime,
    'changelog': 'http://inpanel.org/changelog.html'
});

var Auth = {
    // auth should be done before enter the module
    auth: function ($q, Auth, Message) {
        var deferred = $q.defer();
        Message.setInfo('正在加载，请稍候...', true);
        Auth.required(function (authed) {
            Message.setInfo(false);
            if (authed) deferred.resolve();
        }, function (status) {
            if (status == 403) {
                Message.setError('身份认证失败，请<a href="#/">重新登录</a>！');
            } else {
                Message.setError('对不起，加载失败！（网络异常或服务器故障）');
            }
        });
        return deferred.promise;
    },
    // auth status would expired in 30 mins if no any client action
    // we should active it every 5 mins if client is still active
    auto_auth: function ($rootScope, $location, Auth, Timeout) {
        if (!$rootScope._auth_check_inited) {
            $rootScope._auth_check_inited = true;
            // auto update auth if client active in the pass 5 mins
            // and if no active in the pass 25 mins, a dialog will come out to confirm
            var check_timeout = 300 * 1000;
            var auth_timeout = 2500 * 1000;
            var last_active = new Date().getTime();

            $(document).mousemove(function () {
                last_active = new Date().getTime();
            });
            $(document).keydown(function () {
                last_active = new Date().getTime();
            });

            var active = (function () {
                var stop_check = false;
                var now = new Date().getTime();
                if (now - last_active < check_timeout) {
                    Auth.required();
                } else if (now - last_active > auth_timeout) {
                    // check if the cookie ready to expiring
                    stop_check = true;
                    Auth.getlastactive(function (lastactive) {
                        lastactive = parseInt(lastactive) * 1000;
                        if (now - lastactive > auth_timeout) {
                            // blink the title
                            var oldHtmlTitle = $rootScope.htmlTitle;
                            var blinks = ['登录超时', '!!!!!!!!'];
                            var blink_i = 0;
                            var stop_blink = false;
                            var toggletitle = function () {
                                if (!stop_blink) {
                                    $rootScope.htmlTitle = blinks[(blink_i++) % 2];
                                    Timeout(toggletitle, 1000, false, true, '_authtimeout_title');
                                } else {
                                    $rootScope.htmlTitle = oldHtmlTitle;
                                }
                            };
                            toggletitle();
                            $rootScope._authrenew = function () {
                                last_active = new Date().getTime();
                                stop_blink = true;
                                Auth.required();
                                Timeout(active, check_timeout, false, true, '_authtimeout');
                            };
                            $('#_authconfirm').modal();
                        } else {
                            last_active = lastactive;
                            Timeout(active, check_timeout, false, true, '_authtimeout');
                        }
                    });
                }
                if (!stop_check && $location.path() != '/')
                    Timeout(active, check_timeout, false, true, '_authtimeout');
            });
            Timeout(active, check_timeout, false, true, '_authtimeout');
        }
    }
};
Auth.auth.$inject = ['$q', 'Auth', 'Message'];
Auth.auto_auth.$inject = ['$rootScope', '$location', 'Auth', 'Timeout'];

var getCookie = function (name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
};