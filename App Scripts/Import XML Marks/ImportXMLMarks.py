# Updated July 28, 2026
import flapi
import os
import xml.etree.ElementTree as ET

conn = flapi.Connection.get()

class ImportXMLMarksDialog:
    def __init__(self):
        self.app = conn.Application.get()
        self.scene = self.app.get_current_scene()
        
        self.options = [
            {"Key": "Absolute XML Timecode", "Text": "Absolute XML Timecode"},
            {"Key": "Scene Frame Number", "Text": "Scene Frame Number"},
            {"Key": "Relative to Cursor Position", "Text": "Relative to Cursor Position"}
        ]
        
        self.import_marks_options = [
            {"Key": "All Marks", "Text": "All Marks"},
            {"Key": "Sequence Marks", "Text": "Sequence Marks"},
            {"Key": "Clip Marks", "Text": "Clip Marks"}
        ]
        
        self.mark_types = [
            {"Key": "Auto", "Text": "Auto"},
            {"Key": "Timeline Marks", "Text": "Timeline Marks"},
            {"Key": "Shot Marks", "Text": "Shot Marks"}
        ]
        
        self.items = [
            flapi.DialogItem(
                Key="XMLFile",
                Label="Premiere XML File",
                Type=flapi.DIT_FILEPATH,
                Default=os.path.expanduser("~")
            ),
            flapi.DialogItem(
                Key="Category",
                Label="Mark Category",
                Type=flapi.DIT_MARK_CATEGORY,
                Help="Select which Baselight category to assign the marks to"
            ),
            flapi.DialogItem(
                Key="ImportMarks",
                Label="Import Marks",
                Type=flapi.DIT_DROPDOWN,
                Options=self.import_marks_options,
                Default="All Marks",
                Help="• All Marks: Imports both Sequence and Clip markers\n"
                     + "• Sequence Marks: Only imports markers on the main timeline\n"
                     + "• Clip Marks: Only imports markers embedded inside clips\n"
            ),
            flapi.DialogItem(
                Key="MarkType",
                Label="Mark Type",
                Type=flapi.DIT_DROPDOWN,
                Options=self.mark_types,
                Default="Auto",
                Help="• Auto: Sequence Marks become Timeline Marks; Clip Marks become Shot Marks\n"
                     + "• Timeline Marks: Forces all markers to be Timeline Marks\n"
                     + "• Shot Marks: Forces all markers to be Shot Marks (falls back to Timeline if shot is missing)\n"
            ),
            flapi.DialogItem(
                Key="Mode",
                Label="Placement Mode",
                Type=flapi.DIT_DROPDOWN,
                Options=self.options,
                Default="Absolute XML Timecode",
                Help="• Absolute XML Timecode: Place marks based on Record Timecode\n"
                     + "• Scene Frame Number: Aligns the start of the XML with the start of the Baselight timeline\n"
                     + "• Relative to Cursor Position: Adds the marker offset to the current cursor position\n"
            ),
        ]
        
        self.settings = {
            "XMLFile": os.path.expanduser("~"),
            "ImportMarks": "All Marks",
            "MarkType": "Auto",
            "Mode": "Absolute XML Timecode"
        }
        
        try:
            customDataKeys = self.app.get_custom_data_keys()
            if "import_xml_marks_settings" in customDataKeys:
                loaded_settings = self.app.get_custom_data("import_xml_marks_settings")
                if isinstance(loaded_settings, dict):
                    for key in ["XMLFile", "Category", "ImportMarks", "MarkType", "Mode"]:
                        if key in loaded_settings:
                            self.settings[key] = loaded_settings[key]
                    if self.settings.get("ImportMarks") == "Chapter Marks":
                        self.settings["ImportMarks"] = "Sequence Marks"
        except Exception:
            pass
        
        self.dialog = conn.DynamicDialog.create(
            "Import XML Marks",
            self.items,
            self.settings
        )
        
    def show(self):
        result = self.dialog.show_modal(-200, -50)
        if result:
            try:
                self.app.set_custom_data("import_xml_marks_settings", result)
            except Exception:
                pass
        return result

class ImportXMLMarksMenu:
    def __init__(self):
        self.menuItem = conn.MenuItem.create("Import XML Marks...")
        self.menuItem.register(flapi.MENULOCATION_SHOT_VIEW)
        self.menuItem.connect("MenuItemSelected", self.handle_menu_item)
        self.menuItem.connect("MenuItemUpdate", self.handle_menu_item_state)
        
    def handle_menu_item_state(self, sender, signal, args):
        app = conn.Application.get()
        scene = app.get_current_scene()
        self.menuItem.set_enabled(scene is not None)
        
    def handle_menu_item(self, sender, signal, args):
        dialog = ImportXMLMarksDialog()
        result = dialog.show()
        if not result:
            return
            
        xml_file = result["XMLFile"]
        category = result.get("Category", "Default")
        import_marks = result.get("ImportMarks", "All Marks")
        mode = result["Mode"]
        mark_type = result["MarkType"]
        
        app = conn.Application.get()
        scene = app.get_current_scene()
        if not scene:
            return
            
        if not os.path.exists(xml_file) or not xml_file.lower().endswith(".xml"):
            app.message_dialog("Error", f"Invalid XML file selected:\n{xml_file}", ["OK"])
            return
            
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            sequence = root.find('.//sequence')
            if sequence is None:
                app.message_dialog("Error", "No <sequence> found in the XML file.", ["OK"])
                return
                
            # Get XML timebase
            timebase_elem = sequence.find('./rate/timebase')
            if timebase_elem is None:
                app.message_dialog("Error", "Could not find timebase in the XML file.", ["OK"])
                return
            xml_fps = float(timebase_elem.text)
            if xml_fps <= 0:
                app.message_dialog("Error", "Invalid timebase (0 or negative) in the XML file.", ["OK"])
                return
            
            # Get XML start frame
            xml_start_frame = 0
            timecode_frame_elem = sequence.find('./timecode/frame')
            if timecode_frame_elem is not None:
                xml_start_frame = int(timecode_frame_elem.text)
                
            all_markers = []
            
            # Extract Sequence Marks
            if import_marks in ["All Marks", "Sequence Marks"]:
                for m in sequence.findall('marker'):
                    all_markers.append({
                        "type": "sequence",
                        "element": m
                    })
                    
            # Extract Clip Marks
            if import_marks in ["All Marks", "Clip Marks"]:
                for clipitem in sequence.findall('.//clipitem'):
                    c_start = clipitem.find('start')
                    c_in = clipitem.find('in')
                    c_end = clipitem.find('end')
                    c_out = clipitem.find('out')
                    
                    if c_start is None or c_in is None or c_end is None or c_out is None:
                        continue
                        
                    try:
                        clip_start_frames = int(c_start.text) if c_start.text else 0
                        clip_in_frames = int(c_in.text) if c_in.text else 0
                        clip_end_frames = int(c_end.text) if c_end.text else 0
                        clip_out_frames = int(c_out.text) if c_out.text else 0
                    except ValueError:
                        continue
                    
                    for m in clipitem.findall('marker'):
                        all_markers.append({
                            "type": "clip",
                            "element": m,
                            "clip_start": clip_start_frames,
                            "clip_in": clip_in_frames,
                            "clip_end": clip_end_frames,
                            "clip_out": clip_out_frames
                        })

            if not all_markers:
                app.message_dialog("Warning", "No markers found matching your selection.", ["OK"])
                return
                
            scene_fps = scene.get_working_frame_rate()
            fps_mismatch = (xml_fps != scene_fps)
            
            scene_start_frame = scene.get_start_frame()
            scene_start_tc_frames = 0
            try:
                scene_tc_str = str(scene.get_record_timecode_for_frame(scene_start_frame))
                import re
                match = re.search(r'(\d+)[:;](\d+)[:;](\d+)[:;](\d+)', scene_tc_str)
                if match:
                    h, m, s, f = map(int, match.groups())
                    scene_start_tc_frames = int(round((h * 3600 + m * 60 + s) * scene_fps + f))
            except Exception:
                pass
                
            cursor = app.get_current_cursor()
            cursor_frame = cursor.get_frame() if cursor else scene_start_frame
            
            scene.set_transient_write_lock_deltas(True)
            scene.start_delta("Import XML Marks")
            
            count = 0
            for mark_data in all_markers:
                m = mark_data["element"]
                m_type = mark_data["type"]
                
                try:
                    name_elem = m.find('name')
                    name = (name_elem.text or "") if name_elem is not None else ""
                    
                    comment_elem = m.find('comment')
                    comment = (comment_elem.text or "") if comment_elem is not None else ""
                    
                    in_elem = m.find('in')
                    if in_elem is None or not in_elem.text:
                        continue
                        
                    in_frames = int(in_elem.text)
                    
                    note_text = name
                    if comment:
                        note_text = f"{name}: {comment}" if name else comment
                    if not note_text:
                        note_text = "Marker"
                        
                    out_elem = m.find('out')
                    if out_elem is not None and out_elem.text:
                        try:
                            out_frames = int(out_elem.text)
                            if out_frames != -1 and out_frames > in_frames:
                                length_frames = out_frames - in_frames
                                note_text += f" (Length: {length_frames} frames)"
                        except ValueError:
                            pass
                            
                    # Calculate timeline position
                    if m_type == "sequence":
                        if mode == "Scene Frame Number":
                            dest_frame = scene_start_frame + in_frames
                        elif mode == "Absolute XML Timecode":
                            total_xml_frames = xml_start_frame + in_frames
                            total_seconds = total_xml_frames / float(xml_fps)
                            scene_total_frames = int(round(total_seconds * scene_fps))
                            dest_frame = scene_start_frame + (scene_total_frames - scene_start_tc_frames)
                        elif mode == "Relative to Cursor Position":
                            dest_frame = cursor_frame + in_frames
                        else:
                            dest_frame = in_frames
                    else:
                        clip_start = mark_data["clip_start"]
                        clip_in = mark_data["clip_in"]
                        clip_end = mark_data["clip_end"]
                        clip_out = mark_data["clip_out"]
                        
                        if mode == "Scene Frame Number":
                            clip_tl_start = scene_start_frame + clip_start
                        elif mode == "Absolute XML Timecode":
                            total_xml_frames = xml_start_frame + clip_start
                            total_seconds = total_xml_frames / float(xml_fps)
                            scene_total_frames = int(round(total_seconds * scene_fps))
                            clip_tl_start = scene_start_frame + (scene_total_frames - scene_start_tc_frames)
                        elif mode == "Relative to Cursor Position":
                            clip_tl_start = cursor_frame + clip_start
                        else:
                            clip_tl_start = clip_start
                            
                        # Estimate timeline fallback position for clip mark
                        tl_duration = max(1, clip_end - clip_start)
                        src_duration = max(1, clip_out - clip_in)
                        xml_tl_offset = int(round((in_frames - clip_in) * tl_duration / src_duration))
                        
                        if mode == "Absolute XML Timecode":
                            converted_tl_offset = int(round(xml_tl_offset * (scene_fps / xml_fps)))
                        else:
                            converted_tl_offset = xml_tl_offset
                            
                        dest_frame = clip_tl_start + converted_tl_offset
                        
                    # Prevent out of bounds errors if dest_frame is negative
                    dest_frame = max(0, dest_frame)
                    
                    target_mark_type = mark_type
                    if target_mark_type == "Auto":
                        target_mark_type = "Timeline Marks" if m_type == "sequence" else "Shot Marks"
                        
                    success = False
                    if target_mark_type == "Shot Marks":
                        search_frame = max(0, clip_tl_start if m_type == "clip" else dest_frame)
                        shot_id = scene.get_shot_id_at(search_frame)
                        
                        if shot_id != -1:
                            shot = scene.get_shot(shot_id)
                            tl_start = shot.get_start_frame()
                            tl_end = shot.get_end_frame()
                            src_start = shot.get_src_start_frame()
                            src_end = shot.get_src_end_frame()
                            
                            if m_type == "clip":
                                baselight_src_frame = src_start + (in_frames - mark_data["clip_in"])
                                try:
                                    shot.add_mark(baselight_src_frame, category, note_text)
                                    success = True
                                except Exception:
                                    pass
                            else:
                                if src_start != src_end:
                                    tl_offset = dest_frame - tl_start
                                    src_offset = int(round(tl_offset * (src_end - src_start) / max(1, tl_end - tl_start)))
                                    baselight_src_frame = src_start + src_offset
                                    try:
                                        shot.add_mark(baselight_src_frame, category, note_text)
                                        success = True
                                    except Exception:
                                        pass
                            shot.release()
                            
                    if not success:
                        try:
                            scene.add_mark(dest_frame, category, note_text)
                        except Exception:
                            pass
                            
                    count += 1
                except (ValueError, TypeError, Exception):
                    continue
                
            scene.end_delta()
            scene.set_transient_write_lock_deltas(False)
            
            if fps_mismatch:
                msg = f"Successfully imported {count} markers.\n\nNote: XML frame rate ({xml_fps} fps) did not match Scene frame rate ({scene_fps} fps)."
            else:
                msg = f"Successfully imported {count} markers."
                
            app.message_dialog("Success", msg, ["OK"])
            
        except Exception as e:
            app.message_dialog("Error", f"Failed to parse XML or add markers:\n{str(e)}", ["OK"])

import_xml_menu = ImportXMLMarksMenu()
