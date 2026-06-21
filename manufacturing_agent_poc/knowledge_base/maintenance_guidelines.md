# inspection priority rules
Prioritize critical flags first, then warning flags, then caution flags. If one machine has three or more active flags, inspect that machine before lower severity stations. Always verify the selected timestamp, machine id, and top contributing signals before recommending action.

# safe response to overheating
For overheating, check cooling airflow, product buildup, motor current, and nearby guarding. If temperature exceeds the critical threshold or overheating appears with high vibration, reduce load or stop the station according to local safety practice and escalate to maintenance.

# response to abnormal vibration
For abnormal vibration, inspect bearings, mounts, shafts, belts, and grippers. If vibration is critical or paired with low RUL, avoid running the station at full speed until maintenance reviews the mechanical condition.

# response to queue buildup
For queue buildup, identify whether the queue is caused by the selected station or a downstream bottleneck. Check downstream station state, case accumulation, conveyor transfer, and reject handling. If queue utilization remains high, slow upstream feed to prevent jams.

# when to slow the line
Slow the line when queue utilization is near warning threshold, throughput is falling, but no critical safety or mechanical flag is active. Slowing the line is also appropriate while an operator clears minor accumulation.

# when to stop the line
Stop the line when a critical temperature, critical vibration, very low RUL, or unsafe jam condition is present. Stopping is also appropriate when a machine has multiple active warnings that cannot be verified quickly.

# when to escalate to maintenance
Escalate to maintenance when critical flags appear, when RUL is below the critical threshold, when high vibration repeats, or when the same warning persists across multiple snapshots after basic checks.
