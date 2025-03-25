insert into capture (name, "type")
	values (:'name', :'type')
	returning capture_id as capture_id
\gset import_ 

create temporary table import (ts int8, src text, srcport text, dst text, dstport text, id text);

\copy import from pstdin

insert into pkt (capture_id, ts, src, srcport, dst, dstport, id) select :import_capture_id, ts, src, srcport, dst, dstport, id from import;
