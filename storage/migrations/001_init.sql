-- FPL agent simulation: manager timeline only.
-- Historical 2025/26 world data stays in final_fpl CSVs.

create extension if not exists "pgcrypto";

create table if not exists public.simulations (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    season text not null,
    mode text not null check (mode in ('historical', 'live')),
    config_name text not null,
    mlflow_run_id text,
    status text not null check (status in ('in_progress', 'completed', 'failed')),
    current_gw int not null check (current_gw between 1 and 38),
    total_points int not null default 0,
    created_at timestamptz not null default now(),
    completed_at timestamptz
);

create table if not exists public.simulation_chips (
    id uuid primary key default gen_random_uuid(),
    simulation_id uuid not null references public.simulations(id) on delete cascade,
    chip_type text not null check (chip_type in ('wildcard', 'freehit', 'bboost', '3xc')),
    entitlement int not null,
    available_from_gw int not null check (available_from_gw between 1 and 38),
    expires_after_gw int not null check (expires_after_gw between 1 and 38),
    used_gw int check (used_gw between 1 and 38),
    created_at timestamptz not null default now(),
    unique (simulation_id, chip_type, entitlement)
);

create table if not exists public.manager_gameweeks (
    id uuid primary key default gen_random_uuid(),
    simulation_id uuid not null references public.simulations(id) on delete cascade,
    gw int not null check (gw between 1 and 38),
    status text not null check (status in ('in_progress', 'locked', 'completed')),
    bank numeric(8, 1) not null check (bank >= 0),
    free_transfers int check (free_transfers between 0 and 5),
    team_value numeric(8, 1),
    points_before int not null default 0,
    gross_points int,
    transfer_hit int not null default 0 check (transfer_hit <= 0),
    net_points int,
    total_points_after int,
    active_chip_entitlement_id uuid references public.simulation_chips(id),
    mlflow_trace_id text,
    decision_locked_at timestamptz,
    resolved_at timestamptz,
    created_at timestamptz not null default now(),
    unique (simulation_id, gw)
);

create table if not exists public.squad_players (
    id uuid primary key default gen_random_uuid(),
    manager_gameweek_id uuid not null references public.manager_gameweeks(id) on delete cascade,
    player_id int not null,
    purchase_price numeric(6, 1) not null,
    selling_price numeric(6, 1) not null,
    is_starter boolean not null,
    bench_order int check (bench_order between 1 and 3),
    is_captain boolean not null default false,
    is_vice_captain boolean not null default false,
    created_at timestamptz not null default now(),
    unique (manager_gameweek_id, player_id)
);

create table if not exists public.transfers (
    id uuid primary key default gen_random_uuid(),
    manager_gameweek_id uuid not null references public.manager_gameweeks(id) on delete cascade,
    player_out_id int not null,
    player_in_id int not null,
    sell_price numeric(6, 1) not null,
    buy_price numeric(6, 1) not null,
    created_at timestamptz not null default now()
);

create table if not exists public.player_points (
    id uuid primary key default gen_random_uuid(),
    manager_gameweek_id uuid not null references public.manager_gameweeks(id) on delete cascade,
    player_id int not null,
    raw_points int not null,
    multiplier int not null,
    counted_points int not null,
    started boolean not null,
    bench_order int,
    auto_subbed_in boolean not null default false,
    auto_subbed_out boolean not null default false,
    created_at timestamptz not null default now(),
    unique (manager_gameweek_id, player_id)
);

alter table public.simulations enable row level security;
alter table public.simulation_chips enable row level security;
alter table public.manager_gameweeks enable row level security;
alter table public.squad_players enable row level security;
alter table public.transfers enable row level security;
alter table public.player_points enable row level security;
