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

, match AS (
    SELECT
        post.ts - pre.ts as latency,
        pre.ts AS prets,
        post.ts as postts,
        pre.id, pre.srcport, pre.dstport
    FROM  pre JOIN  post USING (id,srcport,dstport)
    WHERE post.ts > pre.ts
        AND post.ts < pre.ts + 5 * 1e9
        AND post.ts >= (1000000::bigint * (:'trim_ms')::bigint + (SELECT MIN(ts) from post))::bigint
)

SELECT *
FROM match
ORDER BY latency DESC, prets, postts ASC LIMIT :'num_worst';

\copy (select * from export) to pstdout csv header
