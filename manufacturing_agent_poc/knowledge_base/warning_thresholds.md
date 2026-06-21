# failure risk thresholds
Failure risk is a predicted probability between 0 and 1. Warning is triggered when failure risk is at least 0.75. Critical is triggered when failure risk is at least 0.85.

# throughput thresholds
Throughput drop is evaluated against baseline throughput. Warning is triggered when predicted throughput is below 85 percent of baseline. Critical is triggered when predicted throughput is below 75 percent of baseline.

# queue utilization thresholds
Queue utilization is queue length divided by queue capacity. Warning is triggered at 80 percent utilization. Critical is triggered at 90 percent utilization.

# RUL thresholds
Remaining useful life is measured in minutes. Warning is triggered below 45 minutes. Critical is triggered below 30 minutes.

# sensor anomaly thresholds
Temperature warning is triggered above 80 C and critical above 90 C. Vibration warning is triggered above 0.65 RMS and critical above 0.80 RMS.

# uncertainty thresholds
Model uncertainty caution is triggered above 0.30. Warning is triggered above 0.45. High uncertainty means the operator should verify measurements before treating the prediction as a confirmed fault.
