# State machine crawler

A library for following automata based programming model when writing black box tests for systems that have a state.

Check [documentation](http://state-machine-crawler.readthedocs.org/en/latest/) for more details.

# The process

## Code style

Run [pep8](https://pypi.python.org/pypi/pep8) and [pyflakes](https://pypi.python.org/pypi/pyflakes) in **src** directory

## Version policy and changelog format

```
MAJOR.MINOR RELEASE-TIMESTAMP=YYYY-MM-DD

    * change description
    * MAJOR: another change
```

Mark backward incompatible changes as **MAJOR**. Other changes do no need to be marked anyhow.

Example

```
12.11 2014-01-12

    * refactored the modules
    * added a new class
    * removed deprecated function
```

Notes:

- There is no need to modify changelog when documentation or travis related files are updated. Only changes of the
  source code are important.

## Release steps

1. Pull **master** branch
2. Make sure that all checks and tests pass
3. Increment the version in **CHANGES** file according to the types of changes made since the latest release. Add
   timestamp to indicate when the version was released.
4. Add bullet points based on git log entries
5. Commit the changes
6. Execute "git tag VERSION -m VERSION"
7. Push **master** branch to upstream
8. Push version tag to upstream

## Pull requests

1. Make sure that all commits have descriptive messages and are up to the point
2. pep8 and pyflakes checks are supposed to pass
3. All tests are supposed to pass
4. If it is a new feature - make sure that new tests are created and they pass
5. Create a pull request against the **master** branch

## Commits

Commits should be easily revertible - each commit is a logical change that DOES NOT break anything
