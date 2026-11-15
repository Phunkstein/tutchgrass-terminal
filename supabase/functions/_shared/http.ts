import {
  BREVO_CONTACTS_URL,
  BREVO_SMTP_URL,
  GTA6_PARENTS_SOURCE,
  contactBody,
  gta6WelcomeEmail,
} from "./brevo.ts";

export function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export function serviceKey(): string {
  const legacy = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (legacy) return legacy;
  const raw = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (!raw) throw new Error("No service key in the function environment");
  const keys = JSON.parse(raw) as Record<string, string>;
  const key = keys.default || Object.values(keys)[0];
  if (!key) throw new Error("No service key in the function environment");
  return key;
}

export function adminHeaders(key: string, prefer?: string): Record<string, string> {
  const headers: Record<string, string> = {
    apikey: key,
    "content-type": "application/json",
  };
  if (key.startsWith("eyJ")) headers.authorization = `Bearer ${key}`;
  if (prefer) headers.prefer = prefer;
  return headers;
}

const secretCache = new Map<string, string>();

export async function appSecret(name: string): Promise<string | undefined> {
  const fromEnv = Deno.env.get(name);
  if (fromEnv) return fromEnv;
  const cached = secretCache.get(name);
  if (cached) return cached;
  const url = Deno.env.get("SUPABASE_URL");
  if (!url) return undefined;
  try {
    const res = await fetch(`${url}/rest/v1/rpc/get_app_secret`, {
      method: "POST",
      headers: adminHeaders(serviceKey()),
      body: JSON.stringify({ name }),
    });
    if (!res.ok) return undefined;
    const value = await res.json();
    if (typeof value !== "string" || !value) return undefined;
    secretCache.set(name, value);
    return value;
  } catch {
    return undefined;
  }
}

export async function brevoAdd(
  email: string,
  firstName: string,
  source: string,
  options?: { keepSource?: boolean },
): Promise<void> {
  const key = await appSecret("BREVO_API_KEY");
  if (!key) throw new Error("BREVO_API_KEY is not set");
  const payload = contactBody(email, firstName, source, options);
  let res = await postContact(key, payload);
  if (res.status === 400) {
    const text = await res.text();
    if (!/attribute/i.test(text)) throw new Error(text.slice(0, 480));
    await ensureSourceAttribute(key);
    res = await postContact(key, payload);
  }
  if (res.status !== 201 && res.status !== 204) throw new Error(await clip(res));
  if (source === GTA6_PARENTS_SOURCE) await sendGta6Welcome(key, email, firstName);
}

async function sendGta6Welcome(key: string, email: string, firstName: string): Promise<void> {
  const res = await fetch(BREVO_SMTP_URL, {
    method: "POST",
    headers: {
      "api-key": key,
      accept: "application/json",
      "content-type": "application/json",
    },
    body: JSON.stringify(gta6WelcomeEmail(email, firstName)),
  });
  if (res.status === 201) return;
  throw new Error(await clip(res));
}

function postContact(key: string, payload: ReturnType<typeof contactBody>): Promise<Response> {
  return fetch(BREVO_CONTACTS_URL, {
    method: "POST",
    headers: {
      "api-key": key,
      accept: "application/json",
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

async function ensureSourceAttribute(key: string): Promise<void> {
  await fetch("https://api.brevo.com/v3/contacts/attributes/normal/SOURCE", {
    method: "POST",
    headers: {
      "api-key": key,
      accept: "application/json",
      "content-type": "application/json",
    },
    body: JSON.stringify({ type: "text" }),
  });
}

async function clip(res: Response): Promise<string> {
  const text = await res.text();
  return text.slice(0, 480);
}
