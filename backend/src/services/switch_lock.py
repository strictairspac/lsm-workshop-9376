"""进程内切换锁：与 meta 行锁（SELECT ... FOR UPDATE）一起，序列化修订切换与结算提交。

单进程内（含测试）由本锁保证互斥；跨进程（backend 与 worker）由 MySQL 行锁保证。
"""
import threading
switch_lock=threading.Lock()
