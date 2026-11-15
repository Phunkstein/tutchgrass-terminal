export const BREVO_LIST_ID = 3;
export const GTA6_PARENTS_LIST_ID = 6;
export const GTA6_PARENTS_SOURCE = "gta6-parents";
export const GTA6_WELCOME_SUBJECT = "You're on the GTA 6 parent news & tips list";
export const BREVO_CONTACTS_URL = "https://api.brevo.com/v3/contacts";
export const BREVO_SMTP_URL = "https://api.brevo.com/v3/smtp/email";

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

export function listIdForSource(source: string): number {
  return source === GTA6_PARENTS_SOURCE ? GTA6_PARENTS_LIST_ID : BREVO_LIST_ID;
}

export function contactBody(
  email: string,
  firstName: string,
  source: string,
  options?: { keepSource?: boolean },
) {
  const attributes: Record<string, string> = {};
  if (options?.keepSource) {
    if (firstName) attributes.FIRSTNAME = firstName;
  } else {
    attributes.FIRSTNAME = firstName;
    attributes.SOURCE = source;
  }
  return {
    email,
    attributes,
    listIds: [listIdForSource(source)],
    updateEnabled: true as const,
  };
}

export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function gta6WelcomeEmail(email: string, firstName: string) {
  const hello = firstName ? `Hi ${firstName},` : "Hi,";
  const text = [
    hello,
    "",
    "You're signed up for GTA 6 parent news & tips.",
    "",
    "What to expect: launch news, rating changes, and quick tips. This list does not include the paid guide.",
    "",
    "Guide updates are delivered free to buyers through Gumroad: https://arkitekture3.gumroad.com/l/mgfjd",
    "",
    "The site: https://gta6parents.com/",
    "",
    "You can unsubscribe anytime by replying to this email or writing deals@tutchgrass.co with the subject Unsubscribe.",
    "",
    "Tutchgrass Labs",
  ].join("\n");
  const safeHello = firstName ? `Hi ${escapeHtml(firstName)},` : "Hi,";
  const html = [
    '<div style="max-width:560px;margin:auto;font:16px/1.5 Arial,sans-serif;color:#14201a">',
    `<p>${safeHello}</p>`,
    '<p>You\'re signed up for <a href="https://gta6parents.com/updates/">GTA 6 parent news & tips</a>.</p>',
    "<p>What to expect: launch news, rating changes, and quick tips. This list does not include the paid guide.</p>",
    '<p>Guide updates are delivered free to buyers through Gumroad. <a href="https://arkitekture3.gumroad.com/l/mgfjd">Get the parent\'s guide · $9.99</a>.</p>',
    '<p style="font-size:13px;color:#5d6a62">You can unsubscribe anytime by replying to this email or writing deals@tutchgrass.co with the subject Unsubscribe.</p>',
    "<p>Tutchgrass Labs</p>",
    "</div>",
  ].join("");
  return {
    sender: { name: "Tutchgrass Labs", email: "deals@tutchgrass.co" },
    to: firstName ? [{ email, name: firstName }] : [{ email }],
    subject: GTA6_WELCOME_SUBJECT,
    textContent: text,
    htmlContent: html,
    tags: [GTA6_PARENTS_SOURCE],
    headers: {
      "List-Unsubscribe": "<mailto:deals@tutchgrass.co?subject=Unsubscribe%20GTA%206%20parents>",
    },
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
