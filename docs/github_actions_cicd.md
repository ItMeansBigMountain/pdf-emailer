## CI/CD Pipeline (GitHub Actions)

### Workflow File
- `.github/workflows/deploy.yml`

### How it Works
1. On every push to `main` branch
2. GitHub installs dependencies and zips function app
3. Deploys function app to Azure using `Azure/functions-action@v1`
4. Runs post-deployment integration tests

### Secrets Required
- `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`
- `AZURE_FUNCTION_BASE_URL`
- `AZURE_FUNCTION_KEY`

> Secrets managed in GitHub Repository Settings ➜ Secrets ➜ Actions
