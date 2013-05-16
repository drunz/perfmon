DROP FUNCTION IF EXISTS timeseries_rq_avg(in start timestamp, in stop timestamp, in step interval, in endpoint varchar, in complex_id integer);
DROP FUNCTION IF EXISTS timeseries_rq_max(in start timestamp, in stop timestamp, in step interval, in endpoint varchar, in complex_id integer);

DROP FUNCTION IF EXISTS timeseries_rq_avg(in start timestamp, in stop timestamp, in step interval, in endpoint varchar);
DROP FUNCTION IF EXISTS timeseries_rq_max(in start timestamp, in stop timestamp, in step interval, in endpoint varchar);


CREATE FUNCTION timeseries_rq_avg(in start timestamp, 
                                  in stop timestamp, 
                                  in step interval, 
                                  in endpoint varchar,
                                  in complex_id integer)
RETURNS TABLE(bucket timestamp, timerequest double precision)
AS $$
  SELECT s.bucket, COALESCE(avg(timerequest), 0) AS timerequest
  FROM (
    SELECT requests.timestamp, requests.timerequest 
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


CREATE FUNCTION timeseries_rq_max(in start timestamp, 
                                  in stop timestamp, 
                                  in step interval, 
                                  in endpoint varchar,
                                  in complex_id integer)
RETURNS TABLE(bucket timestamp, timerequest double precision)
AS $$
  SELECT s.bucket, COALESCE(max(timerequest), 0) AS timerequest
  FROM (
    SELECT requests.timestamp, requests.timerequest 
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


CREATE FUNCTION timeseries_rq_avg(in start timestamp, 
                                  in stop timestamp, 
                                  in step interval, 
                                  in endpoint varchar)
RETURNS TABLE(bucket timestamp, timerequest double precision)
AS $$
  SELECT s.bucket, COALESCE(avg(timerequest), 0) AS timerequest
  FROM (
    SELECT requests.timestamp, requests.timerequest 
    FROM requests 
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


CREATE FUNCTION timeseries_rq_max(in start timestamp, 
                                  in stop timestamp, 
                                  in step interval, 
                                  in endpoint varchar)
RETURNS TABLE(bucket timestamp, timerequest double precision)
AS $$
  SELECT s.bucket, COALESCE(max(timerequest), 0) AS timerequest
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


-- Call: select * from timeseries_rq_avg('2013-03-28 14:00'::timestamp, '2013-03-28 14:30'::timestamp, '5 S', 'test')