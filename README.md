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

Permitude is five files. You can read all of them before you trust any of them:

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

Permitude receives diagnostic events about the sessions it is loaded in — never
your message text, your files, or their contents. Installed with `--scope
project` it is loaded in that folder only, so your other work sends nothing at
all. Details and options: <https://permitude.com/privacy>.

## Support

<support@permitude.com>
