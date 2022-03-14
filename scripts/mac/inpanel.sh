#!/bin/sh
#
# inpanel - this script starts and stops the inpanel daemon
#
# chkconfig:   - 85 15
# description: InPanel is a web-based linux VPS management tools
# processname: inpanel
# pidfile:     /usr/local/var/run/inpanel.pid

# Source function library.
. /etc/rc.common

exec="/usr/local/inpanel/inpanel"
# pidfile="/usr/local/var/run/inpanel.pid"

StartService() {
    exec
}

StopService() {
    return 0
}

RestartService() {
    stop
    start
}

case "$1" in
    start)
        StartService
        ;;
    stop)
        StopService
        ;;
    restart)
        RestartService
        ;;
    *)
        echo $"Usage: $0 {start|stop|restart|}"
        exit 2
        ;;
esac
