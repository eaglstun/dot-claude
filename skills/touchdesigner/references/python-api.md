# The TouchDesigner Python API

TD embeds **Python 3.11** (on this install) and injects a module called `td` into
every script context, so the names below are available without importing anything.

## Finding operators

```python
me                      # the operator this script lives in
op('noise1')            # sibling, relative to me (or to the DAT's parent)
op('../geo1/torus1')    # relative path, '..' is the parent COMP
op('/project1/base_ui') # absolute path from root
parent()                # the COMP containing me
parent(2)               # two levels up
parent.Ui               # the ancestor COMP whose "parent shortcut" is 'Ui'
op.Globals              # a COMP whose "Global OP Shortcut" is 'Globals'
root                    # the root COMP ('/')
me.parent()             # same as parent()
```

Multiple matches with wildcards:

```python
ops('noise*')                  # list of matching operators
parent().findChildren(type=topTYPE, depth=1)
op('container1').children      # direct children
```

**Shortcuts beat paths.** A path like `op('../../base_audio/null_level')` breaks the
moment you move something. Set a **Global OP Shortcut** (on the COMP's Common
parameter page) and use `op.Audio.op('null_level')`, or a **Parent Shortcut** and
use `parent.Tool`. Inside a component, `iop.name` / `ipar.name` reference the
_internal_ operators and parameters declared on the COMP's Common page — that's
how a `.tox` refers to its own guts without hardcoding a path.

## Parameters

```python
n = op('noise1')

n.par.period                   # the Par object itself
n.par.period.eval()            # current value (evaluates expressions/exports)
n.par.period.val               # the raw stored value
float(n.par.period)            # also evaluates

n.par.period = 4.0             # set a constant value
n.par.period.expr = 'absTime.seconds * 2'   # set an expression
n.par.period.mode = ParMode.EXPRESSION      # CONSTANT / EXPRESSION / EXPORT / BIND
n.par.period.bindExpr = "op('base1').par.Speed"

n.par.reset.pulse()            # fire a pulse parameter
n.par.Mymenu = 'optionname'    # menu params take the menu *name*, not the label
n.par.Mymenu.menuIndex = 2
```

Naming convention — get the capitalization wrong and the attribute simply does not
exist, with a confusing `AttributeError` rather than a helpful one:

- **Built-in parameters are lowercase:** `par.tx`, `par.resolutionw`, `par.file`.
- **Custom parameters you add are Capitalized:** `par.Speed`, `par.Colorr`.
- Multi-value params suffix the component: `par.tx/ty/tz`, `par.colorr/g/b`.
  Access the group at once with `n.parGroup.t` or `n.par.t` tuplet helpers.

To find a real parameter name: hover it in the UI, or

```python
[p.name for p in op('noise1').pars()]
op('noise1').pars('period*')
```

## Custom parameters

Right-click a COMP → **Customize Component** to add parameters via the UI, or
build them in Python:

```python
c = op('base1')
p = c.appendFloat('Speed', label='Speed', size=1)
p[0].normMin, p[0].normMax, p[0].default = 0, 10, 1
c.appendToggle('Enabled')
c.appendMenu('Mode', label='Mode')
c.par.Mode.menuNames  = ['a', 'b']
c.par.Mode.menuLabels = ['Alpha', 'Beta']
c.appendPulse('Reset')
c.appendStr('Title')
c.appendFile('Source')
```

`appendXXX` returns a **ParGroup**; index it (`p[0]`) to touch an individual Par.
Custom parameters live on a custom **page**:

```python
page = c.appendCustomPage('Controls')
page.appendFloat('Speed')
```

This is how you turn a Base COMP into a reusable module with a real interface.

## Operator content

```python
# TOP
t = op('moviefilein1')
t.width, t.height, t.aspect
t.save('/tmp/frame.png')
t.numpyArray()             # CPU readback — slow, don't do it per-frame

# CHOP
c = op('noise1')
c['chan1'][0]              # channel by name, sample by index
c[0][0]                    # channel by index
c.numChans, c.numSamples, c.rate
c.chans('*x')              # matching channels
c.chan('tx').vals          # all samples
float(op('null1')['tx'])   # idiomatic "read one control value"

# DAT
d = op('table1')
d[0, 0]                    # cell by row, col
d['rowname', 'colname']    # cell by header name
d.numRows, d.numCols
d.text                     # whole thing as text
d.appendRow(['a', 'b'])
d.clear(keepFirstRow=True)
d.cell(0, 0).val = 'x'

# SOP
s = op('torus1')
s.points, s.prims
s.points[0].P              # position
s.numPoints
```

## Storage — persistent per-operator state

```python
n.store('counter', 0)
n.fetch('counter', 0)              # second arg is the default
n.fetch('counter', 0, search=True) # walk up the parent chain looking for it
n.unstore('counter')
n.storage                          # the whole dict
```

Storage persists in the saved `.toe`. Use it for state that must survive a save;
use a Python class attribute on an extension for state that shouldn't.

## Extensions — giving a COMP a Python class

Put a class in a Text DAT inside the COMP, then on the COMP's **Extensions**
parameter page set `Extension 1` to `op('ExtDAT').module.ClassName(me)` and
enable **Promote Extension**.

```python
# Text DAT named 'MyToolExt'
class MyTool:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self.Count = 0                 # capitalized = public, shows in the UI

    def Reset(self):                   # capitalized methods are the public API
        self.Count = 0
        self.ownerComp.par.Speed = 1

    def _helper(self):                 # lowercase/underscore = internal
        pass
```

Call it from anywhere:

```python
op('base1').Reset()          # works when Promote Extension is on
me.ext.MyTool.Reset()        # explicit, works from inside the COMP
parent().Count               # promoted attribute
```

Convention: **Capitalized members are the public interface**, lowercase are
private. Promotion only exposes the capitalized ones. After editing the class,
right-click the COMP → **Re-Init Extensions** (or `op('base1').initializeExtensions()`)
— Python does not hot-reload the class for you.

## Importing code from DATs

```python
mod('myModuleDAT').my_function()      # import a Text DAT as a module
mod.myModuleDAT.my_function()         # attribute form, searches from me
import myModuleDAT                    # works if the DAT is on the module search path
```

`mod()` re-imports on change, which is what you want during development.

## Time

```python
absTime.frame        # frames since the app started — always increasing
absTime.seconds
absTime.stepSeconds  # duration of the last frame

me.time.frame        # the local Time COMP's frame — loops with the timeline
me.time.seconds
me.time.rate         # fps of that timeline
project.cookRate     # target fps
```

For anything that should keep running regardless of timeline state, use
`absTime`. For anything that should follow the transport (loops, playback), use
`me.time`.

## Expressions in parameters

The same API works inline in a parameter set to Expression mode:

```
absTime.seconds * 2
op('null_audio')['level'] * 5
parent().par.Speed
op('table1')[1, 'value']
me.digits                     # trailing digits of this op's name — great with Replicators
me.fetch('offset', 0)
```

`me.digits` and `me.parent().digits` are the standard trick for making replicated
or copy-pasted nodes self-index without editing each one.

## Errors and debugging

- `print()` goes to the **Textport** (`Dialogs → Textport and DATs`).
- `debug()` prints with the source operator and line prefixed — better than `print`.
- Script errors show as a red badge on the operator; hover or open the Textport.
- `ui.status = 'message'` writes to the status bar.
- `op('x').errors()`, `op('x').warnings()` return diagnostic text programmatically.

## Deferred execution

Never modify network structure from inside a cook (a Script CHOP/TOP callback,
for instance) — delete or create nodes on the next frame instead:

```python
run("op('base1').destroy()", delayFrames=1)
run("args[0].par.Speed = 2", op('base1'), delayFrames=1)
run("print('later')", delayMilliSeconds=500)
```

`run()` returns a `Run` object you can `.kill()`. Structural changes mid-cook are
the most common cause of a hard crash in TouchDesigner.
