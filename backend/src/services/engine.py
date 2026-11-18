"""每小时存活键峰值的确定性演算。

纯函数，不依赖数据库：乱序到达的记录按发生时间处理，同一时刻按接收顺序
(recv_seq)；小时起点承接上一小时结束时的存活键集合。
"""

def hour_floor(dt):return dt.replace(minute=0,second=0,microsecond=0)

def canonical(events):
    return sorted(events,key=lambda e:(e['event_time'],e['recv_seq']))

def apply_op(alive,op,key):
    if op=='put':alive.add(key)
    else:alive.discard(key)

def state_before(events,moment):
    """moment 之前（不含 moment）所有事件应用后的存活键集合。"""
    alive=set()
    for e in canonical(events):
        if e['event_time']>=moment:break
        apply_op(alive,e['op'],e['key'])
    return alive

def sweep(alive,events):
    """按规范顺序应用一个小时内的事件，返回该小时峰值；alive 就地推进到小时末状态。"""
    peak=len(alive)
    for e in canonical(events):
        apply_op(alive,e['op'],e['key'])
        if len(alive)>peak:peak=len(alive)
    return peak

def group_by_hour(events):
    grouped={}
    for e in events:grouped.setdefault(hour_floor(e['event_time']),[]).append(e)
    return grouped
