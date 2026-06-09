/* AUTHOR: Jake Lockitch, Leah Goldin */

create table if not exists users (
  id uuid not null default gen_random_uuid (),
  username text not null,
  password text not null,
  mfa_secret text null,
  passkey_credentials jsonb null default '[]'::jsonb,
  created_at timestamp without time zone null default now(),
  email text null,
  constraint users_pkey primary key (id),
  constraint users_username_key unique (username)
) TABLESPACE pg_default;