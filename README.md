# Permitude for Claude Code

Design a deck — framing, hardware, code checks, and a permit-ready drawing set —
by describing what you want.

**Permitude is in closed beta.** Installing it takes an invitation, and your
invitation says how to start once it is installed.

## Install

In a terminal, from the folder you want to design in:

```bash
claude plugin marketplace add https://get.permitude.com/.claude-plugin/marketplace.json
claude plugin install permitude --scope project
```

`--scope project` keeps Permitude in that one folder: it loads when you start
Claude Code there, and in none of your other work. Leave the flag off and it
loads in every Claude Code session on the machine, which is rarely what you
want.

## Try it without installing

Permitude is a handful of files. You can read all of them before you trust any of them:

```bash
git clone https://github.com/Po-Hsun-Su/permitude-plugin
claude --plugin-dir ./permitude-plugin
```

That loads Permitude for that one session and writes nothing to your
configuration. Quit Claude Code and it is gone.

## Requirements

- Claude Code, with an active Claude subscription
- `git` and Python 3

On macOS and Linux both are usually already there. On Windows you'll need
[Git for Windows](https://git-scm.com/download/win) and Python 3, set up so that
`git` and `python3` both work in a new terminal — or simply ask Claude Code to
sort it out for you before you install.

## Privacy

Permitude receives the deck design it checks for you: designing a deck is what
you came for, and the design has to reach us to be checked and drawn. It is sent
only when a check runs — the one file that check names, plus the version stamp
of the reference library Permitude itself writes into your folder, so a check
can tell you when that reference copy is out of date.

One more thing can be sent, and only when your agent chooses to: a short
note it writes when something in Permitude's own kit gets in its way — a
check that fired wrongly, a missing function, a page that drew wrong. The
note is the agent's words about that defect, tied to your last check so we
can reproduce it; it is how the kit gets fixed for everyone.

Nothing else is sent: never your message text, and never your other files.
Details and options: <https://permitude.com/privacy>.

## Auto mode and defect notes

Claude Code's auto mode holds that defect note for your approval each time —
it is a message leaving your folder, and auto mode's safety check treats it
as one no matter how routine it is. Your design work never waits on it: a
held note is skipped and the agent carries on. If you would rather the
notes go through without asking, allow the one tool in your Claude Code
settings (`.claude/settings.json` in the design folder, or
`~/.claude/settings.json` for every folder):

```json
{
  "permissions": {
    "allow": ["mcp__plugin_permitude_permitude__report_issue"]
  }
}
```

That allows exactly that tool and nothing else about auto mode changes.

## Support

<support@permitude.com>
