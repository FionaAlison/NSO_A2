#!/bin/bash

# Configuration
VIP="http://46.254.11.222:5000/data"  # Replace with your actual proxy VIP and endpoint

TOTAL_REQUESTS=10000
CONCURRENCY=100
REPEATS=3
OUTPUT_FILE="benchmark_results.csv"

echo "Nodes,Mean_Total(ms),StdDev_Total(ms),RequestsPerSec,95Percentile(ms)" > "$OUTPUT_FILE"

for NODES in 1 2 3 4 5; do
    echo "================================================================="
    echo "[MANUAL STEP] Please scale your service to $NODES node(s) now."
    read -p "Press ENTER to continue once scaling is complete..."

    MEAN_TOTALS=()
    STD_TOTALS=()
    REQ_PER_SECS=()
    P95S=()

    for ((i=1; i<=REPEATS; i++)); do
        echo "[INFO] Run $i of $REPEATS..."
        RESULT=$(ab -n $TOTAL_REQUESTS -c $CONCURRENCY "$VIP" 2>&1)

        # Parse Total mean and stddev from Connection Times
        TOTAL_LINE=$(echo "$RESULT" | awk '/Total:/ {print}')
        MEAN_TOTAL=$(echo "$TOTAL_LINE" | awk '{print $2}')
        STD_TOTAL=$(echo "$TOTAL_LINE" | awk '{print $3}')

        # Requests/sec
        REQ_PER_SEC=$(echo "$RESULT" | grep "Requests per second:" | awk '{print $4}')

        # 95th percentile
        P95=$(echo "$RESULT" | awk '/95%/ {print $2}')

        MEAN_TOTALS+=(${MEAN_TOTAL:-0})
        STD_TOTALS+=(${STD_TOTAL:-0})
        REQ_PER_SECS+=(${REQ_PER_SEC:-0})
        P95S+=(${P95:-0})
    done

    # Averages
    avg() {
        printf '%s\n' "$@" | awk '{sum+=$1} END {print (NR > 0) ? sum/NR : 0}'
    }

    MEAN_TOTAL_AVG=$(avg "${MEAN_TOTALS[@]}")
    STD_TOTAL_AVG=$(avg "${STD_TOTALS[@]}")
    REQ_PER_SEC_AVG=$(avg "${REQ_PER_SECS[@]}")
    P95_AVG=$(avg "${P95S[@]}")

    echo "[INFO] Results for $NODES nodes saved."

    echo "$NODES,$MEAN_TOTAL_AVG,$STD_TOTAL_AVG,$REQ_PER_SEC_AVG,$P95_AVG" >> "$OUTPUT_FILE"
done

echo "[DONE] All results saved to $OUTPUT_FILE"
