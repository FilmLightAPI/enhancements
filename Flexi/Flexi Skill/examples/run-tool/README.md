# Example Run Tool

Wraps a command-line tool you already have: Baselight writes each frame to an image file, the
effect runs the tool on it, and Baselight reads back the file the tool wrote.

- `flexi_run_tool.py` declares `process_mode: file` with `process_filetype: PPM16`, then in
  `run_generate` passes the input file (`data['inputs']['src:0']['file']`) and the output file
  (`data['output']['file']`) to the tool. It never decodes the images itself.
- `tool/gamma.py` stands in for your tool. Replace `TOOL` with your program's command line; ship
  the program under `tool/` (listed in `sources`) or name one every render machine has.
- Parameters become command-line arguments.
- The tool runs with a time limit, in its own process group so that anything it starts is
  stopped too. Baselight waits for every reply without a limit, so a tool that hangs would hang
  the render.
- `local_methods` asks for the input to cover exactly the output area. The tool's result, the
  size of its input, then fits the output.
- When the tool fails, its error output goes back to Baselight with `flexi.error`, so the user
  sees why.
- It reports no VRAM need (`min_mb` and `max_mb` 0). If your tool uses the GPU, report what it
  needs: see `references/vram.md`.

## Choosing the file type

Pick a `process_filetype` your tool reads and writes, from the types `bl-render -list` shows.
`PPM16` and the other integer types hold values from 0 to 1 only: scene-linear or log images with
values outside that range are clipped. Use `EXR` for those. Baselight reads back any type it
knows. It places the result at the output area's top-left corner and fills anything the result
does not cover with black, so the result must have the size of `data['output']['rect']`.

If your tool writes a type Baselight cannot read, or needs other files, convert or collect them
in `run_generate`.

## Several frames at once

For a tool that needs neighbouring frames, declare `temporal` offsets on the input (see
`references/temporal.md`): each frame then arrives as its own file, under `src:-1`, `src:0`,
`src:1` and so on. Frames outside the shot are missing: check before using them.

## Testing

`fl-flexi-test.py` does not drive `file`-mode effects. Test the tool on its own on an image file,
then install the effect and render a frame in Baselight (see `references/testing.md`).
