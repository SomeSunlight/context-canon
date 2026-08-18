# Official Context

`CONTEXT.md` is the generated official notice board for a node.

It answers one question:

> What applies here?

It should not force readers to reconstruct inheritance, inspect provenance, or understand compiler internals.

## One canonical result

The same compiled official context:

- applies to the current node,
- is the primary context read by humans and agents,
- is the package meaning published to child nodes.

This invariant prevents a parent from operating under rules different from those its children inherit.

## Content first

The official Markdown should remain compact and readable even when many rules exist.

Avoid normal-flow clutter such as package digests, opaque node UUIDs, provenance event lists, or dependency internals. These belong under `.context/` and in diagnostic commands.

## Published IDs are visible

Rules and other addressable elements that children may change must display a stable ID in the official context.

A recommended presentation is:

```markdown
#### `SEC-017` — External network access

Agents must not access external networks from this environment.
```

This keeps the content dominant while making the stable reference easy to discover for removes, overrides, exceptions, tracing, and debugging.

## Generated header

The file should clearly state that it is generated, point to `CONTEXT.src.md` for editing, and link to ContextCanon documentation.
