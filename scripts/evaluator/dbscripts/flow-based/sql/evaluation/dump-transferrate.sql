create temp view export as

WITH

pre AS (
    SELECT ts, dstport, id, srcport
    FROM pkt
    JOIN capture USING (capture_id)
    WHERE
        capture.name = :'name'
        AND capture."type" = 'pre'
)

, post AS (
	SELECT ts, dstport, id, srcport
	FROM pkt
	JOIN capture USING (capture_id)
	WHERE
		capture.name = :'name'
		AND capture."type" = 'post'
),

-- calc minima
premin AS (
	SELECT MIN(ts)
	FROM pre
),
postmin AS (
	SELECT MIN(ts)
	FROM post
),

-- NOTE: trimming happens independent for pre and post, i.e. there might be packets trimmed from pre that were received in post
pretrimmed AS (
	SELECT ts,  dstport, id, srcport
	FROM pre
	WHERE pre.ts >= (1000000::bigint * (:'trim_ms')::bigint + (SELECT * from premin))::bigint
),
posttrimmed AS (
	SELECT ts,  dstport, id, srcport
	FROM post
	WHERE post.ts >= (1000000::bigint * (:'trim_ms')::bigint + (SELECT * from postmin))::bigint
),

-- calc trimmed minima
pretrimmin AS (
	SELECT MIN(ts)
	FROM pretrimmed
),
posttrimmin AS (
	SELECT MIN(ts)
	FROM posttrimmed
),

premins AS (
	SELECT ts-(SELECT * from pretrimmin) AS tmstamp, dstport, id, srcport,
	( (ts-(SELECT * from pretrimmin)) / 1000000000 ) * 1000000000 AS second_bucket
	FROM pretrimmed
),
postmins AS (
	SELECT ts-(SELECT * from posttrimmin) AS tmstamp, dstport, id, srcport,
	( (ts-(SELECT * from posttrimmin)) / 1000000000 ) * 1000000000 AS second_bucket
	FROM posttrimmed
),

-- count packets (trimmed)
postcounttrimmed AS (
	SELECT COUNT(*) AS countposttrimmed
	FROM posttrimmed
),
precounttrimmed AS (
	SELECT COUNT(*) AS countpretrimmed
	FROM pretrimmed
),

-- average over pre and post rate per second
pre_pps AS (
SELECT AVG(prepktsps.pkts_per_second) AS pre_pkts_per_second
FROM (
	SELECT count(*) AS pkts_per_second
	FROM (SELECT second_bucket
		FROM premins) as output
	GROUP BY output.second_bucket
	ORDER BY output.second_bucket ASC
) AS prepktsps
),

post_pps AS (
SELECT AVG(postpktsps.pkts_per_second) AS post_pkts_per_second
FROM (
	SELECT count(*) AS pkts_per_second
	FROM (SELECT second_bucket
		FROM postmins) as output
	GROUP BY output.second_bucket
	ORDER BY output.second_bucket ASC
) AS postpktsps
)

-- output selection
SELECT
	precounttrimmed.countpretrimmed AS pre_received,
	postcounttrimmed.countposttrimmed AS post_received,
	CAST(postcounttrimmed.countposttrimmed AS decimal)/precounttrimmed.countpretrimmed AS transferrate,
	pre_pps.pre_pkts_per_second,
	post_pps.post_pkts_per_second
FROM precounttrimmed, postcounttrimmed, pre_pps, post_pps
;

\copy (select * from export) to pstdout csv header
