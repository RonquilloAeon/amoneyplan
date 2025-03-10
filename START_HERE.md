## Dev Environment Setup

### Backend

- Run `pre-commit install`
- Run `./dev.sh init`
- Run `./dev.sh up`

#### Cleanup

To delete the kind cluster, run `kind delete cluster --name amoneyplan`

### Frontend

#### Using dev script
Use `./dev.sh frontend [args]`. All args after __frontend__ are passed to pnpm.

#### Set up
- Run `./dev.sh frontend install`
- Run `./dev.sh frontend dev`
