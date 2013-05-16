DROP FUNCTION IF EXISTS timeseries_tp_avg(in start timestamp, in stop timestamp, in step interval, in endpoint varchar, in complex_id integer);
DROP FUNCTION IF EXISTS timeseries_tp_max(in start timestamp, in stop timestamp, in step interval, in endpoint varchar, in complex_id integer);

DROP FUNCTION IF EXISTS timeseries_tp_avg(in start timestamp, in stop timestamp, in step interval, in endpoint varchar);
DROP FUNCTION IF EXISTS timeseries_tp_max(in start timestamp, in stop timestamp, in step interval, in endpoint varchar);


CREATE FUNCTION timeseries_tp_avg(in start timestamp, 
                                  in stop timestamp, 
                                  in step interval, 
                                  in endpoint varchar, 
                                  in complex_id integer)
RETURNS TABLE(bucket timestamp, bytesreceived bigint, bytessent bigint)
AS $$
  SELECT s.bucket, COALESCE(avg(bytesreceived), 0)::bigint AS bytesreceived, COALESCE(avg(bytessent), 0)::bigint AS bytessent
  FROM (
    SELECT requests.timestamp, requests.bytesreceived, requests.bytessent
    FROM requests JOIN tasks ON (requests.task_id=tasks.id) 
    WHERE endpoint LIKE $4 AND tasks.complex_id = $5
      AND timestamp >= $1::timestamp AND timestamp <= $2::timestamp
  ) as logs 
  RIGHT OUTER JOIN (
    SELECT generate_series as bucket 
    FROM generate_series($1::timestamp, $2::timestamp, $3::INTERVAL)
  ) AS s
  ON (logs.timestamp >= s.bucket AND logs.timestamp < s.bucket + $3::INTERVAL)
  GROUP BY s.bucket
  ORDER BY s.bucket
$$
LANGUAGE SQL;


CREATE FUNCTION timeseries_tp_max(in start timestamp, 
                                  in stop timestamp, 
                                  in step interval, 
                                  in endpoint varchar, 
                                  in complex_id integer)
RETURNS TABLE(bucket timestamp, bytesreceived bigint, bytessent bigint)
AS $$
  SELECT s.bucket, COALESCE(max(bytesreceived), 0)::bigint AS bytesreceived, COALESCE(max(bytessent), 0)::bigint AS bytessent
  FROM (
    SELECT requests.timestamp, requests.bytesreceived, requests.bytessent
    FROM requests JOIN tasks ON (requests.task_id=tasks.id) 
    WHERE endpoint LIKE $4 AND tasks.complex_id = $5
      AND timestamp >= $1::timestamp AND timestamp <= $2::timestamp
  ) as logs
  RIGHT OUTER JOIN (
    SELECT generate_series as bucket 
    FROM generate_series($1::timestamp, $2::timestamp, $3::INTERVAL)
  ) AS s
  ON (logs.timestamp >= s.bucket AND logs.timestamp < s.bucket + $3::INTERVAL)
  GROUP BY s.bucket
  ORDER BY s.bucket
$$
LANGUAGE SQL;


CREATE FUNCTION timeseries_tp_avg(in start timestamp, in stop timestamp, in step interval, in endpoint varchar)
RETURNS TABLE(bucket timestamp, bytesreceived bigint, bytessent bigint)
AS $$
  SELECT s.bucket, COALESCE(avg(bytesreceived), 0)::bigint AS bytesreceived, COALESCE(avg(bytessent), 0)::bigint AS bytessent
  FROM (
    SELECT * FROM requests 
    WHERE endpoint = $4 AND timestamp >= $1::timestamp AND timestamp <= $2::timestamp
  ) as logs 
  RIGHT OUTER JOIN (
    SELECT generate_series as bucket 
    FROM generate_series($1::timestamp, $2::timestamp, $3::INTERVAL)
  ) AS s
  ON (logs.timestamp >= s.bucket AND logs.timestamp < s.bucket + $3::INTERVAL)
  GROUP BY s.bucket
  ORDER BY s.bucket
$$
LANGUAGE SQL;


CREATE FUNCTION timeseries_tp_max(in start timestamp, in stop timestamp, in step interval, in endpoint varchar)
RETURNS TABLE(bucket timestamp, bytesreceived bigint, bytessent bigint)
AS $$
  SELECT s.bucket, COALESCE(max(bytesreceived), 0)::bigint AS bytesreceived, COALESCE(max(bytessent), 0)::bigint AS bytessent
  FROM (
    SELECT * FROM requests 
    WHERE endpoint = $4 AND timestamp >= $1::timestamp AND timestamp <= $2::timestamp
  ) as logs
  RIGHT OUTER JOIN (
    SELECT generate_series as bucket 
    FROM generate_series($1::timestamp, $2::timestamp, $3::INTERVAL)
  ) AS s
  ON (logs.timestamp >= s.bucket AND logs.timestamp < s.bucket + $3::INTERVAL)
  GROUP BY s.bucket
  ORDER BY s.bucket
$$
LANGUAGE SQL;


-- Call: select * from timeseries_tp_max('2013-03-28 14:00'::timestamp, '2013-03-28 14:30'::timestamp, '5 S', 'test')