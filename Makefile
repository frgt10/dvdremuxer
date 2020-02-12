ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
PYTHON ?= /usr/bin/env python

localsymlink:
	ln -sf ${ROOT_DIR}/dvd_remuxer/__main__.py ~/.bin/dvd-remuxer

install: dvd-remuxer
	install -d $(DESTDIR)$(BINDIR)
	install -m 755 dvd-remuxer $(DESTDIR)$(BINDIR)

dvd-remuxer: dvd_remuxer/*.py
	mkdir -p zip
	for d in dvd_remuxer ; do \
	  mkdir -p zip/$$d ;\
	  cp -pPR $$d/*.py zip/$$d/ ;\
	done
	touch -t 200001010101 zip/dvd_remuxer/*.py
	mv zip/dvd_remuxer/__main__.py zip/
	cd zip ; zip -q ../dvd-remuxer dvd_remuxer/*.py __main__.py
	rm -rf zip
	echo '#!$(PYTHON)' > dvd-remuxer
	cat dvd-remuxer.zip >> dvd-remuxer
	rm dvd-remuxer.zip
	chmod a+x dvd-remuxer
