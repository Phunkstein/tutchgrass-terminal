import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { cleanFirstName, secretsMatch, skipGumroadPing, sourceFromGumroad, validEmail } from "../_shared/brevo.ts";
import { adminHeaders, appSecret, brevoAdd, json, serviceKey } from "../_shared/http.ts";

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ ok: false }, 405);
  const provided = new URL(req.url).searchParams.get("secret") ?? "";
  if (!secretsMatch(provided, await appSecret("GUMROAD_PING_SECRET"))) return json({ ok: false }, 401);

  const form = await req.formData().catch(() => null);
  if (!form) return json({ ok: false, error: "Expected a form post" }, 400);
  const resource = value(form, "resource_name") || "sale";
  const skipped = skipGumroadPing(resource, value(form, "refunded") === "true");
  if (skipped) return json({ ok: true, skipped });

  const email = value(form, "email").trim().toLowerCase();
  const source = sourceFromGumroad(value(form, "product_permalink"), value(form, "permalink"));
  if (!validEmail(email) || !source) return json({ ok: false, error: "Missing email or product permalink" }, 400);

  try {
    await brevoAdd(email, cleanFirstName(value(form, "full_name")), source);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Brevo request failed";
    const status = message === "BREVO_API_KEY is not set" ? 503 : 502;
    return json({ ok: false, error: status === 503 ? "Email service is not configured" : "Could not save the contact" }, status);
  }

  await remember(email, cleanFirstName(value(form, "full_name")), source);
  return json({ ok: true });
});

function value(form: FormData, key: string): string {
  const item = form.get(key);
  return typeof item === "string" ? item : "";
}

async function remember(email: string, firstName: string, source: string): Promise<void> {
  const url = Deno.env.get("SUPABASE_URL");
  const key = serviceKey();
  if (!url) return;
  const headers = adminHeaders(key, "return=minimal");
  const inserted = await fetch(`${url}/rest/v1/leads`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      email,
      name: firstName || null,
      source,
      forwarded_at: new Date().toISOString(),
      forward_provider: "brevo",
      forward_error: null,
    }),
  });
  if (inserted.status !== 409) return;
  await fetch(`${url}/rest/v1/leads?email=eq.${encodeURIComponent(email)}&forwarded_at=is.null`, {
    method: "PATCH",
    headers,
    body: JSON.stringify({
      forwarded_at: new Date().toISOString(),
      forward_provider: "brevo",
      forward_error: null,
    }),
  });
}
