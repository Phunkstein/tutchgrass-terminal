-- GTA 6 parents signups reuse public.leads.
-- A new row with source gta6-parents is forwarded by the existing insert trigger
-- to Brevo list 6, which also sends the welcome email.
-- An email already stored for another guide can still join that list.

alter table public.leads add column if not exists gta6_welcomed_at timestamptz;
alter table public.leads add column if not exists gta6_queued_at timestamptz;
alter table public.leads add column if not exists gta6_error text;

alter table public.leads drop constraint if exists leads_gta6_error_len;
alter table public.leads add constraint leads_gta6_error_len
  check (gta6_error is null or char_length(gta6_error) <= 500);

comment on column public.leads.gta6_welcomed_at is
  'Set when Brevo list 6 accepted this email and the GTA 6 parents welcome email was accepted.';
comment on column public.leads.gta6_queued_at is
  'Set when an existing lead asked to join the GTA 6 parents list and the welcome is not confirmed yet.';
comment on column public.leads.gta6_error is
  'Last error while adding an existing lead to the GTA 6 parents list. Null after success.';

create or replace function private.signup_gta6_parent(p_email text, p_name text)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  clean_email text := lower(trim(coalesce(p_email, '')));
  clean_name text := nullif(trim(coalesce(p_name, '')), '');
  queued_count integer := 0;
  secret text;
begin
  if char_length(clean_email) < 6
     or char_length(clean_email) > 320
     or clean_email !~ '^[^@\s]+@[^@\s]+\.[^@\s]+$' then
    return 'invalid';
  end if;
  if clean_name is not null and char_length(clean_name) > 80 then
    return 'invalid';
  end if;

  begin
    insert into public.leads (email, name, source)
    values (clean_email, clean_name, 'gta6-parents');
    return 'created';
  exception
    when unique_violation then
      null;
  end;

  update public.leads
     set gta6_queued_at = now(),
         name = coalesce(clean_name, public.leads.name)
   where public.leads.email = clean_email
     and public.leads.gta6_welcomed_at is null
     and public.leads.gta6_queued_at is null
     and not (
       public.leads.source = 'gta6-parents'
       and public.leads.forwarded_at is null
     );
  get diagnostics queued_count = row_count;
  if queued_count = 0 then
    return 'already';
  end if;

  select decrypted_secret into secret
  from vault.decrypted_secrets
  where name = 'lead_forward_secret';
  if secret is not null then
    perform net.http_post(
      url := 'https://ckauuurdpltrqjimjgbt.supabase.co/functions/v1/lead-to-brevo',
      body := jsonb_build_object('backfill', true),
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'x-forward-secret', secret
      ),
      timeout_milliseconds := 20000
    );
  end if;
  return 'queued';
end;
$$;

revoke all on function private.signup_gta6_parent(text, text) from public, anon, authenticated;
grant execute on function private.signup_gta6_parent(text, text) to anon, authenticated, service_role;

create or replace function public.signup_gta6_parent(p_email text, p_name text default null)
returns text
language sql
volatile
security invoker
set search_path = ''
as $$
  select private.signup_gta6_parent(p_email, p_name);
$$;

revoke all on function public.signup_gta6_parent(text, text) from public;
grant execute on function public.signup_gta6_parent(text, text) to anon, authenticated, service_role;

notify pgrst, 'reload schema';
