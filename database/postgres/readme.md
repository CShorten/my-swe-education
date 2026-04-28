# Postgres Nuggets

`@>`: containment operator.

```sql
'{"name": "Alice", "role": "admin", "active": true}'::jsonb @> '{"role": "admin"}'::jsonb
-- true

'{"tags": ["postgres", "json", "database"]}'::jsonb @> '{"tags": ["json"]}'::jsonb
-- true
```
