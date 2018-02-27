PYTHON=python2
PYTEST=pytest-2.7
VERSION:=$(shell $(PYTHON) setup.py --version)
DOC_HOST='qam.suse.de'
LOCAL_DOC_DIRECTORY='Documentation/_build/html'
REMOTE_DOC_DIRECTORY='/srv/www/qam.suse.de/projects/oscqam/$(VERSION)'

.PHONY: doc, deploy-doc

all:

	$(PYTHON) setup.py build

check:

	$(PYTEST) tests

doc:

	rm -f Documentation/modules.rst
	rm -f Documentation/oscqam.rst
	sphinx-apidoc oscqam -o Documentation
	pushd Documentation && make html && popd

deploy-doc: doc

	ssh root@$(DOC_HOST) rm -rf $(REMOTE_DOC_DIRECTORY)
	scp -r $(LOCAL_DOC_DIRECTORY) root@$(DOC_HOST):$(REMOTE_DOC_DIRECTORY)
	ssh root@$(DOC_HOST) rm -f $(subst $(VERSION),latest,$(REMOTE_DOC_DIRECTORY))
	ssh root@$(DOC_HOST) ln -s $(REMOTE_DOC_DIRECTORY) $(subst $(VERSION),latest,$(REMOTE_DOC_DIRECTORY))
