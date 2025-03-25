CREATE temp VIEW export AS

WITH pkts AS (
	SELECT ts, dstport, id, srcport
	FROM pkt
	JOIN capture USING (capture_id)
	WHERE
		capture.name = :'name'
		AND capture."type" = :'type'
)

, oldmin AS (
	SELECT MIN(ts)::bigint
	FROM pkts
)

, pkts_trimmed AS (
	SELECT *
	FROM pkts
	WHERE ts >= ((1000000::bigint * (:'trim_ms')::bigint) + (SELECT * FROM oldmin))
)

, minimum AS (
	SELECT MIN(ts)
	FROM pkts_trimmed
)


SELECT bucket + (SELECT * FROM minimum) AS ts, count(1)
FROM (
	SELECT *, ((ts - (SELECT * FROM minimum))/1000000000) * 1000000000 as bucket
	FROM pkts_trimmed
) AS blarb
GROUP BY bucket
ORDER BY bucket ASC;

\copy (SELECT * FROM export) to pstdout csv header
;
