from collections import deque
from copy import deepcopy


class Process:
    def __init__(self, pid, arrival, burst, priority=0):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.priority = priority
        self.reset()

    def reset(self):
        self.rem = self.burst
        self.finish_time = None
        self.wt = 0
        self.tat = 0


# ================= UTILITIES ================= #

def compute_metrics(p):
    p.tat = p.finish_time - p.arrival
    p.wt = p.tat - p.burst


def print_gantt(gantt):
    print("\nGantt Chart:")
    for pid, s, e in gantt:
        print(f"| {pid} ({s}-{e}) ", end="")
    print("|\n")


def print_metrics(processes):
    processes = sorted(processes, key=lambda x: x.pid)
    total_wt = sum(p.wt for p in processes)
    total_tat = sum(p.tat for p in processes)

    print("PID\tWT\tTAT")
    for p in processes:
        print(f"{p.pid}\t{p.wt}\t{p.tat}")

    print(f"\nAverage WT: {total_wt/len(processes):.2f}")
    print(f"Average TAT: {total_tat/len(processes):.2f}\n")


def clone_processes(processes):
    return deepcopy(processes)


def add_gantt(gantt, pid, start, end):
    if start == end:
        return
    if gantt and gantt[-1][0] == pid:
        gantt[-1] = (pid, gantt[-1][1], end)
    else:
        gantt.append((pid, start, end))


# ================= FCFS ================= #

def fcfs(processes):
    procs = sorted(clone_processes(processes), key=lambda x: (x.arrival, x.pid))
    time = 0
    gantt = []

    for p in procs:
        if time < p.arrival:
            add_gantt(gantt, "IDLE", time, p.arrival)
            time = p.arrival

        start = time
        time += p.burst
        p.finish_time = time
        compute_metrics(p)
        add_gantt(gantt, p.pid, start, time)

    print_gantt(gantt)
    print_metrics(procs)


# ================= SJF ================= #

def sjf(processes):
    procs = clone_processes(processes)
    time = 0
    done = 0
    gantt = []

    while done < len(procs):
        ready = [p for p in procs if p.arrival <= time and p.finish_time is None]

        if not ready:
            next_arrival = min(p.arrival for p in procs if p.finish_time is None)
            add_gantt(gantt, "IDLE", time, next_arrival)
            time = next_arrival
            continue

        p = min(ready, key=lambda x: (x.burst, x.arrival, x.pid))
        start = time
        time += p.burst
        p.finish_time = time
        compute_metrics(p)
        add_gantt(gantt, p.pid, start, time)
        done += 1

    print_gantt(gantt)
    print_metrics(procs)


# ================= SRT ================= #

def srt(processes):
    procs = clone_processes(processes)
    time = 0
    done = 0
    gantt = []

    current = None
    start = 0

    while done < len(procs):
        ready = [p for p in procs if p.arrival <= time and p.rem > 0]

        if not ready:
            if current is not None:
                add_gantt(gantt, current.pid if current != "IDLE" else "IDLE", start, time)
            current = "IDLE"
            start = time
            time += 1
            continue

        p = min(ready, key=lambda x: (x.rem, x.arrival, x.pid))

        if current != p:
            if current is not None:
                add_gantt(gantt, current.pid if current != "IDLE" else "IDLE", start, time)
            current = p
            start = time

        p.rem -= 1
        time += 1

        if p.rem == 0:
            p.finish_time = time
            compute_metrics(p)
            done += 1

    if current is not None:
        add_gantt(gantt, current.pid if current != "IDLE" else "IDLE", start, time)

    print_gantt(gantt)
    print_metrics(procs)


# ================= ROUND ROBIN ================= #

def round_robin(processes, tq):
    procs = sorted(clone_processes(processes), key=lambda x: (x.arrival, x.pid))
    time = 0
    i = 0
    done = 0

    queue = deque()
    gantt = []

    while done < len(procs):
        while i < len(procs) and procs[i].arrival <= time:
            queue.append(procs[i])
            i += 1

        if not queue:
            add_gantt(gantt, "IDLE", time, procs[i].arrival)
            time = procs[i].arrival
            continue

        p = queue.popleft()
        start = time

        run = min(tq, p.rem)
        time += run
        p.rem -= run
        add_gantt(gantt, p.pid, start, time)

        while i < len(procs) and procs[i].arrival <= time:
            queue.append(procs[i])
            i += 1

        if p.rem > 0:
            queue.append(p)
        else:
            p.finish_time = time
            compute_metrics(p)
            done += 1

    print_gantt(gantt)
    print_metrics(procs)


# ================= PRIORITY NON-PREEMPTIVE ================= #

def priority_np(processes, mode):
    procs = clone_processes(processes)
    time = 0
    done = 0
    gantt = []

    while done < len(procs):
        ready = [p for p in procs if p.arrival <= time and p.finish_time is None]

        if not ready:
            next_arrival = min(p.arrival for p in procs if p.finish_time is None)
            add_gantt(gantt, "IDLE", time, next_arrival)
            time = next_arrival
            continue

        if mode == '2':  # higher number = higher priority
            p = max(ready, key=lambda x: (x.priority, -x.arrival, -int(x.pid[1:])))
        else:  # lower number = higher priority
            p = min(ready, key=lambda x: (x.priority, x.arrival, x.pid))

        start = time
        time += p.burst
        p.finish_time = time
        compute_metrics(p)
        add_gantt(gantt, p.pid, start, time)
        done += 1

    print_gantt(gantt)
    print_metrics(procs)


# ================= PRIORITY + RR ================= #

def priority_rr(processes, tq, mode):
    procs = sorted(clone_processes(processes), key=lambda x: (x.arrival, x.pid))
    time = 0
    i = 0
    done = 0

    queues = {}
    gantt = []

    def get_highest_priority(active):
        if mode == '2':
            return max(active)
        return min(active)

    while done < len(procs):
        while i < len(procs) and procs[i].arrival <= time:
            p = procs[i]
            queues.setdefault(p.priority, deque()).append(p)
            i += 1

        active = [k for k in queues if queues[k]]

        if not active:
            add_gantt(gantt, "IDLE", time, procs[i].arrival)
            time = procs[i].arrival
            continue

        highest = get_highest_priority(active)
        queue = queues[highest]
        p = queue.popleft()

        start = time
        run = min(tq, p.rem)
        time += run
        p.rem -= run
        add_gantt(gantt, p.pid, start, time)

        while i < len(procs) and procs[i].arrival <= time:
            new_p = procs[i]
            queues.setdefault(new_p.priority, deque()).append(new_p)
            i += 1

        if p.rem > 0:
            queue.append(p)
        else:
            p.finish_time = time
            compute_metrics(p)
            done += 1

    print_gantt(gantt)
    print_metrics(procs)


# ================= MAIN ================= #

def main():
    while True:
        print("\n--- CPU Scheduling Simulator ---")
        print("1. FCFS")
        print("2. SJF (Non-Preemptive)")
        print("3. SRT (Preemptive)")
        print("4. Round Robin")
        print("5. Priority (Non-Preemptive)")
        print("6. Priority with RR")
        print("7. Exit")

        

        ch = input("Choice: ")
        if ch == '7':
            break
        
        if ch not in ['1','2','3','4','5','6','7']:
                print("Invalid menu choice.")
                continue

        n = int(input("Number of processes: "))
        processes = []

        priority_mode = None
        if ch in ['5', '6']:
            print("\nPriority Rule:")
            print("1. Lower number = higher priority")
            print("2. Higher number = higher priority")
            priority_mode = input("Choose mode (1 or 2): ")

        for i in range(n):
            pid = f"P{i+1}"
            arr = int(input(f"Arrival for {pid}: "))
            burst = int(input(f"Burst for {pid}: "))
            pri = 0

            if ch in ['5', '6']:
                pri = int(input(f"Priority for {pid}: "))

            processes.append(Process(pid, arr, burst, pri))

        if ch == '1':
            fcfs(processes)
        elif ch == '2':
            sjf(processes)
        elif ch == '3':
            srt(processes)
        elif ch == '4':
            tq = int(input("Time Quantum: "))
            round_robin(processes, tq)
        elif ch == '5':
            priority_np(processes, priority_mode)
        elif ch == '6':
            tq = int(input("Time Quantum: "))
            priority_rr(processes, tq, priority_mode)


if __name__ == "__main__":
    main()