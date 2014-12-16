"""Dialog plugin."""


from otopi import util


from . import TUI_human

@util.export
def createPlugins(context):
    
    TUI_human.Plugin(context=context)



#
