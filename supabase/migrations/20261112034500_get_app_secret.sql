-- Record public.get_app_secret, already deployed on project ckauuurdpltrqjimjgbt.
-- Edge functions call it with the service role when BREVO_API_KEY or
-- GUMROAD_PING_SECRET is not in the function environment.
-- The function is SECURITY DEFINER so it can read vault.decrypted_secrets.
-- Execute is limited to service_role. anon, authenticated, and public cannot call it.

create or replace function public.get_app_secret(name text)
returns text
language sql
stable
security definer
set search_path = ''
as $$
  select ds.decrypted_secret
  from vault.decrypted_secrets ds
  where ds.name = get_app_secret.name
    and get_app_secret.name in ('BREVO_API_KEY', 'GUMROAD_PING_SECRET')
  limit 1;
$$;

revoke execute on function public.get_app_secret(text) from public, anon, authenticated;
grant execute on function public.get_app_secret(text) to service_role;

notify pgrst, 'reload schema';
