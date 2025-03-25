create temp view export as

WITH

pre AS (

	select ts, dstport, id, srcport from (
		SELECT ts, dstport, id, srcport, count(1) over (partition by CONCAT(id, srcport, dstport)) as c
		FROM pkt
		JOIN capture USING (capture_id)
		WHERE
			capture.name = :'name'
			AND capture."type" = 'pre'
	) as yolo where c = 1
)

, post AS (
	SELECT ts, dstport, id, srcport
	FROM pkt
	JOIN capture USING (capture_id)
	WHERE
		capture.name = :'name'
		AND capture."type" = 'post'
)

SELECT *, count(*) FROM (
    SELECT mpcaps.latency_bucket
    FROM (
	SELECT
		pre.ts AS prets,
		post.ts as postts,
            ((post.ts - pre.ts) / :'bucket_size' ) * :'bucket_size' AS latency_bucket
        FROM  pre JOIN  post USING (id,srcport,dstport)
        WHERE post.ts > pre.ts 
            AND post.ts < pre.ts + 5 * 1e9
            AND post.ts >= (1000000::bigint * (:'trim_ms')::bigint + (SELECT MIN(ts) from post))::bigint
        ORDER BY pre.ts ASC
    ) AS mpcaps
) AS histogram
GROUP BY histogram.latency_bucket
ORDER BY histogram.latency_bucket ASC
;

\copy (select * from export order by latency_bucket) to pstdout csv header
