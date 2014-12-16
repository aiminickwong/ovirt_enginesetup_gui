"""Dialog plugin."""


from otopi import util


from . import human
from . import misc

@util.export
def createPlugins(context):
    human.Plugin(context=context)
    misc.Plugin(context=context)



#
