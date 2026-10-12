"""Apply wordpop to the Text+ template named "Lirik" and open the Fusion page.

Run from Workspace > Scripts > Utility > test_wordpop. No transcription.
Uses the Media Pool Text+ named "Lirik": reuses an existing timeline clip named
Lirik, otherwise appends the template at the end of track 1. Reads the caption
text from the innermost tool (CLS > Follower > Text+) before and after the run
so a blank clip can be traced to the right link in the chain.
Import of WhisperSubtitles falls back to the Utility folder because Resolve's
script runner does not always define __file__.
"""
import importlib.util
import os
import time
import traceback

CANDIDATES = [
    os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    os.path.expanduser("~/Library/Application Support/Blackmagic Design/"
                       "DaVinci Resolve/Fusion/Scripts/Utility"),
    "/Volumes/VGEN10S1T/DaVInci Plugins/WhisperSubtitles",
]
TEMPLATE_NAME = "Lirik"


def log(text):
    path = os.path.expanduser("~/Movies/DaVinci Subtitles/last_run.log")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as h:
            h.write(text + "\n")
    except Exception:
        pass


def load_ws():
    for folder in CANDIDATES:
        if not folder:
            continue
        path = os.path.join(folder, "WhisperSubtitles.py")
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("ws", path)
            ws = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ws)
            return ws
    raise RuntimeError("WhisperSubtitles.py not found in %r" % CANDIDATES)


def get_tool_and_comp(item, ws):
    """(tool, comp) with retries - the comp is not built instantly."""
    for _ in range(6):
        try:
            comp = item.GetFusionCompByIndex(1)
            tool = ws._first_tool(comp, "TextPlus")
            if tool is not None:
                return tool, comp
        except Exception:
            pass
        time.sleep(0.4)
    return None, None


def dump_text_chain(tag, comp, tool, ws):
    """Log where the caption text currently lives (innermost first).

    Only inputs that are NOT connected are read: GetInput on a chained input
    (tool.StyledText once a Follower is attached) evaluates the whole chain on
    the UI thread and deadlocks Resolve.
    """
    follower = ws._find_modifier_by_type(tool, "StyledTextFollower")
    cls = None
    if follower is not None:
        cls = ws._find_modifier_by_type(follower, "StyledTextCLS")
    log("%s chain: tool=%r follower=%r cls=%r" % (tag, tool, follower, cls))
    reads = (("cls.Text", cls, "Text", cls is not None),
             ("follower.Text", follower, "Text", cls is None),
             ("tool.StyledText", tool, "StyledText", follower is None))
    for label, src, prop, do_read in reads:
        if src is None:
            continue
        if not do_read:
            log("%s %s = (skipped: input is connected - deadlock risk)" % (tag, label))
            continue
        try:
            log("%s %s = %r" % (tag, label, src.GetInput(prop)))
        except Exception as exc:
            log("%s %s read failed: %s" % (tag, label, exc))
    # Dump the CLS's input ids (attrs only, no value evaluation) so a missing
    # text input name can be spotted without touching connected values.
    if cls is not None:
        try:
            ids = []
            for _k, inp in (cls.GetInputList() or {}).items():
                try:
                    ia = inp.GetAttrs() or {}
                    ids.append((ia.get("INPS_ID"), ia.get("INPS_DataType")))
                except Exception:
                    continue
            log("%s cls input ids: %r" % (tag, ids))
        except Exception as exc:
            log("%s cls input dump failed: %s" % (tag, exc))
    return follower, cls


def dump_spacing(tag, tool):
    """Log spacing-related inputs of `tool` (id, value, or connection source)."""
    if tool is None:
        return
    try:
        inputs = tool.GetInputList() or {}
    except Exception:
        return
    for _k, inp in (inputs.items() if hasattr(inputs, "items") else []):
        try:
            ia = inp.GetAttrs() or {}
            iid = ia.get("INPS_ID") or ""
            if "Spacing" not in str(iid):
                continue
            out = inp.GetConnectedOutput()
            if out is not None:
                t = out.GetTool()
                log("%s %s -> connected to %r" % (tag, iid, t))
            else:
                log("%s %s = %r" % (tag, iid, tool.GetInput(iid)))
        except Exception:
            continue


def dump_connections(tag, tool):
    """Log every connected input of `tool` (input id -> connected tool)."""
    try:
        inputs = tool.GetInputList() or {}
    except Exception as exc:
        log("%s GetInputList failed: %s" % (tag, exc))
        return
    for _k, inp in (inputs.items() if hasattr(inputs, "items") else []):
        try:
            out = inp.GetConnectedOutput()
            if out is None:
                continue
            t = out.GetTool()
            if t is None:
                continue
            attrs = t.GetAttrs() or {}
            ia = inp.GetAttrs() if hasattr(inp, "GetAttrs") else None
            iname = (ia or {}).get("INPS_ID") or (ia or {}).get("INPS_Name")
            log("%s input %r(%s) -> %s" % (tag, _k, iname,
                                           (attrs.get("TOOLS_Name"), attrs.get("TOOLS_RegID"))))
        except Exception:
            continue


def main():
    log("=== test_wordpop start ===")
    try:
        ws = load_ws()
    except Exception:
        log("import WhisperSubtitles FAILED:\n" + traceback.format_exc())
        return
    resolve = globals().get("resolve")  # injected by Resolve into THIS script
    if resolve is None:
        resolve = ws.get_resolve()
    if resolve is None:
        log("resolve is None")
        return
    project = resolve.GetProjectManager().GetCurrentProject()
    timeline = project.GetCurrentTimeline() if project else None
    if project is None or timeline is None:
        log("no project/timeline")
        return
    pool = project.GetMediaPool()
    template = ws.find_pool_clip(pool.GetRootFolder(), TEMPLATE_NAME)
    if template is None:
        names = []
        ws.collect_pool_names(pool.GetRootFolder(), names)
        log("template '%s' not in Media Pool; available: %r" % (TEMPLATE_NAME, names))
        return
    # Reuse an existing timeline clip sourced from the Lirik pool item;
    # otherwise append it at the end. (The appended clip may display a
    # different timeline name - it took "White on Blue Shear" last time - so
    # match by source Media Pool item, not by name.)
    matches = []
    for track in range(1, timeline.GetTrackCount("video") + 1):
        for it in timeline.GetItemListInTrack("video", track) or []:
            if TEMPLATE_NAME in (it.GetName() or ""):
                matches.append(it)
                continue
            try:
                mpi = it.GetMediaPoolItem()
                if mpi is not None and mpi.GetName() == TEMPLATE_NAME:
                    matches.append(it)
            except Exception:
                pass
    if len(matches) > 1:
        log("test_wordpop: %d clips sourced from '%s'; using the first, "
            "delete the extras manually" % (len(matches), TEMPLATE_NAME))
    item = matches[0] if matches else None
    if item is None:
        end = timeline.GetStartFrame()
        for track in range(1, timeline.GetTrackCount("video") + 1):
            for it in timeline.GetItemListInTrack("video", track) or []:
                try:
                    end = max(end, it.GetEnd())
                except Exception:
                    pass
        try:
            items = pool.AppendToTimeline([{
                "mediaPoolItem": template, "startFrame": 0, "endFrame": 150,
                "trackIndex": 1, "recordFrame": end, "mediaType": 1}])
        except Exception:
            items = None
        if not items:
            log("could not append '%s' to the timeline" % TEMPLATE_NAME)
            return
        item = items[0]
    log("test_wordpop: clip '%s'" % item.GetName())
    tool, comp = get_tool_and_comp(item, ws)
    if tool is None:
        log("no Text+ tool in the clip")
        return
    follower, cls = dump_text_chain("before:", comp, tool, ws)
    dump_connections("before tool", tool)
    if follower is not None:
        dump_connections("before follower", follower)
    dump_spacing("before tool", tool)
    dump_spacing("before follower", follower)
    dump_spacing("before cls", cls)
    # Prefer the innermost non-empty text - but never read a connected input
    # (that is what deadlocked Resolve). Same skip rules as dump_text_chain.
    text = None
    candidates = []
    if cls is not None:
        candidates.append((cls, "Text"))
    elif follower is not None:
        candidates.append((follower, "Text"))
    else:
        candidates.append((tool, "StyledText"))
    for src, prop in candidates:
        try:
            value = src.GetInput(prop)
        except Exception:
            continue
        if value and str(value).strip():
            text = str(value)
            break
    if not text:
        text = "test word pop here"
    if len(text.split()) < 2:
        # A one-word caption cannot show karaoke: the pop is a subtle 0.8->1.0
        # on a single word. Use a multi-word phrase so the effect is visible.
        text = "satu dua tiga empat lima"
        log("test_wordpop: template text is one word; using demo phrase instead")
    frames = max(6, int(item.GetEnd() - item.GetStart()))
    log("test_wordpop: using text %r, frames %d" % (text, frames))
    t0 = time.time()
    ws.animate_wordpop(comp, tool, frames, text)
    log("probe: animate_wordpop took %.2fs" % (time.time() - t0))
    dump_text_chain("after:", comp, tool, ws)
    dump_connections("after tool", tool)
    follower2 = ws._find_modifier_by_type(tool, "StyledTextFollower")
    dump_spacing("after tool", tool)
    dump_spacing("after follower", follower2)
    dump_spacing("after cls", ws._find_modifier_by_type(
        follower2, "StyledTextCLS") if follower2 else None)
    if follower2 is not None:
        dump_connections("after follower", follower2)
    try:
        timeline.SetCurrentTimecode(item.GetStart())
    except Exception:
        pass
    resolve.OpenPage("fusion")
    log("test_wordpop: done, Fusion page opened")
    log("=== test_wordpop end ===")


try:
    main()
except Exception:
    log("test_wordpop CRASHED:\n" + traceback.format_exc())
