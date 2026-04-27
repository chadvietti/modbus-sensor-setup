#!/bin/bash

# ── Config ──────────────────────────────────────────
TO="chad.vietti@kaust.edu.sa rebekah.waller@kaust.edu.sa kennedy.odokonyero@kaust.edu.sa"
FROM="your.email@gmail.com"
SUBJECT="ePAR 15-min averages — $(date '+%Y-%m-%d %H:%M')"
CSV_FILE="/home/wqes/ePAR_sensors/epar_15min.csv"
# ────────────────────────────────────────────────────

if [ ! -f "$CSV_FILE" ]; then
    echo "CSV file not found: $CSV_FILE" >&2
    exit 1
fi

LINE_COUNT=$(wc -l < "$CSV_FILE")
DATA_ROWS=$((LINE_COUNT - 1))   # subtract header

BODY="ePAR 15-minute averages — full dataset to date.
Data rows: $DATA_ROWS
Period: $(sed -n '2p' "$CSV_FILE" | cut -d',' -f2) to $(tail -1 "$CSV_FILE" | cut -d',' -f3)

See attached CSV."

{
  printf "To: %s\n" "$TO"
  printf "From: %s\n" "$FROM"
  printf "Subject: %s\n" "$SUBJECT"
  printf "MIME-Version: 1.0\n"
  printf "Content-Type: multipart/mixed; boundary=\"BOUNDARY\"\n"
  printf "\n"
  printf -- "--BOUNDARY\n"
  printf "Content-Type: text/plain\n\n"
  printf "%s\n\n" "$BODY"
  printf -- "--BOUNDARY\n"
  printf "Content-Type: text/csv; name=\"epar_15min.csv\"\n"
  printf "Content-Disposition: attachment; filename=\"epar_15min.csv\"\n\n"
  cat "$CSV_FILE"
  printf "\n--BOUNDARY--\n"
} | msmtp chad.vietti@kaust.edu.sa rebekah.waller@kaust.edu.sa kennedy.odokonyero@kaust.edu.sa
echo "Email sent to $TO"
