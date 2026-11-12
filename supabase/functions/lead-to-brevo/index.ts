import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { cleanFirstName, validEmail, validSource } from "../_shared/brevo.ts";
import { adminHeaders, appSecret, brevoAdd, json, serviceKey } from "../_shared/http.ts";

type Lead = {
  email: string;
  name: string | null;
  source: string;
  forward_error: string | null;
};

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ ok: false }, 405);
  const key = serviceKey();
  const url = Deno.env.get("SUPABASE_URL");
  if (!url) return json({ ok: false, error: "SUPABASE_URL is not set" }, 500);
  const header = req.headers.get("x-forward-secret") ?? "";
  const allowed = await forwardAllowed(url, key, header);
  if (!allowed) return json({ ok: false }, 401);

  const rows = await pending(url, key);
  if (!rows) return json({ ok: false, error: "Could not read leads" }, 500);
  const todo = rows.filter((row) => !row.forward_error?.startsWith("stop:"));
  if (todo.length === 0) return json({ ok: true, forwarded: 0, failed: 0 });

  let forwarded = 0;
  let failed = 0;
  for (const row of todo) {
    const email = row.email.trim().toLowerCase();
    const source = row.source.trim().toLowerCase();
    if (!validEmail(email) || !validSource(source)) {
      await mark(url, key, email, "stop: invalid lead", true);
      failed += 1;
      continue;
    }
    try {
      await brevoAdd(email, cleanFirstName(row.name), source);
      await mark(url, key, email, null, true);
      forwarded += 1;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Brevo request failed";
      await mark(url, key, email, `retry: ${message}`.slice(0, 500), false);
      failed += 1;
    }
  }
  const missingKey = failed > 0 && !(await appSecret("BREVO_API_KEY"));
  return json(
    { ok: failed === 0, forwarded, failed },
    missingKey ? 503 : failed > 0 && forwarded === 0 ? 502 : 200,
  );
});

async function forwardAllowed(url: string, key: string, token: string): Promise<boolean> {
  if (!token) return false;
  const res = await fetch(`${url}/rest/v1/rpc/lead_forward_ok`, {
    method: "POST",
    headers: adminHeaders(key),
    body: JSON.stringify({ p_token: token }),
  });
  if (!res.ok) return false;
  return (await res.json()) === true;
}

async function pending(url: string, key: string): Promise<Lead[] | null> {
  const res = await fetch(
    `${url}/rest/v1/leads?forwarded_at=is.null&select=email,name,source,forward_error&order=created_at.asc&limit=50`,
    { headers: adminHeaders(key) },
  );
  if (!res.ok) return null;
  return await res.json();
}

async function mark(url: string, key: string, email: string, error: string | null, sent: boolean): Promise<void> {
  const body = sent
    ? { forwarded_at: new Date().toISOString(), forward_provider: "brevo", forward_error: error }
    : { forward_error: error };
  await fetch(`${url}/rest/v1/leads?email=eq.${encodeURIComponent(email)}`, {
    method: "PATCH",
    headers: adminHeaders(key, "return=minimal"),
    body: JSON.stringify(body),
  });
}
