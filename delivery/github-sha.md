`${{ github.sha }}` gets the full SHA of the commit that triggered the workflow

You can use this to build docker images and make sure each build is uniquely identifiable and that you can trace any deployed image back to the exact code version.
