export const BREVO_LIST_ID = 3;
export const BREVO_CONTACTS_URL = "https://api.brevo.com/v3/contacts";

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const SOURCE = /^[a-z0-9][a-z0-9-]{0,78}$/;

export function validEmail(email: string): boolean {
  return email.length >= 6 && email.length <= 320 && EMAIL.test(email);
}

export function validSource(source: string): boolean {
  return SOURCE.test(source);
}

export function cleanFirstName(value: string | null | undefined): string {
  const name = (value ?? "").trim().replace(/\s+/g, " ");
  const first = name.split(" ")[0] ?? "";
  return first.slice(0, 80);
}

export function slugFromPermalink(raw: string): string {
  let value = raw.trim();
  if (/^https?:\/\//i.test(value)) {
    try {
      const parts = new URL(value).pathname.split("/").filter(Boolean);
      value = parts[parts.length - 1] ?? "";
    } catch {
      value = value.split("/").filter(Boolean).pop() ?? "";
    }
  } else if (value.includes("/")) {
    value = value.split("/").filter(Boolean).pop() ?? "";
  }
  return value.toLowerCase().replace(/[^a-z0-9-]/g, "").replace(/^-+|-+$/g, "").slice(0, 60);
}

export function skipGumroadPing(resource: string, refunded: boolean): string | null {
  if (refunded) return "refunded";
  if (resource === "refund" || resource === "dispute") return resource;
  return null;
}

export function sourceFromGumroad(productPermalink: string, permalink = ""): string | null {
  for (const raw of [productPermalink, permalink]) {
    const slug = slugFromPermalink(raw);
    if (slug) return `gumroad-${slug}`;
  }
  return null;
}

export function contactBody(email: string, firstName: string, source: string) {
  return {
    email,
    attributes: { FIRSTNAME: firstName, SOURCE: source },
    listIds: [BREVO_LIST_ID],
    updateEnabled: true as const,
  };
}

export function timingSafeEqual(a: string, b: string): boolean {
  const enc = new TextEncoder();
  const left = enc.encode(a);
  const right = enc.encode(b);
  const len = Math.max(left.length, right.length);
  let out = left.length === right.length ? 0 : 1;
  for (let i = 0; i < len; i++) out |= (left[i] ?? 0) ^ (right[i] ?? 0);
  return out === 0;
}

export function secretsMatch(provided: string, expected: string | undefined): boolean {
  if (!expected || !provided) return false;
  return timingSafeEqual(provided, expected);
}
