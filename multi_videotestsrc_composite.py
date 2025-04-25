#!/usr/bin/env python3
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

Gst.init(None)

pipeline      = Gst.Pipeline.new("display-only-pipeline")

source1       = Gst.ElementFactory.make("videotestsrc", "source1")
source2       = Gst.ElementFactory.make("videotestsrc", "source2")
compositor    = Gst.ElementFactory.make("compositor",  "compositor")
videoconvert  = Gst.ElementFactory.make("videoconvert","videoconvert")
sink          = Gst.ElementFactory.make("autovideosink","sink")

if not all((pipeline, source1, source2, compositor, videoconvert, sink)):
    raise RuntimeError("Failed to create one or more GStreamer elements.")

source1.set_property("pattern", 0)
source2.set_property("pattern", 1)

# --- add each element separately ---
for elem in (source1, source2, compositor, videoconvert, sink):
    pipeline.add(elem)
# -----------------------------------

if not compositor.link(videoconvert):
    raise RuntimeError("Could not link compositor → videoconvert")
if not videoconvert.link(sink):
    raise RuntimeError("Could not link videoconvert → sink")

def attach(src, xpos):
    caps = Gst.Caps.from_string("video/x-raw,width=320,height=240")
    sink_pad = compositor.get_request_pad("sink_%u")
    sink_pad.set_property("xpos", xpos)
    sink_pad.set_property("ypos", 0)
    if not src.link_filtered(compositor, caps):
        raise RuntimeError(f"Could not link {src.get_name()} to compositor")

attach(source1, 0)
attach(source2, 320)

loop = GLib.MainLoop()
bus  = pipeline.get_bus()
bus.add_signal_watch()

def on_message(bus, message, loop):
    if message.type == Gst.MessageType.EOS:
        loop.quit()
    elif message.type == Gst.MessageType.ERROR:
        err, dbg = message.parse_error()
        print(f"ERROR: {err}\nDEBUG: {dbg}")
        loop.quit()

bus.connect("message", on_message, loop)

pipeline.set_state(Gst.State.PLAYING)
GLib.timeout_add_seconds(5, lambda: pipeline.send_event(Gst.Event.new_eos()) or False)

try:
    loop.run()
finally:
    pipeline.set_state(Gst.State.NULL)
