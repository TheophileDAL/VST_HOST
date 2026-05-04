# VST_HOST
A project to host, install, select and control music plugins easily (for midi controller and guitar electric), on a raspberry pi, with an ios app or vocal commands

List of available plugins for the moment:
- (MIDI&Audio)Carla
- (MIDI)Organteq (demo version only)
- (MIDI)Pianoteq (demo version only)
- (MIDI)ZynAddSubFx
- (MIDI)Analog Lab 4 (via wine and box64 and with a desktop os version only / work well with low vst CPU)
- (Audio)Guitarix
- (Audio)Rakarrack-Plus

If you don't find the plugin you looking for, you can add its class file in the "Plugins" folder by referring to the other plugin classes and your plugin's API (like MIDI, OSC, JSON-RPC... if it has one).
