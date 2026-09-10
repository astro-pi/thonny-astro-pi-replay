##################
# OS Dependencies
##################
CUT:=cut
FIND:=find
GIT:=git
GREP:=grep
PYTHON3:=/usr/bin/python3
RM:=rm
SORT:=sort
TEST:=test
TR:=tr
XARGS:=xargs

#####################
# Python dependencies
#####################
BUILD:=build
TOUCH:=touch
TWINE:=twine
PRE_COMMIT:=pre-commit
PYTEST:=pytest
VENV:=venv
VENV_PIP:=pip
VENV_PYTHON:=$(VENV)/bin/python3

###################
# Configuration
###################
CURRENT_BRANCH:=$(shell $(GIT) rev-parse --abbrev-ref HEAD)
DIST_DIR:=dist
GREP_REGEX_ENGINE:=$(shell $(GREP) "-P" Makefile &> /dev/null && echo "P" || echo "E")
MAIN_BRANCH:=main
PYFLAGS=
PYPROJECT:=pyproject.toml
ifdef PYTEST_DEBUG
PYTEST_FLAGS:=-s --log-cli-level=DEBUG
else
PYTEST_FLAGS:=-s
endif
REQUIREMENTS_TXT:=requirements.txt
REQUIREMENTS_DEV_TXT:=requirements-dev.txt
SRC_DIR:=thonnycontrib
# Dynamic configuration to ensure pyproject.toml is the source of truth
NAME:=$(shell cat $(PYPROJECT) | \
     $(TR) '\n' '\a' | \
     $(GREP) -o$(GREP_REGEX_ENGINE) 'name = "[a-z_-]+"' | \
     $(CUT) -d" " -f3 | \
     $(TR) -d '""')
VERSION:=$(shell cat $(PYPROJECT) | \
     $(TR) '\n' '\a' | \
     $(GREP) -o$(GREP_REGEX_ENGINE) 'version = "[0-9\.]+"' | \
     $(CUT) -d" " -f3 | \
     $(TR) -d '""')
VERSION_MAJOR:=$(shell $(PYTHON3) -c 'print("$(VERSION)".split(".")[0])')
VERSION_MINOR:=$(shell $(PYTHON3) -c 'print("$(VERSION)".split(".")[1])')
VERSION_PATCH:=$(shell $(PYTHON3) -c 'print("$(VERSION)".split(".")[2])')
VENV_NAME:=venv


all:
	@echo "(GNU)make targets:"
	@echo ""
	@echo "build_python      - Build the python package"
	@echo "clean             - Clean (delete files) from the environment"
	@echo "                    and start afresh."
	@echo "diagnostics       - Run diagnostics in case of any problems with"
	@echo "                    this Makefile."
	@echo "publish_git_tags  - Publish and overwrite git tags to the remote."
	@echo "publish_prod_pypi - Build and publish a release to prod PyPi."
	@echo "publish_test_pypi - Build and publish a release to test PyPi."
	@echo "publish_test_pypi - Build and publish a release to test PyPi."
	@echo "setup_developer   - Install pre-commit hooks and venv to"
	@echo "                    the developer environment."

	@echo "version           - Print the package version"
	@echo ""


assert_env_var_set_%:
	@if [ "${${*}}" = "" ]; then \
	  echo "Environment variable $* not set"; \
          exit 1; \
    	fi

assert_installed_%:
	@command -v $* || echo "$* not installed"; exit 1

assert_min_python_version_detected:
	@if [ -z $(shell echo '$(PYTHON_VERSION_EXPR)' | \
		$(SED) -E 's/(>=?3\.([0-9]\.){1,2})/\1/g') ]; then \
	  echo "Cannot find minimum version"; \
	  exit 1; \
	fi

assert_on_git_branch_head_or_%:
	@if [ $(CURRENT_BRANCH) != "HEAD" ] && [ "$*" != "$(CURRENT_BRANCH)" ]; then \
	  echo "Expected branch to be $* but was '$(CURRENT_BRANCH)'"; \
	  exit 1; \
	fi

build_python: $(DIST_DIR)

diagnostics:
	@echo "Detected project name: $(NAME)"
	@echo "Detected version is: $(VERSION)"
	@echo "Detected major version is: $(VERSION_MAJOR)"
	@echo "Detected minor version is: $(VERSION_MINOR)"
	@echo "Detected patch version is: $(VERSION_PATCH)"

$(DIST_DIR): 	$(VENV_NAME)
	. $(VENV_NAME)/bin/activate; $(VENV_PYTHON) -m $(BUILD)

pre_commit_install: $(VENV_NAME)
	@echo "Installing pre-commit hooks"
	. $(VENV_NAME)/bin/activate; \
	$(PRE_COMMIT) install --install-hooks

publish_git_tags: assert_on_git_branch_head_or_main
	@echo "Creating semver tags for $(VERSION)"
	$(GIT) tag -f v$(VERSION_MAJOR)
	$(GIT) tag -f v$(VERSION_MAJOR).$(VERSION_MINOR)
	$(GIT) tag -f v$(VERSION_MAJOR).$(VERSION_MINOR).$(VERSION_PATCH)
	@echo "Overwriting the remote tags"
	$(GIT) push -f origin --tags

publish_test_pypi: assert_on_git_branch_head_or_main assert_env_var_set_TWINE_USERNAME \
	assert_env_var_set_TWINE_PASSWORD $(DIST_DIR)
	. $(VENV_NAME)/bin/activate; \
	$(TWINE) check $(DIST_DIR)/* ; \
	$(TWINE) upload -r testpypi $(DIST_DIR)/*

publish_prod_pypi: assert_on_git_branch_head_or_main assert_env_var_set_TWINE_USERNAME \
	assert_env_var_set_TWINE_PASSWORD $(DIST_DIR)
	. $(VENV_NAME)/bin/activate; \
	$(TWINE) check $(DIST_DIR)/* ; \
	$(TWINE) upload $(DIST_DIR)/*

setup_developer: $(VENV_NAME) pre_commit_install
	@echo "Activate venv with $(VENV_NAME)/bin/activate"
	@echo "or use direnv"

test: $(VENV_NAME)
	. $(VENV_NAME)/bin/activate; $(PYTEST) $(PYTEST_FLAGS)

$(VENV_NAME)/touchfile: $(REQUIREMENTS_TXT) $(REQUIREMENTS_DEV_TXT)
	$(TEST) -d $(VENV_NAME) || $(PYTHON3) $(PYFLAGS) -m $(VENV) --upgrade-deps $(VENV_NAME) && \
	. $(VENV_NAME)/bin/activate ; \
	$(VENV_PIP) install --upgrade -r $(REQUIREMENTS_TXT) ; \
	$(VENV_PIP) install --upgrade -r $(REQUIREMENTS_DEV_TXT) ; \
	$(TOUCH) $(VENV_NAME)/touchfile

$(VENV_NAME): $(VENV_NAME)/touchfile

version:
	@echo $(VERSION)

.PHONY:	all assert_env_var_set_% assert_installed_% assert_min_python_version_detected assert_on_git_branch_head_or_% build_python diagnostics pre_commit_install clean test publish_git_tags publish_test_pypi publish_prod_pypi setup_developer version

clean:
	@$(RM) -rf $(DIST_DIR) $(VENV_NAME)
	@$(FIND) . -iname "__pycache__" | $(SORT) -r | $(XARGS) -I{} rm -rf {}
	@$(FIND) . -iname "*.pyc" | $(SORT) -r | $(XARGS) -I{} rm -f {}
	@$(FIND) . -iname "*.egg-info" | $(SORT) -r | $(XARGS) -I{} rm -rf {}

