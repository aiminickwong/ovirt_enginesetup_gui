import sys
if not "/usr/local/lib/python2.7/site-packages/" in sys.path:
    sys.path.append("/usr/local/lib/python2.7/site-packages/")


from TUI_startup.app import app, ui
import TUI_startup.core  as setup
import sys

def quit(instance):
    def ui_quit(dialog, changes):
        instance.ui.quit()
    txt = "Are you sure you want to quit?"
    dialog = ui.ConfirmationDialog("dialog.exit", "Exit", txt,
                                   [ui.Button("dialog.exit.yes", "Yes"),
                                    ui.CloseButton("dialog.exit.close", "No")]
                                   )

    dialog.buttons[0].on_activate.clear()
    dialog.buttons[0].on_activate.connect(ui.CloseAction())
    dialog.buttons[0].on_activate.connect(ui_quit)
    instance.show(dialog)


def run(self):
    args, _ = app.parse_cmdline()
    print "ARGS IS %s" %args
    print "_ %s" %_
    #import pdb
    #pdb.set_trace()
    #log.configure_logging(args.debug)
    instance = app.Application(setup, args, quit=quit)
    #instance.__dict__['executelist']=self.executelist
    instance.__dict__['context']=self
    instance.run()

