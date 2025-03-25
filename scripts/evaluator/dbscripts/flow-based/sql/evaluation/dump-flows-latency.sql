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

SELECT
	post.ts - pre.ts as latency,
	pre.ts AS prets,
	post.ts as postts,
	pre.id, pre.srcport, pre.dstport as dstport
FROM  pre JOIN  post USING (id,srcport,dstport)
WHERE post.ts > pre.ts
    AND post.ts < pre.ts + 5 * 1e9
;

\copy (select * from export order by latency desc, prets, postts, dstport asc) to pstdout csv header
