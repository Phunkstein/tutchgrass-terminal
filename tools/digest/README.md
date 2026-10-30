# Tutchgrass digest / alerts

`send_digest.py` emails opted-in users the new PubMed studies for the conditions they picked (My Condition), using the Brevo transactional API (`POST https://api.brevo.com/v3/smtp/email`, header `api-key`).

**Status: not sending.** It needs `BREVO_API_KEY` (Brevo account Arkitekt@myyahoo.com) and `SUPABASE_SERVICE_ROLE_KEY`. Without both keys, `--send` refuses. The default is a dry run that writes previews to `out/`.

- Opt-in: an `email_prefs` row is created at sign-in with alerts and digest on by default. Users can switch them off in their account, or by clicking the one-click link `/terminal/unsubscribe/?t=<token>` (RPC `digest_unsubscribe`).
- Content: plain-words "what they did / what the authors concluded" plus an honest grade caveat. Research, not medical advice.
- Schedule it (after keys are added) as a Render cron: `python3 tools/digest/send_digest.py --send` daily for alerts, and `--mode digest --send` weekly.
