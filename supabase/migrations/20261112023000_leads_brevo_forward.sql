-- Forward public.leads to Brevo list 3, and accept Gumroad Ping on an edge function.
-- BREVO_API_KEY and GUMROAD_PING_SECRET are Edge Function secrets, not stored here.
-- The trigger secret below is generated in Vault and never leaves the database.

create schema if not exists extensions;
create extension if not exists pg_net with schema extensions;
create extension if not exists pg_cron;
create schema if not exists private;

alter table public.leads drop constraint if exists leads_source_ok;
alter table public.leads add constraint leads_source_ok
  check (source ~ '^[a-z0-9][a-z0-9-]{0,78}$');

drop policy if exists "leads anon insert" on public.leads;
create policy "leads anon insert"
  on public.leads
  for insert
  to anon
  with check (
    source ~ '^[a-z0-9][a-z0-9-]{0,78}$'
    and email = lower(email)
    and forwarded_at is null
    and forward_provider is null
    and forward_error is null
  );

comment on table public.leads is
  'Prep-guide signups. Anon insert only. A trigger forwards new rows to Brevo list 3.';
comment on column public.leads.source is
  'Brevo SOURCE attribute. Facing Homelessness uses facing-homelessness. Gumroad uses gumroad-<permalink>.';
comment on column public.leads.forwarded_at is
  'Null until Brevo accepts the contact.';
comment on column public.leads.forward_provider is
  'brevo after a successful forward.';

do $$
begin
  if not exists (select 1 from vault.secrets where name = 'lead_forward_secret') then
    perform vault.create_secret(
      encode(gen_random_bytes(32), 'hex'),
      'lead_forward_secret',
      'Header the leads trigger sends to the lead-to-brevo edge function'
    );
  end if;
end $$;

create or replace function private.lead_forward_ok(p_token text)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select coalesce(p_token, '') <> ''
     and p_token = (
       select decrypted_secret
       from vault.decrypted_secrets
       where name = 'lead_forward_secret'
       limit 1
     );
$$;

revoke all on function private.lead_forward_ok(text) from public, anon, authenticated;
grant execute on function private.lead_forward_ok(text) to service_role;

create or replace function public.lead_forward_ok(p_token text)
returns boolean
language sql
stable
security invoker
set search_path = ''
as $$
  select private.lead_forward_ok(p_token);
$$;

revoke all on function public.lead_forward_ok(text) from public, anon, authenticated;
grant execute on function public.lead_forward_ok(text) to service_role;
grant usage on schema private to anon, authenticated, service_role;

create or replace function private.queue_lead_to_brevo()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  secret text;
begin
  if NEW.forwarded_at is not null then
    return NEW;
  end if;
  select decrypted_secret into secret
  from vault.decrypted_secrets
  where name = 'lead_forward_secret';
  if secret is null then
    raise warning 'lead_forward_secret is missing; signup was stored and not queued';
    return NEW;
  end if;
  perform net.http_post(
    url := 'https://ckauuurdpltrqjimjgbt.supabase.co/functions/v1/lead-to-brevo',
    body := jsonb_build_object('backfill', true),
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'x-forward-secret', secret
    ),
    timeout_milliseconds := 20000
  );
  return NEW;
end;
$$;

revoke all on function private.queue_lead_to_brevo() from public;
grant execute on function private.queue_lead_to_brevo() to anon, authenticated, service_role;

drop trigger if exists leads_brevo_forward on public.leads;
create trigger leads_brevo_forward
  after insert on public.leads
  for each row
  execute function private.queue_lead_to_brevo();

select cron.unschedule(jobid)
from cron.job
where jobname = 'leads-brevo-retry';

select cron.schedule(
  'leads-brevo-retry',
  '*/5 * * * *',
  $cron$
  select net.http_post(
    url := 'https://ckauuurdpltrqjimjgbt.supabase.co/functions/v1/lead-to-brevo',
    body := '{"backfill":true}'::jsonb,
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'x-forward-secret', (
        select decrypted_secret from vault.decrypted_secrets where name = 'lead_forward_secret'
      )
    ),
    timeout_milliseconds := 20000
  );
  $cron$
);

notify pgrst, 'reload schema';
