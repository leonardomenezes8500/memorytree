PREFIX ?= $(HOME)/.local
BINDIR := $(PREFIX)/bin

.PHONY: install uninstall test

install:
	install -Dm755 bin/memorytree $(BINDIR)/memorytree

uninstall:
	rm -f $(BINDIR)/memorytree

test:
	python3 test_memorytree.py
