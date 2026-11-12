-- Tutchgrass Prep lead magnet: Facing Homelessness guide signups.
-- Anonymous visitors may insert email, name, and source. They cannot read or update.
--
-- name is the optional first name. source is the list/tag key for a later email tool
-- (Kit, MailerLite, or similar). Nothing here calls that tool.
--
-- A later server-side job can forward new rows and mark them sent. Use the
-- service role or the SQL editor, never the browser:
--   select email, name, source, consent_at, created_at
--   from public.leads
--   where forwarded_at is null
--   order by created_at;
--   update public.leads
--      set forwarded_at = now(), forward_provider = 'kit', forward_error = null
--    where email = 'person@example.com';
--
-- View or export every column from the Supabase dashboard
-- (Table Editor → public.leads), or:
--   select email, name, source, consent_text, consent_at,
--          forwarded_at, forward_provider, forward_error, created_at
--   from public.leads
--   order by created_at desc;

create table if not exists public.leads (
  email text primary key,
  name text,
  source text not null default 'facing-homelessness',
  created_at timestamptz not null default now(),
  constraint leads_email_format check (
    char_length(email) between 6 and 320
    and email = lower(email)
    and email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'
  ),
  constraint leads_name_len check (name is null or char_length(name) between 1 and 80),
  constraint leads_source_ok check (source = 'facing-homelessness')
);

alter table public.leads add column if not exists consent_text text;
alter table public.leads add column if not exists consent_at timestamptz;
alter table public.leads add column if not exists forwarded_at timestamptz;
alter table public.leads add column if not exists forward_provider text;
alter table public.leads add column if not exists forward_error text;

update public.leads
   set consent_text = 'We''ll email you occasional prep guides. Unsubscribe anytime.'
 where consent_text is null;

update public.leads
   set consent_at = created_at
 where consent_at is null;

alter table public.leads alter column consent_text set default 'We''ll email you occasional prep guides. Unsubscribe anytime.';
alter table public.leads alter column consent_text set not null;
alter table public.leads alter column consent_at set default now();
alter table public.leads alter column consent_at set not null;

alter table public.leads drop constraint if exists leads_consent_text_len;
alter table public.leads add constraint leads_consent_text_len
  check (char_length(consent_text) between 1 and 200);

alter table public.leads drop constraint if exists leads_forward_provider_len;
alter table public.leads add constraint leads_forward_provider_len
  check (forward_provider is null or char_length(forward_provider) between 1 and 40);

alter table public.leads drop constraint if exists leads_forward_error_len;
alter table public.leads add constraint leads_forward_error_len
  check (forward_error is null or char_length(forward_error) <= 500);

alter table public.leads enable row level security;

drop policy if exists "leads anon insert" on public.leads;
create policy "leads anon insert"
  on public.leads
  for insert
  to anon
  with check (
    source = 'facing-homelessness'
    and email = lower(email)
    and forwarded_at is null
    and forward_provider is null
    and forward_error is null
  );

revoke all on table public.leads from anon, authenticated, public;
grant insert (email, name, source) on table public.leads to anon;
grant select, insert, update, delete on table public.leads to service_role;

comment on table public.leads is
  'Prep-guide signups. Anon insert only. forwarded_at is null until a server-side job sends the row to an email service.';
comment on column public.leads.name is 'Optional first name for the email tool.';
comment on column public.leads.source is 'List or tag key. Facing Homelessness uses facing-homelessness.';
comment on column public.leads.forwarded_at is 'Null until this signup is created in Kit, MailerLite, or a similar service.';
comment on column public.leads.forward_provider is 'Which email service accepted the row, for example kit or mailerlite.';
comment on column public.leads.forward_error is 'Last forward error. Null after a successful send.';
