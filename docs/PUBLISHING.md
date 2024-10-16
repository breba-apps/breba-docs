# Publishing Workflow

## Current - Manual Workflow Dispatch

Currently, the release is automated after the "Manual Release Workflow" is dispatched from Github Actions.
The key parts of it are:
1. Bumping the version automatically using the user input.
   1. The semantic version that comes from user input is used to run `poetry version [user input]`
2. Creating GitHub Release which will also create a git tag from the latest revision
3. Publishing to PyPi
4. Attest the build provenance (Optional)
5. Upload build artifact to GitHub Actions (Optional)

```mermaid
flowchart TB
    User(["User"])
    Workflow["Manual Release Workflow"]
    subgraph UpdateVersion["Updating Version in pyproject.toml"]
    direction LR
        Checkout["Checkout main"]
        Version["`Bump version 
                **poetry version major|minor|path** `"]
        Commit["Commit back to main"]
    end

    subgraph Releasing["Creating Github Release"]
        Release["Tag Repo and publish release"]
    end

    subgraph Publishing
    direction LR
        Build["Build Package"] 
        Build --> Publish["Publish to PyPi"]
        Build --> Attest
        Build --> UploadArtifact["Upload Artifact to Workflow"]
    end

    User -- Input: poetry semantic version --> Workflow
    Workflow --> UpdateVersion
    Checkout --> Version
    Version --> Commit
    UpdateVersion --> Releasing
    UpdateVersion --> Publishing
```


## Alternative: Manual Workflow Dispatch With Pull Request
This may be a better approach because it doesn't involve making unreviewed commits to the repo.
```mermaid
flowchart TB
    User(["User"])
    Workflow["Manual Release Workflow"]
    subgraph UpdateVersion["Updating Version in pyproject.toml"]
    direction LR
        Checkout["Checkout main"]
        Version["`Bump version 
                **poetry version major|minor|path** `"]
        Commit["Create PR"]
    end

    MergePr["Manually Merge PR"]

    subgraph Releasing["Creating Github Release"]
        Release["Tag Repo and publish release"]
    end

    subgraph Publishing
    direction LR
        Build["Build Package"] 
        Build --> Publish["Publish to PyPi"]
        Build --> Attest
        Build --> UploadArtifact["Upload Artifact to Workflow"]
    end

    User -- Input: poetry semantic version --> Workflow
    Workflow --> UpdateVersion
    Checkout --> Version
    Version --> Commit
    UpdateVersion --> MergePr
    MergePr --> Releasing
    MergePr --> Publishing
```

