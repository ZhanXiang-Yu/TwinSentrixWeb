# overheating
Overheating means a station is predicted to run above its safe thermal range. Common causes include excessive motor load, blocked cooling paths, product buildup, abnormal friction, or a failing bearing. Symptoms often include high temperature, rising power draw, higher vibration, reduced throughput, and shortened remaining useful life. First checks: verify cooling airflow, inspect for product buildup, confirm motor current, and compare vibration with the latest baseline.

# jam_risk
Jam risk means material flow may stop or become unstable. Common causes include misaligned cartons, delayed indexing, bad spacing, worn guides, or upstream surges. Symptoms include rising queue utilization, throughput loss, start-stop motion, and downstream starvation. First checks: inspect guides, clear partial blockages, validate spacing sensors, and compare upstream and downstream queue levels.

# sensor_drift
Sensor drift means a measurement is becoming less reliable or shifting away from calibrated behavior. Common causes include contamination, alignment changes, loose mounts, temperature effects, or aging sensors. Symptoms include high model uncertainty, inconsistent state changes, small throughput effects, and warnings that do not match visible station behavior. First checks: clean and align the sensor, compare redundant signals, and verify calibration history.

# mechanical_wear
Mechanical wear means the model sees patterns consistent with degrading components. Common causes include bearing wear, loose belts, worn grippers, low lubrication, or repeated overload. Symptoms include high vibration, increased power, rising downtime risk, and falling RUL. First checks: inspect wear points, check lubrication, verify torque/current, and schedule maintenance if multiple warnings are active.

# blockage
Blockage means material is physically accumulating before or inside a station. Common causes include jammed product, blocked discharge, slow downstream equipment, or a stopped transfer. Symptoms include high upstream queue, low downstream feed, and reduced throughput. First checks: compare queue before and after the station, inspect the station entrance and exit, and clear blocked material only after safe stop procedures.

# starvation
Starvation means a station cannot run at target rate because it is not receiving enough product. Common causes include upstream slowdown, feeder gaps, delayed conveyor transfer, or an upstream blockage. Symptoms include low input queue, idle cycles, and reduced downstream throughput without high local temperature or vibration. First checks: inspect upstream queue and conveyor handoff, then verify feeder and sensor timing.

# queue_congestion
Queue congestion means queue utilization is high enough to threaten throughput or create jam risk. Common causes include downstream speed loss, case packer delay, palletizer backup, or temporary mismatch between stations. Symptoms include queue utilization above threshold, falling line throughput, and warnings at neighboring stations. First checks: inspect the downstream bottleneck, compare throughput to baseline, and consider slowing upstream feed.

# high_vibration
High vibration means vibration RMS is above the internal threshold. Common causes include imbalance, worn bearing, loose mount, motor issue, or product impact. Symptoms include audible vibration, high power, rising temperature, and lower RUL. First checks: inspect mounts, bearings, shafts, and guards; if vibration is critical, stop or isolate the station according to maintenance guidance.
