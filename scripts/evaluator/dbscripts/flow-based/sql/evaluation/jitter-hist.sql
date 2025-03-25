create temp view export as

WITH pkts AS (
	SELECT ts
	FROM pkt
	JOIN capture USING (capture_id)
	WHERE
		capture.name = :'name'
		AND capture."type" = :'type'
)

, pkts_trimmed AS (
	SELECT *
	FROM pkts
	WHERE ts >= 1000000::bigint * (:'trim_ms')::bigint + (SELECT MIN(ts) FROM pkts)::bigint
)


select bucket, count(1)
from (
	select ((ts - lag(ts) over (order by ts))/:bucket_size)*:bucket_size as bucket
	from pkts_trimmed
	) as jitter
where bucket is not null
group by bucket
order by bucket asc
;

\copy (select * from export order by bucket) to pstdout csv header
;
