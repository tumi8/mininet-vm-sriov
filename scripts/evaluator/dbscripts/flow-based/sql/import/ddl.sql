create unlogged table if not exists capture (capture_id serial primary key, name text, "type" text);
create unlogged table if not exists pkt (capture_id int references capture(capture_id), ts int8, src text, srcport text, dst text, dstport text, id text);
create unique index if not exists capture_name_type_idx on capture (name, "type");
create index if not exists pkt_capture_id_idx ON pkt using brin (capture_id);

ALTER TABLE capture SET (
  autovacuum_enabled = false, toast.autovacuum_enabled = false
);

ALTER TABLE pkt SET (
  autovacuum_enabled = false, toast.autovacuum_enabled = false
);
