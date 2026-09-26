# GitHub

This reusable Context Node is the concrete **github.com provider** for [Development Workflow](../development-workflow/).

It deliberately keeps the normal GitHub vocabulary intact:

```text
Issue → branch → Pull Request → review → checks → merge
```

The provider adds only the infrastructure binding. It does not duplicate the inherited workflow rules, and it does not compose ContextCanon Foundation transitively.

Projects that use another implementation of the same workflow should select the corresponding provider instead of locally redefining what Issue, Pull Request, review or merge mean.
