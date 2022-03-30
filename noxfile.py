import nox

nox.options.sessions = ["format", "test"]


@nox.session(python="3.10", reuse_venv=True)
def dev(session):
    """Development virtual environment. Handy for setting interpreter in IDE."""
    session.install("-r", "test-requirements.txt")


@nox.session(python="3.10", reuse_venv=True)
def format(session):
    session.install("black")
    session.run("black", "amoneyplan", "tests", *session.posargs)


@nox.session(python="3.10", reuse_venv=True)
def test(session):
    session.install("-r", "test-requirements.txt")
    session.run("pytest", *session.posargs)
