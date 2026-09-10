# Open Questions

- Does `RemoteTrigger`'s `sources.git_repository` mechanism actually reject
  non-GitHub URLs outright, or would a GitLab (or other host) URL work via
  plain `git clone` inside the sandbox given network access + an embedded
  token? Moot for this project (we moved to GitHub), but relevant if a
  future project needs to stay on GitLab.
- How does context compaction interact with a long cloud-routine run — does
  the routine's session compact the same way an interactive session does,
  and is there any user-visible signal before it happens?
- What exactly triggers the auto-mode classifier (beyond the two cases hit
  tonight: credential generation via `ssh-keygen`, self-editing
  `.claude/settings.json`)? Worth knowing before assuming any given command
  is safe to run unattended.
- Real end-to-end validation of the scheduled continuation is still
  pending — the plan is sound on paper (per `RemoteTrigger`'s documented
  behaviour) but hasn't yet been observed firing and picking up from
  `STATE.md` for real. First thing to check when the routine's run log is
  available.
