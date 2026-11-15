import test from "node:test";
import assert from "node:assert/strict";
import {
  BREVO_LIST_ID,
  GTA6_PARENTS_LIST_ID,
  GTA6_PARENTS_SOURCE,
  GTA6_WELCOME_SUBJECT,
  cleanFirstName,
  contactBody,
  gta6WelcomeEmail,
  secretsMatch,
  skipGumroadPing,
  sourceFromGumroad,
  validEmail,
  validSource,
} from "./brevo.ts";

test("contact body matches the Brevo list contract", () => {
  assert.deepEqual(contactBody("ada@example.com", "Ada", "facing-homelessness"), {
    email: "ada@example.com",
    attributes: { FIRSTNAME: "Ada", SOURCE: "facing-homelessness" },
    listIds: [BREVO_LIST_ID],
    updateEnabled: true,
  });
  assert.equal(BREVO_LIST_ID, 3);
});

test("refunds and disputes are not added to the list", () => {
  assert.equal(skipGumroadPing("sale", false), null);
  assert.equal(skipGumroadPing("sale", true), "refunded");
  assert.equal(skipGumroadPing("refund", false), "refund");
  assert.equal(skipGumroadPing("dispute", false), "dispute");
});

test("gumroad source uses the permalink slug", () => {
  assert.equal(sourceFromGumroad("rbpkuj"), "gumroad-rbpkuj");
  assert.equal(sourceFromGumroad("https://gum.co/wvkrs"), "gumroad-wvkrs");
  assert.equal(sourceFromGumroad("", "Cqjggg"), "gumroad-cqjggg");
  assert.equal(sourceFromGumroad(""), null);
  assert.equal(validSource("gumroad-rbpkuj"), true);
  assert.equal(validSource("Facing"), false);
});

test("email and first name checks", () => {
  assert.equal(validEmail("ada@example.com"), true);
  assert.equal(validEmail("nope"), false);
  assert.equal(cleanFirstName("  Ada Lovelace "), "Ada");
  assert.equal(cleanFirstName(""), "");
});

test("gta6 parents contacts join list 6 and other sources stay on list 3", () => {
  const gta = contactBody("parent@example.com", "Sam", GTA6_PARENTS_SOURCE);
  assert.deepEqual(gta.listIds, [GTA6_PARENTS_LIST_ID]);
  assert.equal(GTA6_PARENTS_LIST_ID, 6);
  assert.equal(gta.attributes.SOURCE, GTA6_PARENTS_SOURCE);
  assert.deepEqual(contactBody("ada@example.com", "Ada", "72-hour").listIds, [BREVO_LIST_ID]);
  assert.deepEqual(contactBody("ada@example.com", "Ada", "gumroad-wvkrs").listIds, [3]);
  const kept = contactBody("ada@example.com", "", GTA6_PARENTS_SOURCE, { keepSource: true });
  assert.deepEqual(kept.listIds, [6]);
  assert.equal("SOURCE" in kept.attributes, false);
  assert.equal("FIRSTNAME" in kept.attributes, false);
});

test("gta6 welcome email confirms the list without a client secret", () => {
  const mail = gta6WelcomeEmail("parent@example.com", "Sam");
  assert.equal(mail.subject, GTA6_WELCOME_SUBJECT);
  assert.deepEqual(mail.sender, { name: "Tutchgrass Labs", email: "deals@tutchgrass.co" });
  assert.deepEqual(mail.to, [{ email: "parent@example.com", name: "Sam" }]);
  assert.match(mail.textContent, /one update after launch, weekly through December 2026, plus any major change/);
  assert.match(mail.textContent, /If GTA 6 ever opens private servers/);
  assert.match(mail.textContent, /unsubscribe/i);
  assert.equal(JSON.stringify(mail).includes("api-key"), false);
  assert.equal(JSON.stringify(mail).includes("BREVO"), false);
  const blank = gta6WelcomeEmail("parent@example.com", "");
  assert.deepEqual(blank.to, [{ email: "parent@example.com" }]);
  assert.match(blank.textContent, /^Hi,/);
});

test("secret compare fails closed", () => {
  assert.equal(secretsMatch("correct", "correct"), true);
  assert.equal(secretsMatch("wrong", "correct"), false);
  assert.equal(secretsMatch("", "correct"), false);
  assert.equal(secretsMatch("correct", undefined), false);
});
