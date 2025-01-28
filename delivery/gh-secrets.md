### GitHub Secrets `${{ secrets.ECR_REPOSITORY }}`

- GitHub repositories have a "Secrets" section in their settings where you can store sensitive data
- These secrets are encrypted and only exposed during workflow runs
- You can access them in workflows using the syntax ${{ secrets.SECRET_NAME }}
- Common uses include API keys, passwords, tokens, etc.
- Once saved, you can't view the secret value again - you can only update it
- They can be set at repository, environment, or organization level
