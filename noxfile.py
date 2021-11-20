from nox_poetry import session  # type: ignore


@session(python=["3.9"])
def tests(session):  # noqa: D103,WPS442
    session.run_always("poetry", "install", external=True)
    session.install(".")
    session.run("pytest", "tests/unit", external=True)
