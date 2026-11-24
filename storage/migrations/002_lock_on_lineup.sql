-- Flatten transfers, drop decisions, store MLflow trace id per gameweek.
-- Wipe leftover simulation rows first (cascade). Safe to re-run after 001_init.

delete from public.simulations;

alter table public.manager_gameweeks
    add column if not exists mlflow_trace_id text;

drop table if exists public.decisions;
drop table if exists public.transfers;
drop table if exists public.transfer_batches;

create table public.transfers (
    id uuid primary key default gen_random_uuid(),
    manager_gameweek_id uuid not null references public.manager_gameweeks(id) on delete cascade,
    player_out_id int not null,
    player_in_id int not null,
    sell_price numeric(6, 1) not null,
    buy_price numeric(6, 1) not null,
    created_at timestamptz not null default now()
);

alter table public.transfers enable row level security;
