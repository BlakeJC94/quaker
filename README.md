# quaker
Lightweight python API to USGS earthquake dataset

*This is a work in progress, documentation will be supplied on the first release*

[API Docs are located here](https://earthquake.usgs.gov/fdsnws/event/1/)

## Installation
Clone the repo to your system and install

```bash
$ git clone https://github.com/BlakeJC94/quaker.git
$ cd quaker
$ pip install .
```

## Quickstart
***TODO***

## Ideas to implement

- [X] Links to robust documentation by USGS
- [ ] Stable Python API for querying the USGS earthquake API
    - [ ] Add safety for KeyboardInterrupt error
    - [ ] Finalise object model for python API
    - [ ] Add io helpers and functions
    - [ ] Documentation for python api
        - [ ] Docstrings
        - [ ] Type hints
        - [ ] README quickstart and install instructions
    - [ ] Proper setup.py and requierments.txt
- [ ] CLI bindings
- [ ] Dash app to visualise clustered query results
- [ ] Publish to pypi?

## Contributing

This is a small personal project, but pull requests are most welcome!

* Code is styled using `[black](https://github.com/psf/black)`
* Requirements are managed using `pip-tools` (run `pip install pip-tools` if needed)
    * Add dependencies by adding packages to `setup.py` and running `pip-compile`
* [Semantic versioning](https://semver.org) is used in this repo
    * Major version: rare, substantial changes that break backward compatibility
    * Minor version: most changes - new features, models or improvements
    * Patch version: small bug fixes and documentation-only changes
