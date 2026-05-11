# Huma

Huma is a Go REST API framework built on top of standard Go HTTP routers (like chi, which this projec tuses). The name "Huma" comes from Persian mythology - a bird said to bring fortune to anyone it touches.

Declaratively register API operations with typed inputs and outputs, automatic request validation, and OpenAPI spec generation.

### `.NewGroup`

`huma.NewGroup` creates a route prefix group - it returns a `huma.API` scoped to a base path. All routes registered on that group automatically inherit the prefix.
