# Setting Up Repository Secrets in GitHub

GitHub repository secrets provide a secure way to store sensitive data like API keys, passwords, and tokens. This guide explains how to set up and use repository secrets effectively.

## Initial Setup

To add secrets to your repository, navigate to your repository's settings. Under the "Security" section in the sidebar, select "Secrets and variables" then "Actions." This is where you'll manage all your repository's secrets.

## Adding New Secrets

1. Click the "New repository secret" button
2. Enter a name for your secret (e.g., `API_KEY`)
3. Paste your secret value in the value field
4. Click "Add secret" to save

Remember that secret names should be descriptive and follow these conventions:
- Use uppercase letters and underscores
- Avoid spaces or special characters
- Choose names that clearly indicate the secret's purpose

## Using Secrets in GitHub Actions

Once you've added your secrets, you can reference them in your GitHub Actions workflows using this syntax:

```yaml
name: Deploy Application
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        env:
          API_KEY: ${{ secrets.API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          echo "Running deployment with secrets"
          ./deploy.sh
```

## Security Best Practices

When working with repository secrets, follow these security guidelines:

First, limit access to your secrets. Only repository administrators and selected collaborators should have the ability to manage secrets. GitHub automatically enforces this restriction through repository permissions.

Second, rotate your secrets regularly. Establish a process for updating secrets, especially when team members leave or you suspect a secret might have been compromised.

Third, audit your secrets usage. Regularly review which workflows are using your secrets and remove any that are no longer needed. GitHub logs secret usage in workflow runs while keeping the actual values hidden.

## Environment-Specific Secrets

For more complex applications, you might want to use different secrets for different environments. GitHub allows you to create environment-specific secrets:

Navigate to Settings > Environments, create different environments (e.g., staging, production), and add environment-specific secrets. Then reference them in your workflows:

```yaml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        env:
          API_KEY: ${{ secrets.PROD_API_KEY }}
        run: ./deploy.sh
```

## Troubleshooting Common Issues

If you encounter issues with your secrets, verify these common problems:

Secret names must exactly match the references in your workflows. Check for typos and ensure the casing matches. Remember that secrets are case-sensitive.

Secrets are only available to trusted workflows. If you're using third-party actions, make sure they have the necessary permissions to access your secrets.

When debugging workflow issues involving secrets, remember that GitHub automatically redacts secrets from logs for security. You'll need to verify your code logic without relying on direct log output of secret values.

## Maintaining Secret Hygiene

Develop good habits for managing your repository secrets:

Document all secrets in your project documentation, including their purpose and any relevant expiration dates. While you should never document the actual secret values, maintaining a clear record of what secrets are used where helps with project maintenance.

Implement a regular review process for your secrets. Schedule periodic reviews to ensure all secrets are still required and haven't expired. This helps maintain security and prevents the accumulation of unnecessary secrets.

Use secret scanning to prevent accidental commits of sensitive data. GitHub's secret scanning feature will alert you if it detects potential secrets in your code, helping prevent accidental exposure of sensitive information.

By following these guidelines, you can effectively manage sensitive information in your GitHub repositories while maintaining security and enabling smooth CI/CD operations.
