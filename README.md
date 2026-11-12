# Permitude

Design a deck with the AI agent you already use. Permitude builds it in 3D,
checks it against the building code, and draws the permit set.

**Free during the open beta.** Each sheet notes it came from the beta.
Questions: <support@permitude.com>.

## Requirements

- Claude Code, Codex CLI or Antigravity CLI, with an active subscription
- `git` and Python 3 (usually already there on macOS and Linux)
- On Windows: [Git for Windows](https://git-scm.com/install/windows) and
  [Python 3.13 from the Microsoft Store](https://apps.microsoft.com/detail/9pnrbtzxmb4z).
  Not the python.org installer: it has no `python3` command.

## Install

Run these in the folder you'll design in. One folder can hold more than one
agent's install.

### Claude Code

```bash
claude plugin marketplace add https://get.permitude.com/.claude-plugin/marketplace.json
claude plugin install permitude --scope project
```

`--scope project` keeps Permitude in this folder only. To remove it:
`claude plugin uninstall permitude --scope project`.

### Codex CLI

```bash
codex plugin marketplace add Po-Hsun-Su/permitude-plugin
codex plugin add permitude@permitude
```

This installs for your whole machine. Then start Codex in your folder and
type:

- `/hooks`, and trust both hooks (a design check can't read your design
  file until you do)
- `/mcp login permitude` to sign in

To remove it: `codex plugin remove permitude@permitude`.

### Antigravity CLI

```bash
agy plugin install https://github.com/Po-Hsun-Su/permitude-plugin
```

Needs Antigravity CLI 1.4.0 or later (`agy --version`). This installs for
your whole machine. To remove it: `agy plugin uninstall permitude`.

## Try it without installing

Permitude is a handful of files you can read first:

```bash
git clone https://github.com/Po-Hsun-Su/permitude-plugin
claude --plugin-dir ./permitude-plugin
```

That loads it for one Claude Code session and changes nothing in your
settings.

## Privacy

What Permitude receives:

- **When a check runs:** the one design file it checks, that file's name
  inside your folder (never where that folder is on your computer), and the
  version of the reference files Permitude wrote into your folder.
- **With every call your agent makes to Permitude**, once you've set your
  property: the small record Permitude keeps in your folder,
  `.permitude/site_data.json` (the address, the parcel number and the date
  it was looked up), so each call says which project it's about.
- **Only if your agent sends one:** a short note about a problem in
  Permitude itself (a check that fired wrongly, a missing function, a page
  that drew wrong), tied to your last check so we can fix it.

Never your messages, and never your other files. Details and options:
<https://permitude.com/privacy>.

## Auto mode and problem notes

Claude Code's auto mode asks you to approve each problem note, because it
leaves your folder. Your design work never waits on it: a held note is
skipped. To let notes through without asking, allow this one tool in
`.claude/settings.json` (this folder) or `~/.claude/settings.json` (every
folder):

```json
{
  "permissions": {
    "allow": ["mcp__plugin_permitude_permitude__report_issue"]
  }
}
```

Nothing else about auto mode changes.

## Support

<support@permitude.com>
