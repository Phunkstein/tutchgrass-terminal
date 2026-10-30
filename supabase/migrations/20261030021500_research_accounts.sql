-- Tutchgrass Labs research accounts: My conditions, saved items, email alert/digest preferences.
-- All rows are owned by auth.users and visible/editable only by their owner (RLS).

create table if not exists public.user_conditions (
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  condition_id text not null check (condition_id in ('sleep','pain','anxiety','mood','ptsd','arthritis','inflammation','nausea','appetite','fibromyalgia','ms','epilepsy','migraine','ibd','focus')),
  created_at timestamptz not null default now(),
  primary key (user_id, condition_id)
);
alter table public.user_conditions enable row level security;
create policy "own conditions select" on public.user_conditions for select to authenticated using (user_id = (select auth.uid()));
create policy "own conditions insert" on public.user_conditions for insert to authenticated with check (user_id = (select auth.uid()));
create policy "own conditions delete" on public.user_conditions for delete to authenticated using (user_id = (select auth.uid()));

create table if not exists public.user_saves (
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  kind text not null check (kind in ('finding','condition','paper')),
  item_id text not null check (char_length(item_id) between 1 and 120),
  created_at timestamptz not null default now(),
  primary key (user_id, kind, item_id)
);
alter table public.user_saves enable row level security;
create policy "own saves select" on public.user_saves for select to authenticated using (user_id = (select auth.uid()));
create policy "own saves insert" on public.user_saves for insert to authenticated with check (user_id = (select auth.uid()));
create policy "own saves delete" on public.user_saves for delete to authenticated using (user_id = (select auth.uid()));

create table if not exists public.email_prefs (
  user_id uuid primary key default auth.uid() references auth.users(id) on delete cascade,
  alerts boolean not null default true,          -- new-study alerts for My conditions
  digest boolean not null default true,          -- weekly digest
  unsubscribe_token uuid not null unique default gen_random_uuid(),
  consent_at timestamptz not null default now(),
  last_digest_at timestamptz,
  updated_at timestamptz not null default now()
);
alter table public.email_prefs enable row level security;
create policy "own prefs select" on public.email_prefs for select to authenticated using (user_id = (select auth.uid()));
create policy "own prefs insert" on public.email_prefs for insert to authenticated with check (user_id = (select auth.uid()));
create policy "own prefs update" on public.email_prefs for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
-- users may only set their own on/off switches; token and send bookkeeping are server-side
revoke all on public.email_prefs from anon, authenticated;
grant select on public.email_prefs to authenticated;
grant insert (user_id, alerts, digest) on public.email_prefs to authenticated;
grant update (alerts, digest, updated_at) on public.email_prefs to authenticated;
revoke all on public.user_conditions, public.user_saves from anon;

-- one-click unsubscribe from email links (no sign-in): definer function lives in the unexposed private schema
create or replace function private.digest_unsub(p_token uuid) returns boolean
language plpgsql security definer set search_path = '' as $$
declare n int;
begin
  update public.email_prefs set alerts = false, digest = false, updated_at = now() where unsubscribe_token = p_token;
  get diagnostics n = row_count; return n > 0;
end $$;
revoke all on function private.digest_unsub(uuid) from public;
grant execute on function private.digest_unsub(uuid) to anon, authenticated;
create or replace function public.digest_unsubscribe(token uuid) returns boolean
language sql set search_path = '' as $$ select private.digest_unsub(token) $$;
grant execute on function public.digest_unsubscribe(uuid) to anon, authenticated;
