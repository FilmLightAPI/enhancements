import flapi
import sys

def format_range(start, end):
    """Format frame range as 'start-end' or just 'start' if single frame."""
    s = int(start)
    e = int(end)
    if s == e:
        return f"{s}"
    return f"{s}-{e}"


def show_menu_signal(obj, signal, args):
    try:
        app = conn.Application.get()
        
        center_options = [
            {"Key": "poster", "Text": "Centered around Poster Frame"},
            {"Key": "middle", "Text": "Centered around Middle Frame"},
            {"Key": "first", "Text": "Starting at First Frame"},
            {"Key": "last", "Text": "Ending at Last Frame"},
            {"Key": "start_end", "Text": "Start and End Segments"},
            {"Key": "across_cuts", "Text": "Across Cuts"}
        ]

        # Load persistent settings
        dialog_settings = {}
        try:
            customDataKeys = app.get_custom_data_keys()
            if "custom_frame_selector_settings" in customDataKeys:
                loaded_settings = app.get_custom_data("custom_frame_selector_settings")
                
                # Validation: check center_type
                valid_keys = [opt["Key"] for opt in center_options]
                if loaded_settings.get("center_type") in valid_keys:
                    dialog_settings["center_type"] = loaded_settings["center_type"]
                
                # Validation: check numeric fields
                for key in ["segment_length", "min_shot_length"]:
                    if isinstance(loaded_settings.get(key), int):
                        dialog_settings[key] = loaded_settings[key]
        except Exception:
            # Fallback to empty settings if load fails
            dialog_settings = {}

        dialog_items = []
        
        selection_item = flapi.DialogItem({
            "Key"       : "Shots", 
            "Label"     : "Shots",
            "Type"      : flapi.DIT_SHOT_SELECTION
        })
        dialog_items.append(selection_item)

        center_item = flapi.DialogItem({
            "Key"       : "center_type", 
            "Label"     : "Frame Range", 
            "Type"      : flapi.DIT_DROPDOWN,
            "Options"   : center_options,
            "Default"   : "poster"
        })
        dialog_items.append(center_item)

        segment_length_item = flapi.DialogItem({
            "Key"       : "segment_length", 
            "Label"     : "Segment length (frames)", 
            "Type"      : flapi.DIT_INTEGER, 
            "IntMin"    : 1,
            "IntMax"    : 100000,
            "Default"   : 24 
        })    
        dialog_items.append(segment_length_item)

        min_shot_length_item = flapi.DialogItem({
            "Key"       : "min_shot_length", 
            "Label"     : "Minimum shot length (frames)", 
            "Type"      : flapi.DIT_INTEGER, 
            "IntMin"    : 0,
            "IntMax"    : 100000,
            "Default"   : 10 
        })    
        dialog_items.append(min_shot_length_item)

        help_item = flapi.DialogItem({
            "Key"       : "show_help", 
            "Label"     : "Show Help / Usage", 
            "Type"      : flapi.DIT_TOGGLE,
            "Default"   : False
        })
        dialog_items.append(help_item)

        def on_settings_changed(sender, signal, args):
            if args.get("show_help"):
                help_text = (
                    "Custom Frame Range Selector\n\n"
                    "This script generates a list of frame ranges for selected shots that can be pasted directly into the render page.\n\n"
                    "It is useful for rendering short segments of a project to give a quick overview of the grade and its consistency.\n\n"
                    "Modes:\n"
                    "• Centered around Poster: Uses the shot's poster frame as center of the segments.\n"
                    "• Centered around Middle: Uses always the mathematical center of the shot.\n"
                    "• Starting/Ending: Segments are locked to the start or end of the shot.\n"
                    "• Start and End Segments: Returns two segments per shot.\n"
                    "• Across Cuts: Places the segments on the boundaries between shots.\n\n"
                    "The minimum shot length removes very short shots. Use 0 to include all shots.\n\n"
                    "The resulting frame range is copied to your clipboard and shown in an editable box."
                )
                app.message_dialog("Script Help", help_text, ["Close"])
                args["show_help"] = False # Reset toggle
                return {"Valid": 1, "Settings": args}
            return {"Valid": 1, "Settings": args}

        dialog = conn.DynamicDialog.create("Custom Frame Range Selector", dialog_items, dialog_settings)
        dialog.connect("SettingsChanged", on_settings_changed)
        result = dialog.show_modal(700, 350)
        
        if result != None:
            # Save persistent settings
            app.set_custom_data("custom_frame_selector_settings", dialog.get_settings())
            
            scene = app.get_current_scene()
            if scene is None:
                app.message_dialog("Error", "No scene is currently open.", ["Ok"])
                return
            ranges = []
            seg_len = result['segment_length']
            min_len = result['min_shot_length']
            center_type = result['center_type']
            
            if center_type == "across_cuts":
                cut_frames = set()
                for shot_id in result["Shots"]:
                    shot = scene.get_shot(shot_id)
                    start_frame = shot.get_start_frame()
                    end_frame = shot.get_end_frame()
                    duration = end_frame - start_frame
                    if duration >= min_len:
                        cut_frames.add(start_frame)
                        cut_frames.add(end_frame)
                    shot.release()
                
                # Find scene boundaries
                num_shots = scene.get_num_shots()
                all_shots_info = scene.get_shot_ids(0, num_shots)
                scene_start = 0
                scene_end = 0
                if all_shots_info:
                    first_s = scene.get_shot(all_shots_info[0].ShotId)
                    last_s = scene.get_shot(all_shots_info[-1].ShotId)
                    scene_start = first_s.get_start_frame()
                    scene_end = last_s.get_end_frame()
                    first_s.release()
                    last_s.release()

                # Process unique cuts in order
                for frame in sorted(list(cut_frames)):
                    # Centre the segment on the cut frame
                    seg_start = int(frame - seg_len / 2.0)
                    seg_end = seg_start + seg_len - 1

                    # Single unified clamp: shift inward if we exceed either
                    # scene boundary, then hard-clamp as a final safety net.
                    if seg_start < scene_start:
                        # Push segment right
                        shift = scene_start - seg_start
                        seg_start += shift
                        seg_end   += shift
                    if seg_end >= scene_end:
                        # Push segment left
                        shift = seg_end - (scene_end - 1)
                        seg_end   -= shift
                        seg_start -= shift
                    # Hard clamp — handles shots shorter than seg_len
                    seg_start = max(seg_start, scene_start)
                    seg_end   = min(seg_end,   scene_end - 1)

                    range_str = format_range(seg_start, seg_end)
                    if range_str not in ranges:
                        ranges.append(range_str)

            elif center_type == "start_end":
                selected_shots_data = []
                for shot_id in result["Shots"]:
                    shot = scene.get_shot(shot_id)
                    start_frame = shot.get_start_frame()
                    end_frame = shot.get_end_frame()
                    duration = end_frame - start_frame
                    
                    if duration >= min_len:
                        # Start segment
                        s_start = start_frame
                        s_end = s_start + seg_len - 1
                        if s_end >= end_frame: s_end = end_frame - 1
                        
                        # End segment
                        e_end = end_frame - 1
                        e_start = e_end - seg_len + 1
                        if e_start < start_frame: e_start = start_frame
                        
                        range1 = format_range(s_start, s_end)
                        range2 = format_range(e_start, e_end)
                        
                        selected_shots_data.append({"start": start_frame, "range": range1})
                        if range1 != range2:
                            selected_shots_data.append({"start": start_frame + 0.5, "range": range2})
                    
                    shot.release()
                
                selected_shots_data.sort(key=lambda x: x["start"])
                for sd in selected_shots_data:
                    ranges.append(sd["range"])

            else:
                # First 4 modes: Poster, Middle, First, Last
                selected_shots_data = []
                for shot_id in result["Shots"]:
                    shot = scene.get_shot(shot_id)
                    start_frame = shot.get_start_frame()
                    end_frame = shot.get_end_frame()
                    duration = end_frame - start_frame
                    
                    if duration >= min_len:
                        if center_type == "poster":
                            center = shot.get_poster_frame()
                        elif center_type == "middle":
                            center = start_frame + duration / 2.0
                        elif center_type == "first":
                            center = start_frame
                        elif center_type == "last":
                            center = end_frame - 1
                        else:
                            center = start_frame + duration / 2.0
                        
                        seg_start = int(center - seg_len / 2.0)
                        seg_end = seg_start + seg_len - 1
                        
                        # Clamp/Shift logic
                        if seg_start < start_frame:
                            seg_start = start_frame
                            seg_end = seg_start + seg_len - 1
                        
                        if seg_end >= end_frame:
                            seg_end = end_frame - 1
                            seg_start = seg_end - seg_len + 1
                        
                        # Safety check
                        if seg_start < start_frame:
                            seg_start = start_frame
                        
                        selected_shots_data.append({
                            "start": start_frame,
                            "range": format_range(seg_start, seg_end)
                        })
                    shot.release()
                
                selected_shots_data.sort(key=lambda x: x["start"])
                for shot_data in selected_shots_data:
                    ranges.append(shot_data["range"])
                    
            output_str = ",".join(ranges)
            
            if not output_str:
                scene.release()
                app.message_dialog("Result", "No shots matched the criteria.", ["Ok"])
                return

            try:
                app.set_clipboard(output_str)
                clipboard_success = True
            except Exception:
                clipboard_success = False
            
            title = "Success (Copied to Clipboard)" if clipboard_success else "Result (Clipboard Failed)"
            label = "The following ranges are in your clipboard:" if clipboard_success else "Manual copy required:"
            
            result_items = [
                flapi.DialogItem({
                    "Key"    : "label_text", 
                    "Label"  : "",
                    "Type"   : flapi.DIT_STATIC_TEXT, 
                    "Default": label
                }),
                flapi.DialogItem({
                    "Key"    : "output", 
                    "Label"  : "", 
                    "Type"   : flapi.DIT_STRING, 
                    "Default": output_str
                })
            ]
            
            if clipboard_success:
                result_items.append(flapi.DialogItem({
                    "Key"    : "success_msg", 
                    "Label"  : "",
                    "Type"   : flapi.DIT_STATIC_TEXT, 
                    "Default": "✓ Copied to Clipboard"
                }))
            
            result_dialog = conn.DynamicDialog.create(title, result_items, {})
            result_dialog.show_modal(700, 200)
            
            # Explicit resource cleanup
            scene.release()

    except Exception as e:
        app.message_dialog("Error", f"{e}", ["Ok"])

# Connect to FLAPI
conn = flapi.Connection.get() 
try:
    conn.connect()
except flapi.FLAPIException as ex:
    sys.exit(1)

app = conn.Application.get()

menuItem = conn.MenuItem.create("Custom Frame Range Selector", "CustomFrameRangeSelectorMenuItem")
menuItem.register(flapi.MENULOCATION_SHOT_VIEW)
menuItem.connect("MenuItemSelected", show_menu_signal)
