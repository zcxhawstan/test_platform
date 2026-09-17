#!/bin/bash
# 测试平台 WSL 部署启停脚本（无 systemd 环境）
# 用法: ./deploy.sh {start|stop|restart|status}
set -u

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PY="$HOME/test_platform_venv/bin/python"
VENV_BIN="$HOME/test_platform_venv/bin"
PID_DIR="/tmp/test_platform_pids"
LOG_DIR="/tmp"
MYSQL_PWD="${MYSQL_PWD:-TpUser@2026}"

mkdir -p "$PID_DIR"

# ---- 各服务状态探测 ----

mysql_running() {
    # 用业务账号走TCP探测（默认socket对普通用户无权限）
    mysqladmin -utpuser -p"$MYSQL_PWD" -h127.0.0.1 ping 2>/dev/null | grep -q 'alive'
}

redis_running() {
    redis-cli ping 2>/dev/null | grep -q PONG
}

gunicorn_running() {
    [ -f "$PID_DIR/gunicorn.pid" ] && kill -0 "$(cat "$PID_DIR/gunicorn.pid")" 2>/dev/null
}

# 兼容历史手动部署：清理不在pidfile管理内的旧gunicorn（会占住8000端口导致新实例起不来）
cleanup_stale_gunicorn() {
    local managed_pid
    managed_pid=$(cat "$PID_DIR/gunicorn.pid" 2>/dev/null || echo '')
    for pid in $(pgrep -f "gunicorn Django.wsgi" 2>/dev/null); do
        if [ -z "$managed_pid" ] || [ "$pid" != "$managed_pid" ]; then
            kill "$pid" 2>/dev/null
        fi
    done
    # 等端口释放
    sleep 2
}

celery_worker_running() {
    pgrep -f "celery -A Django worker" >/dev/null 2>&1
}

celery_beat_running() {
    pgrep -f "celery -A Django beat" >/dev/null 2>&1
}

# ---- 启动 ----

start_mysql() {
    if mysql_running; then
        echo "[OK] MySQL 已在运行"
        return 0
    fi
    echo "[..] 启动 MySQL ..."
    sudo -n mkdir -p /run/mysqld 2>/dev/null
    sudo -n chown mysql:mysql /run/mysqld 2>/dev/null
    if sudo -n /usr/sbin/mysqld --user=mysql --daemonize >/dev/null 2>&1; then
        sleep 2
        mysql_running && echo "[OK] MySQL 已启动" || { echo "[FAIL] MySQL 启动失败"; return 1; }
    else
        echo "[FAIL] MySQL 启动失败（sudo 需要密码时请手动执行: sudo /usr/sbin/mysqld --user=mysql --daemonize）"
        return 1
    fi
}

start_redis() {
    if redis_running; then
        echo "[OK] Redis 已在运行"
        return 0
    fi
    echo "[..] 启动 Redis ..."
    sudo -n service redis-server start >/dev/null 2>&1
    sleep 1
    redis_running && echo "[OK] Redis 已启动" || { echo "[FAIL] Redis 启动失败"; return 1; }
}

start_gunicorn() {
    if gunicorn_running; then
        echo "[OK] gunicorn 已在运行"
        return 0
    fi
    echo "[..] 启动 gunicorn :8000 ..."
    cleanup_stale_gunicorn
    cd "$BASE_DIR"
    "$VENV_BIN/gunicorn" Django.wsgi:application \
        --bind 0.0.0.0:8000 --workers 3 \
        --daemon --pid "$PID_DIR/gunicorn.pid" \
        --error-logfile "$LOG_DIR/gunicorn_err.log" \
        --access-logfile "$LOG_DIR/gunicorn_acc.log"
    sleep 3
    if gunicorn_running && curl -s -m 5 -o /dev/null http://127.0.0.1:8000/api/auth/users/login/ -X POST \
        -H 'Content-Type: application/json' -d '{"username":"__healthcheck__","password":"x"}'; then
        echo "[OK] gunicorn 已启动（API 可达）"
    else
        echo "[WARN] gunicorn 进程已拉起但API未响应，请查 $LOG_DIR/gunicorn_err.log"
    fi
}

start_celery_worker() {
    if celery_worker_running; then
        echo "[OK] celery worker 已在运行"
        return 0
    fi
    echo "[..] 启动 celery worker ..."
    cd "$BASE_DIR"
    nohup "$VENV_BIN/celery" -A Django worker --loglevel=info > "$LOG_DIR/celery_worker.log" 2>&1 &
    sleep 5
    celery_worker_running && echo "[OK] celery worker 已启动" || { echo "[FAIL] celery worker 启动失败"; return 1; }
}

start_celery_beat() {
    if celery_beat_running; then
        echo "[OK] celery beat 已在运行"
        return 0
    fi
    echo "[..] 启动 celery beat ..."
    cd "$BASE_DIR"
    nohup "$VENV_BIN/celery" -A Django beat --loglevel=info > "$LOG_DIR/celery_beat.log" 2>&1 &
    sleep 3
    celery_beat_running && echo "[OK] celery beat 已启动" || { echo "[FAIL] celery beat 启动失败"; return 1; }
}

do_start() {
    start_mysql
    start_redis
    start_gunicorn
    start_celery_worker
    start_celery_beat
    echo ""
    echo "启动完成。访问: http://localhost:8000"
}

# ---- 停止 ----

stop_gunicorn() {
    if [ -f "$PID_DIR/gunicorn.pid" ]; then
        kill "$(cat "$PID_DIR/gunicorn.pid")" 2>/dev/null
        rm -f "$PID_DIR/gunicorn.pid"
        sleep 2
        # 兜底清理所有残留实例
        pkill -f "gunicorn Django.wsgi" 2>/dev/null
        echo "[OK] gunicorn 已停止"
    else
        pkill -f "gunicorn Django.wsgi" 2>/dev/null && echo "[OK] 清理了残留 gunicorn 进程" || echo "[--] gunicorn 未在运行"
    fi
}

stop_celery() {
    pkill -f "celery -A Django worker" 2>/dev/null && echo "[OK] celery worker 已停止" || echo "[--] celery worker 未在运行"
    pkill -f "celery -A Django beat" 2>/dev/null && echo "[OK] celery beat 已停止" || echo "[--] celery beat 未在运行"
}

do_stop() {
    stop_gunicorn
    stop_celery
    echo "已停止应用层服务（MySQL/Redis 保持运行）"
}

# ---- 状态 ----

do_status() {
    mysql_running          && echo "MySQL:         运行中" || echo "MySQL:         未运行"
    redis_running          && echo "Redis:         运行中" || echo "Redis:         未运行"
    gunicorn_running       && echo "gunicorn:      运行中" || echo "gunicorn:      未运行"
    celery_worker_running  && echo "celery worker: 运行中" || echo "celery worker: 未运行"
    celery_beat_running    && echo "celery beat:   运行中" || echo "celery beat:   未运行"

    if gunicorn_running; then
        code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/auth/users/login/ \
            -X POST -H 'Content-Type: application/json' -d '{"username":"__healthcheck__","password":"x"}')
        echo "API健康检查:    HTTP $code（400/200 均为正常响应）"
    fi
}

# ---- 入口 ----

case "${1:-}" in
    start)   do_start ;;
    stop)    do_stop ;;
    restart) do_stop; sleep 2; do_start ;;
    status)  do_status ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
