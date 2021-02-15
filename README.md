# Petflap Open Passage Monitor
Monitors the GPIO pins to detect passages

# Setup

```
sudo apt-get install gcc libpq-dev -y
sudo apt-get install python-dev  python-pip -y
sudo apt-get install python3-dev python3-pip python3-venv python3-wheel -y
pip3 install wheel



python3 -m pip install --update -r git+https://github.com/ahue/pfo-passage-monitor.git
```


## Getting Started

To set up your local development environment, please use a fresh virtual environment.

Then run:

    pip install -r requirements.txt -r requirements-dev.txt

You can now run the module from the `src` directory with `python -m pfo_passage_monitor`.

### Testing

We use `pytest` as test framework. To execute the tests, please run

    python setup.py test

To run the tests with coverage information, please use

    python setup.py testcov

and have a look at the `htmlcov` folder, after the tests are done.

### Distribution Package

To build a distribution package (wheel), please use

    python setup.py dist

this will clean up the build folder and then run the `bdist_wheel` command.

### Contributions

Before contributing, please set up the pre-commit hooks to reduce errors and ensure consistency

    pip install -U pre-commit && pre-commit install

## Contact

Andreas Hübner (ahue87@gmail.com)

## License

© Andreas Hübner
