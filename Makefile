MSGLANGS = $(wildcard pictures/locale/*/LC_MESSAGES/*.po)
MSGOBJS = $(MSGLANGS:.po=.mo)

.PHONY: translations gettext gettext-clean

gettext: $(MSGOBJS)

gettext-clean:
	-rm $(MSGOBJS)

%.mo: %.po
	msgfmt --check-format --check-domain --statistics -o $@ $*.po
