## Structure

This project is a monorepo. The backend is contained in the `backend/` directory. The frontend is contained in the `frontend/` directory.

## Running tests
You can use `test.sh` to run tests. For backend tests, use the following command: `./test.sh backend`. You can pass arguments as well. For example: `./test.sh backend -- -k 'test_edit_nonexistent_account_notes'`

## Python preferences
Please place module imports at the top of modules when possible. This should be the case for the vast majority of module imports.
