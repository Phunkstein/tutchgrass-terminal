import test from "node:test";
import assert from "node:assert/strict";
import {
  BREVO_LIST_ID,
  cleanFirstName,
  contactBody,
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

test("secret compare fails closed", () => {
  assert.equal(secretsMatch("correct", "correct"), true);
  assert.equal(secretsMatch("wrong", "correct"), false);
  assert.equal(secretsMatch("", "correct"), false);
  assert.equal(secretsMatch("correct", undefined), false);
});
