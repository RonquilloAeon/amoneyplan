import nox

nox.options.sessions = ["test"]


@nox.session(python="3.10", reuse_venv=True)
def test(session):
    session.install("-r", "test-requirements.txt")
    session.run("pytest", *session.posargs)
