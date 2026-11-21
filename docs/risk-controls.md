# Risk controls

Reading a logged-in Instagram account with third-party tools is against Instagram's terms and can lead to a checkpoint, a temporary block or a ban. These rules reduce the risk. They do not remove it.

## Before you start

- **Use a secondary account if you can.** Save the posts you care about to it, or accept the risk on your main account knowingly. doughrun's own README recommends a secondary account.
- **Pilot first.** Run one small folder (3 to 5 posts) and look at the result before anything bigger.
- **Be present for every login.** You type the password and 2FA in the browser window. It is never pasted into a chat, a note or a file.

## While running

- Batches of 20 to 30 posts, with a pause between batches.
- One folder at a time. Stop at the first sign of trouble.
- Pull each post once and keep the note. Do not re-scrape.
- Read-only only. Nothing that likes, follows, comments or posts.

## If Instagram shows a checkpoint or warning

Stop. Do not retry in a loop. Open Instagram normally in your own browser, finish any verification it asks for, and wait at least a day before the next batch. If you were asked to change your password, do it, then delete the stored sessions (see Cleanup) and log in again later.

## Review the permissions change

doughrun's setup adds allow rules to your Claude Code `settings.json`. Before accepting it:

- [ ] `git diff` or compare `~/.claude/settings.json` before and after.
- [ ] Every new rule points at the plugin's own folder and its scripts, nothing broader.
- [ ] No rule allows arbitrary shell commands, network access to other hosts or paths outside `ig-tools\`.
- [ ] If any rule is broader than that, remove it and approve prompts one at a time instead.

## Keep private data out of git

Sessions, cookies, downloaded media and your notes are never committed. `.gitignore` blocks them and `scripts/check_no_secrets.py` fails the commit and CI if one slips through. Enable the hook once: `git config core.hooksPath .githooks`.

## Cleanup (when the sweep is done)

- Delete `~/.instagram-mcp/sessions/` and `~/.instagram-mcp/downloads/`.
- Delete doughrun's browser profile and any downloaded media it kept.
- Remove the tools if you no longer need them: `claude mcp remove instagram`, `claude plugin uninstall instagram-scraper@instagram-scraper`.
- Log out of any "Where you're logged in" sessions you do not recognise in Instagram's Accounts Center.
