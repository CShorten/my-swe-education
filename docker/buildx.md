### Docker Buildx

An extension of the regular docker build command with extra features
Key benefits:

- Multi-platform builds (e.g., build for AMD64 and ARM64 from same machine)
- Better caching capabilities
- Concurrent build steps
- More efficient layer management

In your workflow, it's used with --platform linux/amd64 to ensure the image is built specifically for AMD64 architecture, which is important for compatibility with your deployment environment
