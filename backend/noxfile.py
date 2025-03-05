import nox
from nox.sessions import Session

nox.options.sessions = ["test"]
locations = ["src"]


@nox.session(python="3.13", reuse_venv=True)
def lint(session: Session) -> None:
    """Run the linter."""
    args = session.posargs or ["--fix"] + locations
    session.install("ruff")
    session.run("ruff", "check", *args)


@nox.session(python="3.13", reuse_venv=True)
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or locations
    session.install("mypy")
    session.run_always("poetry", "install", "--no-root", external=True)
    session.run("mypy", *args)


@nox.session(python="3.13", reuse_venv=True)
def test(session: Session) -> None:
    """Run the test suite."""
    args = session.posargs or ["--cov=amoneyplan", "-v"] + locations
    session.run_always("poetry", "install", "--no-root", external=True)
    session.run("pytest", *args)
