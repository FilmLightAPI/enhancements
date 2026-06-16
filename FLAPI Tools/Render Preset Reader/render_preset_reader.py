#!/usr/bin/env python3

# Last Updated June 6, 2026
# Reads Baselight render presets from bluserprefs files.
#
# Can be run on the command-line with no arguments to read from user preferences,
# or be given the location of a blpref file.
#
# Call from another Python script with:
#       render_presets = RenderPresetReader.auto().read()
#
#   Or with a specific path:
#       render_presets = RenderPresetReader(Path('path/to/bluserprefs'))
#       render_presets.read()
#
#   Read from a stored JSON file with:
#       render_presets = RenderPresetReader.from_json('path/to/myfile.json')
#
# Once presets are read, use:
#  
#    deliverables = render_presets.deliverables   # list of flapi.RenderDeliverable
#    dicts = render_presets.to_dicts()    # (optional) list of plain dicts
#    specific_deliverable = render_presets.get('deliverable_name')
#
#    for d in render_presets.deliverables:
#        print(d.Name)
#    render_presets.to_json('path/to/myflie.json')
#    renderSetup.add_deliverable(render_presets.get('My Named Deliverable'))


import json
import re
import sys
from pathlib import Path

import flapi

RS_TO_RD = {
    "rs_name": "Name",
    "rs_movie": "IsMovie",
    "rs_file_type": "FileType",
    "rs_movie_codec": "MovieCodec",
    "rs_audio_codec": "AudioCodec",
    "rs_image_options": "ImageOptions",
    "rs_movie_params": "ImageOptions",
    "rs_faststart": "FastStart",
    "rs_audio_sample_rate": "AudioSampleRate",
    "rs_audio_num_channels": "AudioNumChannels",
    "rs_container": "Container",
    "rs_output_dir": "OutputDirectory",
    "rs_file_prefix": "FileNamePrefix",
    "rs_file_postfix": "FileNamePostfix",
    "rs_pad_len": "FileNameNumDigits",
    "rs_file_letter": "FileNameNumber",
    "rs_file_ext": "FileNameExtension",
    "rs_nclc": "ColourSpaceTag",
    "rs_render_format": "RenderFormat",
    "rs_render_resolution": "RenderResolution",
    "rs_output_frame_rate": "RenderFrameRate",
    "rs_render_field_order": "RenderFieldOrder",
    "rs_decode_quality": "RenderDecodeQuality",
    "rs_render_colour_space": "RenderColourSpace",
    "rs_video_lut": "RenderVideoLUT",
    "rs_layer": "RenderLayer",
    "rs_render_track": "RenderTrack",
    "rs_render_mask": "RenderMask",
    "rs_mask_black": "RenderMaskMode",
    "rs_burnin": "RenderBurnin",
    "rs_burnin_flash": "RenderFlashBurnin",
    "rs_dont_read_cache": "RenderDisableCache",
    "rs_nocache": "RenderDisableCache",
    "rs_channels": "RenderChannels",
    "rs_alpha_handling": "RenderAlphaHandling",
    "rs_missingstripbehaviour": "HandleIncompleteStacks",
    "rs_emptyframebehaviour": "HandleEmptyFrames",
    "rs_errorbehaviour": "HandleError",
    "rs_embedtimecode": "EmbedTimecode",
    "rs_embedtape": "EmbedTape",
    "rs_embedclip": "EmbedClip",
    "rs_render_depth": "RenderDepth",
    "rs_disabled": "Disabled",
    "rs_track": "RenderTrack",
}

INT_FIELDS = {
    "Disabled", "IsMovie", "FastStart",
    "AudioSampleRate", "AudioNumChannels", "FileNameNumDigits",
    "ColourSpaceTag", "RenderLayer", "RenderTrack", "RenderMaskMode",
    "RenderFlashBurnin", "RenderDisableCache", "EmbedTimecode",
    "EmbedTape", "EmbedClip", "RenderDepth",
}

FLOAT_FIELDS = {"RenderFrameRate"}


class RenderPresetReader:
    """Reads Baselight render presets from bluserprefs files.

    Usage:
        reader = RenderPresetReader.auto()
        reader.read()
        for d in reader.deliverables:
            print(d.Name)
        reader.to_json()

    Or with a specific path:
        reader = RenderPresetReader(Path("path/to/bluserprefs"))
        reader.read()
    """

    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self._presets = []
        self._deliverables = []

    # ---- Public API ----

    @classmethod
    def auto(self):
        """Auto-detect bluserprefs or blduserprefs path."""
        path = self._default_bluserprefs_path()
        if not path:
            raise FileNotFoundError(
                "Could not auto-detect bluserprefs. "
                "Pass an explicit path or set it after construction."
            )
        return self(path)

    def read(self):
        """Parse the file, populate presets and deliverables.

        Returns self for chaining.
        """
        if not self.path or not self.path.exists():
            raise FileNotFoundError(
                f"bluserprefs file not found: {self.path}"
            )
        raw = self.path.read_text()
        filtered = self._filter_data_lines(raw)

        presets = self._find_structs_in_text(filtered)
        meta_presets = self._find_meta_structs_in_text(filtered)

        self._presets = presets + meta_presets
        self._deliverables = []
        for fields in self._presets:
            d = self._fields_to_deliverable(fields)
            if d:
                self._deliverables.append(d)
        return self

    @property
    def deliverables(self):
        """flapi.RenderDeliverable objects (list)."""
        return list(self._deliverables)

    def to_dicts(self):
        """Convert deliverables to plain dicts for JSON serialization."""
        return [vars(d) for d in self._deliverables]

    def to_json(self, path="render_deliverables.json", indent=2):
        """Write deliverables as JSON. Returns the output path."""
        output = self.to_dicts()
        with open(path, "w") as f:
            json.dump(output, f, indent=indent, default=str)
        return path

    def read_json(self, path):
        """Load deliverables from a JSON file written by to_json().

        Populates ``deliverables`` and ``to_dicts()`` from the file.
        Returns self for chaining.
        """
        with open(path) as f:
            dicts = json.load(f)
        self._deliverables = [self._dict_to_deliverable(d) for d in dicts]
        return self

    @classmethod
    def from_json(self, path):
        """Create a reader pre-loaded from a JSON file written by to_json()."""
        reader = self()
        reader.read_json(path)
        return reader

    def get(self, name):
        """Return the first flapi.RenderDeliverable matching *name*, or None."""
        for d in self._deliverables:
            if d.Name == name:
                return d
        return None

    # ---- Internal helpers ----

    @staticmethod
    def _parse_bl_value_at(text, start):
        pos = start
        length = len(text)

        while pos < length and text[pos] in " \t\n\r":
            pos += 1
        if pos >= length:
            return None, pos

        if text[pos] == '"':
            pos += 1
            result = []
            while pos < length:
                if text[pos] == '\\':
                    pos += 1
                    if pos < length:
                        result.append(text[pos])
                        pos += 1
                elif text[pos] == '"':
                    pos += 1
                    return "".join(result), pos
                else:
                    result.append(text[pos])
                    pos += 1
            return "".join(result), pos

        if text[pos] == '[':
            depth = 1
            pos += 1
            while pos < length and depth > 0:
                if text[pos] == '[':
                    depth += 1
                elif text[pos] == ']':
                    depth -= 1
                pos += 1
            return None, pos

        if text.startswith("NULL", pos):
            return None, pos + 4

        end = pos
        while end < length and text[end] not in " \t\n\r,]}":
            end += 1
        raw = text[pos:end]
        try:
            if "." in raw or "e" in raw.lower():
                return float(raw), end
            return int(raw), end
        except (ValueError, TypeError):
            return raw, end

    @classmethod
    def _extract_struct_fields(self, text):
        fields = {}
        pos = 0
        length = len(text)

        while pos < length:
            while pos < length and text[pos] in " \t\n\r,":
                pos += 1
            if pos >= length:
                break

            m = re.match(r'(rs_[a-zA-Z_]+)\s*=', text[pos:])
            if not m:
                pos += 1
                continue

            field_name = m.group(1)
            pos += m.end()

            while pos < length and text[pos] in " \t\n\r":
                pos += 1
            if pos >= length:
                break

            value, end_pos = self._parse_bl_value_at(text, pos)
            fields[field_name] = value
            pos = end_pos

        return fields

    @classmethod
    def _find_structs_in_text_body(self, matches, text, structs):
        for m in matches:
            name = m.group(1)
            struct_start = m.end()
            depth = 1
            pos = struct_start
            while pos < len(text) and depth > 0:
                if text[pos] == '[':
                    depth += 1
                elif text[pos] == ']':
                    depth -= 1
                pos += 1
            struct_content = text[struct_start:pos - 1]
            fields = self._extract_struct_fields(struct_content)
            fields["rs_name"] = name
            structs.append(fields)

    @classmethod
    def _find_structs_in_text(self, text):
        # parse /* render_presets */
        structs = []
        pattern = re.compile(r'render_presets\.(\w+)\s*=\s*\[struct\s*', re.DOTALL)
        if re.search(pattern, text) is not None:
            self._find_structs_in_text_body(pattern.finditer(text), text, structs)
        pattern = re.compile(r'render_presets\[\"([^\"]+)\"\]\s*=\s*\[struct\s*', re.DOTALL)
        if re.search(pattern, text) is not None:
            self._find_structs_in_text_body(pattern.finditer(text), text, structs)
        return structs

    @classmethod
    def _find_meta_structs_in_array(self, pattern, text, structs):
        for m in pattern.finditer(text):
            array_start = m.end()
            depth = 1
            pos = array_start
            while pos < len(text) and depth > 0:
                if text[pos] == '[':
                    depth += 1
                elif text[pos] == ']':
                    depth -= 1
                pos += 1
            array_content = text[array_start:pos - 1]
            struct_pattern = re.compile(r'\[struct\s*', re.DOTALL)
            for sm in struct_pattern.finditer(array_content):
                ss = sm.end()
                sd = 1
                sp = ss
                while sp < len(array_content) and sd > 0:
                    if array_content[sp] == '[':
                        sd += 1
                    elif array_content[sp] == ']':
                        sd -= 1
                    sp += 1
                fields = self._extract_struct_fields(array_content[ss:sp - 1])
                if 'rs_name' in fields :
                    fields['rs_name'] = m.group(1) + '.' + fields['rs_name']
                structs.append(fields)

    @classmethod
    def _find_meta_structs_in_text(self, text):
        # parse /* render_metapresets */  (Deliverable sets)
        structs = []
        pattern = re.compile(r'render_metapresets\.(\w+)\s*=\s*\[array\s*', re.DOTALL)
        self._find_meta_structs_in_array(pattern, text, structs)
        pattern = re.compile(r'render_metapresets\[\"([^\"]+)\"\]\s*=\s*\[array\s*', re.DOTALL)
        self._find_meta_structs_in_array(pattern, text, structs)
        return structs

    @staticmethod
    def _filter_data_lines(text):
        lines = text.split("\n")
        result = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("} onerror { oldprefs."):
                continue
            result.append(line)
        return "\n".join(result)

    @staticmethod
    def _fields_to_deliverable(fields):
        d = flapi.RenderDeliverable()
        for rs_name, raw_value in fields.items():
            rd_name = RS_TO_RD.get(rs_name)
            if rd_name is None:
                continue
            if raw_value is None:
                continue
            if rd_name == 'ImageOptions':
                # Both "rs_image_options" and "rs_movie_params" can be set, but we only want to apply the relevant one to ImageOptions
                if rs_name == "rs_image_options" and d.IsMovie:
                    continue
                if rs_name == "rs_movie_params" and not d.IsMovie:
                    continue
                if not raw_value:
                    continue
                value = str(raw_value).lstrip('/')
                if "=" not in value:
                    # rs_image_options="/PIZ"
                    setattr(d, rd_name, {'compression': value})
                else:
                    # rs_image_options="/quality=90"
                    # rs_movie_params="kbitrate=20000"
                    # rs_movie_params="x264_i_bframe_adaptive="None";x264_i_bitrate=10000;x264_i_rc_method="Average bitrate""
                    matches = re.findall(r'(\w+)=([^;\n]+)', str(raw_value))
                    if matches:
                        setattr(d, rd_name, dict(matches))
            elif rd_name in INT_FIELDS:
                try:
                    setattr(d, rd_name, int(raw_value))
                except (ValueError, TypeError):
                    setattr(d, rd_name, 0)
            elif rd_name in FLOAT_FIELDS:
                try:
                    setattr(d, rd_name, float(raw_value))
                except (ValueError, TypeError):
                    setattr(d, rd_name, 0.0)
            else:
                setattr(d, rd_name, str(raw_value))
        if d.Name:
            return d
        return None

    @staticmethod
    def _dict_to_deliverable(d):
        rd = flapi.RenderDeliverable()
        for k, v in d.items():
            if v is not None:
                setattr(rd, k, v)
        return rd

    @staticmethod
    def _default_bluserprefs_path():
        if sys.platform == "darwin":
            path = Path.home() / "Library/Preferences/FilmLight/Baselight/bluserprefs"
            if path.exists():
                return path
            path = Path.home() / "Library/Preferences/FilmLight/Baselight/blduserprefs"
            if path.exists():
                return path
        else:
            path = Path.home() / ".baselight/bluserprefs"
            if path.exists():
                return path
            path = Path.home() / ".baselight/blduserprefs"
            if path.exists():
                return path
        return None


def main():
    if len(sys.argv) > 1:
        reader = RenderPresetReader(Path(sys.argv[1]))
    else:
        reader = RenderPresetReader.auto()

    reader.read()

    if not reader.deliverables:
        print("No render presets found.", file=sys.stderr)
        sys.exit(0)

    output_path = reader.to_json()

    print(f"Found {len(reader.deliverables)} render preset(s)")
    for d in reader.deliverables:
        print(f"  - {d.Name}  (File Type = {d.FileType})")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
