AWS OIDC vs Access Keys


Traditional method (Access Keys):

Store AWS access key and secret key in GitHub secrets
Like having a permanent username/password
If exposed, they can be misused until manually revoked


OIDC method:

GitHub and AWS establish a trust relationship
GitHub generates temporary tokens for each workflow run
AWS validates these tokens and provides temporary credentials
More secure because:

No long-lived credentials to store
Credentials automatically expire after the workflow
Easier to audit and manage permissions
