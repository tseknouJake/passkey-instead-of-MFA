create table if not exists public.study_profiles (
    username text primary key,
    age integer not null check (age between 13 and 120),
    gender text not null,
    technical_expertise smallint not null check (technical_expertise between 1 and 5),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.study_responses (
    username text not null,
    auth_method text not null check (auth_method in ('classic', 'mfa', 'passkey', 'social')),
    used_before boolean not null,
    easy_to_log_in smallint not null check (easy_to_log_in between 1 and 5),
    easy_to_understand smallint not null check (easy_to_understand between 1 and 5),
    quick_to_complete smallint not null check (quick_to_complete between 1 and 5),
    complete_without_help smallint not null check (complete_without_help between 1 and 5),
    felt_secure smallint not null check (felt_secure between 1 and 5),
    trust_to_protect_account smallint not null check (trust_to_protect_account between 1 and 5),
    comfortable_regularly smallint not null check (comfortable_regularly between 1 and 5),
    additional_feedback text not null default '',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (username, auth_method)
);

create index if not exists study_responses_auth_method_idx
    on public.study_responses (auth_method);

create index if not exists study_responses_updated_at_idx
    on public.study_responses (updated_at desc);
