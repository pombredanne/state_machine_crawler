# State machine crawler

A library for following automata based programming model.

Check [documentation](http://state-machine-crawler.readthedocs.org/en/latest/) for more details.

# The process

## Code style

Run [pep8](https://pypi.python.org/pypi/pep8) and [pyflakes](https://pypi.python.org/pypi/pyflakes) in **src** directory

## Version policy

[Semantic version](http://semver.org/)

## Changelog format

```
VERSION RELEASE-TIMESTAMP=YYYY-MM-DD

    [Author Name <author@email>]
        * CHANGE_TYPE=MAJOR|MINOR|PATCH: change description
```

Example

```
12.11.3 2014-01-12

    [John Smith <john.smith@example.com>]
        * PATCH: refactored the modules
        * MINOR: added a new class
        * MAJOR: removed deprecated function
```

Notes:

- There is no need to modify changelog when documentation or travis related files are updated. Only changes of the
  source code are important.

## Release steps

1. Switch to **master**
2. Merge **dev** into **master**
3. Make sure that all checks and tests pass
4. Increment the version in **CHANGES** file according to the types of changes made since the latest release. Add
   timestamp to indicate that the version was released.
5. Commit the changes
6. Execute "git tag VERSION -m VERSION"
7. Switch to **dev**
8. Merge **master** into **dev**
9. Add a new changelog entry that is just slightly higher than the released one (without release timestamp) with a
    FILLME entry
10. Commit the changes
11. Push **dev** & **master** branches to upstream
12. Push tags to upstream

## Pull requests

Always create your own feature branches from the **dev** branch. Not from **master** one.

1. Make sure that all commits have descriptive messages and are up to the point
2. pep8 and pyflakes checks are supposed to pass
3. All tests are supposed to pass
4. If it is a new feature - make sure that new tests are created and they pass
5. Add a new set of bullet points to the latest changelog entry according to the specified format
6. Create a pull request against the **dev** branch

## Commits

1. Make sure that all commits that touched the source have MAJOR, MINOR or PATCH prefix to simplify changelog
   management. Changes that did not involve source code modification should not be annotated with any prefix.
2. Commits should be easily revertible - each commit is a logical change that DOES NOT break anything
