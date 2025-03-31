## Dev Environment Setup

### Backend

- Run `pre-commit install`
- Run `./dev.sh init`
- Run `./dev.sh up`

#### Cleanup

To delete the kind cluster, run `kind delete cluster --name amoneyplan`

#### Profiling tests
Run `./test.sh backend -- --profile --durations=10 --durations-min=0.1` to find slow tests.

### Frontend

#### Using dev script
Use `./dev.sh frontend [args]`. All args after __frontend__ are passed to pnpm.

#### Set up
- Run `./dev.sh frontend install`
- Run `./dev.sh frontend dev`
