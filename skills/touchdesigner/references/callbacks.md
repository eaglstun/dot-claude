# Callbacks — how Python actually gets run

A Text DAT full of Python does nothing on its own. Code runs when one of these
fires it. Each callback DAT ships with a commented template when you create it —
create the node and read its default contents; the signatures below are the shape,
but the generated template is authoritative for your build.

## Execute DAT — frame and application lifecycle

The general-purpose one. Enable the hooks you want on its parameters.

```python
def onStart():          pass   # project opened
def onCreate():         pass   # this DAT created
def onExit():           pass   # project closing
def onFrameStart(frame):pass   # every frame, before cooking
def onFrameEnd(frame):  pass   # every frame, after cooking
def onPlayStateChange(state): pass
def onProjectPreSave(): pass
def onProjectPostSave():pass
```

`onFrameStart` runs 60 times a second. Anything expensive in there is a frame-rate
problem by construction. Prefer an event-driven callback below.

## CHOP Execute DAT — react to a channel changing

Point its **CHOP** parameter at a Null CHOP and enable the conditions you need.

```python
def onOffToOn(channel, sampleIndex, val, prev):  pass  # rising edge — buttons, triggers
def onOnToOff(channel, sampleIndex, val, prev):  pass
def whileOn(channel, sampleIndex, val, prev):    pass
def whileOff(channel, sampleIndex, val, prev):   pass
def onValueChange(channel, sampleIndex, val, prev): pass
```

`channel` is a Channel object — `channel.name` and `channel.owner` are what you
usually want. This is the standard way to turn a MIDI note, an OSC message, or a
button into a Python action.

**Watch out:** `onValueChange` on a continuously-changing channel (an LFO, audio
level) fires every frame. Use `onOffToOn` with a Trigger/Logic CHOP upstream to
make the event discrete instead of filtering in Python.

## Parameter Execute DAT — react to a parameter changing

```python
def onValueChange(par, prev):   pass
def onPulse(par):               pass
def onExpressionChange(par, val, prev): pass
```

Point it at an OP and a parameter name (wildcards allowed, e.g. `Speed*`). This is
how a custom parameter on your Base COMP triggers behavior — the standard pattern
being `onValueChange` → call a method on the COMP's extension.

## DAT Execute DAT — react to table/text contents changing

```python
def onTableChange(dat):                 pass
def onRowChange(dat, rows):             pass
def onColChange(dat, cols):             pass
def onCellChange(dat, cells, prev):     pass
def onSizeChange(dat):                  pass
```

## Panel Execute DAT — react to UI interaction

```python
def onOffToOn(panelValue):   pass
def onValueChange(panelValue): pass
```

Point it at a Panel COMP and a panel value (`select`, `state`, `u`, `v`, `rollover`,
`inside`…). For buttons, `select` on a Button COMP is the click.

Panel COMPs also have their own **callback DAT** parameter in newer builds —
either route works; pick one convention per project rather than mixing.

## Script operators — generate content in Python

- **Script CHOP** — `onCook(scriptOp)`; build channels with
  `scriptOp.clear()`, `scriptOp.appendChan('x')`, `scriptOp.numSamples = n`.
- **Script SOP** — build points/prims in `onCook`.
- **Script DAT / Script TOP** — same pattern.

`onCook` runs inside the cook. Do not create, destroy, or reparent operators from
there — schedule it with `run(..., delayFrames=1)` (see `python-api.md`).

## Timer CHOP

The right tool for sequencing, cues, and anything with a duration. Its callback DAT
gets:

```python
def onInitialize(timerOp, callCount):  return
def onReady(timerOp):                  return
def onStart(timerOp):                  return
def onTimerPulse(timerOp, segment):    return
def onSegmentEnter(timerOp, segment, interrupt): return
def onSegmentExit(timerOp, segment, interrupt):  return
def onCycle(timerOp, segment):         return
def onDone(timerOp, segment, interrupt): return
```

Drive it with `op('timer1').par.start.pulse()`, and read progress from its
`timer_fraction` / `running` channels. Reach for this before writing a
frame-counting loop in an Execute DAT.

## Replicator COMP

Creates one clone of a master COMP per row of a template table — the way to build
a dynamic UI list or N identical processing chains.

```python
def onReplicate(comp, allOps, newOps, template, master):
    for o, row in zip(newOps, template.rows()[1:]):
        o.par.Label = row[0].val
```

Inside each replicant, `me.digits` gives the index, so most per-clone
configuration can be an expression rather than Python.

## OSC / TCP / WebSocket / MIDI In DATs

Network DATs have a callback DAT with a `onReceive`-family function
(`onReceiveOSC`, `onReceiveText`, `onReceiveMessage` — the exact name depends on
the DAT, read its generated template). Message handling belongs here; parsing and
routing belongs in an extension method that the callback calls, so the logic stays
testable and doesn't live in a network node.

## Choosing between callbacks and expressions

If a value just needs to _follow_ another value, use a **parameter expression** or
a **CHOP export** — no Python runs, no callback fires, and the dependency is
visible in the network. Reserve callbacks for genuine events (a button press, a
message arriving, a segment ending) and for things expressions can't do (creating
nodes, writing files, calling out to a network).

A network full of Execute DATs polling for changes is a network that will be slow
and hard to debug. A network of expressions and edge-triggered callbacks is
neither.
