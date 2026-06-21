# what to check first
First verify timestamp, selected machine, current state, active flags, and top contributing signals. Then check the physical station for the highest severity flag. Do not treat mock prediction values as live plant telemetry.

# what data to verify
Verify risk, confidence, predicted throughput, baseline throughput, queue length, temperature, vibration, power, RUL, and model uncertainty. Confirm whether the warning persists across multiple snapshots.

# distinguishing blockage from starvation
Blockage usually has high upstream queue and reduced downstream flow. Starvation usually has low input queue and idle downstream cycles because upstream material is missing. Compare the selected station queue with neighboring stations before assigning the cause.

# interpreting high uncertainty
High uncertainty means the model is less confident in the prediction. It can be caused by sensor drift, missing or unstable signals, abnormal operating modes, or data outside the training range. Verify sensors and avoid overconfident claims.

# interpreting multiple warnings
Multiple warnings on one machine should be treated as higher priority because combined risk can indicate a real bottleneck or mechanical issue. Look for a shared cause such as overheating plus vibration, or queue congestion plus throughput drop.
