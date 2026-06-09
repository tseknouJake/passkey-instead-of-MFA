/* AUTHOR: Enna Pirvu, Leah Goldin */

create table if not exists login_metrics (
  id serial not null,
  login_method character varying(50) not null,
  time_elapsed numeric(20, 10) not null,
  user_name character varying(100) not null,
  failed_logins integer not null default 0,
  created_at timestamp without time zone not null default CURRENT_TIMESTAMP,
  constraint login_metrics_pkey primary key (id)
) TABLESPACE pg_default;