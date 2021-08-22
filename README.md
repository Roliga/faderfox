Faderfox MIDI Driver
====================

Reads MIDI commands from the [Faderfox PC4](http://www.faderfox.de/pc4.html) and control playback volume on Linux via Pulseaudio.

Can probably also be used with any other MIDI device with minimal modification.

Configuration is read from `config.json` either in the current working directory, in `$XDG_CONFIG_HOME/faderfox/` or `~/.config/faderfox/`. See `config-example.json` for an example.

MIDI channels can be mapped to Pulseaudio sinks, sources, sink-inputs or source-outputs by filtering by name or properties. These can be found in the *Name:* and *Properties:* fields when running `pactl list [sinks|sources|sink-inputs|source-outputs]`. If multiple filters are specified, only objects that match all of them will be used.

Note that the actual name of a sink/source may be different from what you see in your normal volume control apps, as those usually display the `device.description` property.
