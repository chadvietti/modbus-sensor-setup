import csv
import time
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────
SLAVE_IDS   = [7, 8, 9, 10, 11, 12]
RAW_CSV     = "epar_raw.csv"
AVG_CSV     = "epar_15min.csv"
WINDOW_MIN  = 15
INTERVAL    = WINDOW_MIN * 60   # seconds between averages
# ────────────────────────────────────────────────────

def read_raw_since(filename, since_dt):
    """Return all rows from RAW_CSV with timestamp >= since_dt."""
    rows = []
    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                    if ts >= since_dt:
                        rows.append(row)
                except (ValueError, KeyError):
                    continue
    except FileNotFoundError:
        pass
    return rows

def write_header_if_needed(filename):
    try:
        with open(filename, 'r'):
            pass
    except FileNotFoundError:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ['timestamp', 'window_start', 'window_end', 'n_readings'] \
                     + [f'sensor_{i}' for i in SLAVE_IDS]
            writer.writerow(header)

write_header_if_needed(AVG_CSV)

print(f"Starting 15-min averager — reading from {RAW_CSV}")
print(f"Writing averages to: {AVG_CSV}")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        # Sleep until next 15-minute boundary
        now = datetime.now()
        next_boundary = (now + timedelta(minutes=WINDOW_MIN)).replace(
            minute=(now.minute // WINDOW_MIN + 1) * WINDOW_MIN % 60,
            second=0, microsecond=0
        )
        if next_boundary <= now:
            next_boundary += timedelta(hours=1)
        sleep_secs = (next_boundary - datetime.now()).total_seconds()
        print(f"  Next average at {next_boundary.strftime('%H:%M:%S')} "
              f"(sleeping {sleep_secs:.0f}s)")
        time.sleep(max(0, sleep_secs))

        window_end   = datetime.now()
        window_start = window_end - timedelta(minutes=WINDOW_MIN)
        rows = read_raw_since(RAW_CSV, window_start)

        averages = []
        for sid in SLAVE_IDS:
            col = f'sensor_{sid}'
            vals = []
            for row in rows:
                try:
                    v = float(row[col])
                    vals.append(v)
                except (ValueError, KeyError, TypeError):
                    pass
            avg = round(sum(vals) / len(vals), 2) if vals else None
            averages.append(avg)

        timestamp    = window_end.strftime('%Y-%m-%d %H:%M:%S')
        win_start_str = window_start.strftime('%Y-%m-%d %H:%M:%S')
        win_end_str   = window_end.strftime('%Y-%m-%d %H:%M:%S')
        n = len(rows)

        with open(AVG_CSV, 'a', newline='') as f:
            csv.writer(f).writerow(
                [timestamp, win_start_str, win_end_str, n] + averages
            )

        display = [f"S{sid}={avg if avg is not None else 'ERR'}"
                   for sid, avg in zip(SLAVE_IDS, averages)]
        print(f"  [{timestamp}] n={n}  " + "  ".join(display))

except KeyboardInterrupt:
    print("\nStopped.")
