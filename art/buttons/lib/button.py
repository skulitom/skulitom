"""Build driver shared by the seven buttons.

Usage (from a button folder, as its build.sh does):
  python ../lib/button.py sources    write out/fluids/*.fluid.json from the scene's sources()
  python ../lib/button.py recipes    write out/recipes/<name>[-narrow].json and the review recipes
  python ../lib/button.py wraps      write out/<name>[-narrow][-still].wrap.json

A scene module (src/scene.py) defines:
  NAME, KIND ("portfolio" | "tile"), FRAMES (motion frames + 1 hold frame, the hold is last), TITLE, DESC,
  VARIANTS: {"regular": (w, h), "narrow": (w, h)} (tiles) or {"regular": (w, h)},
  frame_ops(i, variant) -> list of Pixelbolt operations for frame i,
  optionally SYMBOLS (dict), sources() -> {file stem: fluid source dict}.

Timing: frames 0 .. FRAMES-2 run at 70 ms; the last frame is the hold, which takes the rest of the 24,000 ms cycle and
is the reduced-motion still. Frame 0 is the start of the motion, so the integrator's 4 s stagger starts each button's
motion on its own beat.
"""

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pb import MS, CYCLE, recipe, write_json, flat  # noqa: E402

HERE = Path.cwd()


def load_scene():
    spec = importlib.util.spec_from_file_location("scene", HERE / "src" / "scene.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HERE / "src"))
    spec.loader.exec_module(mod)
    return mod


def durations(n):
    hold = CYCLE - MS * (n - 1)
    return [MS] * (n - 1) + [hold]


def variant_name(scene, variant):
    return scene.NAME if variant == "regular" else f"{scene.NAME}-{variant}"


def build_recipes(scene):
    rdir = HERE / "out" / "recipes"
    for variant, (w, h) in scene.VARIANTS.items():
        name = variant_name(scene, variant)
        ds = durations(scene.FRAMES)
        frames = []
        for i in range(scene.FRAMES):
            body = scene.frame_ops(i, variant)
            f = {"name": f"{name}-{i}", "duration": ds[i]}
            if isinstance(body, dict):
                f["ops"] = flat(body["ops"])
                f["layers"] = [dict(layer, ops=flat(layer["ops"])) for layer in body["layers"]]
            else:
                f["ops"] = flat(body)
            frames.append(f)
        anims = {name: {"frames": [f["name"] for f in frames]}}
        rec = recipe(name, w, h, frames, rdir, animations=anims, symbols=getattr(scene, "SYMBOLS", None))
        write_json(rdir / f"{name}.json", rec)
        # Review recipe: the same frames, with the hold cut to 1,050 ms so a GIF shows the motion and a beat of rest
        # (the hold is the frame the page shows most of the time). Rendered at 6x by Pixelbolt's gif command.
        rframes = []
        for i, f in enumerate(frames):
            g = dict(f, name=f"review-{i}")
            if i == scene.FRAMES - 1:
                g["duration"] = 1050
            rframes.append(g)
        rrec = recipe(f"{name}-review", w, h, rframes, rdir, animations={"review": {"frames": [f["name"] for f in rframes]}},
                      symbols=getattr(scene, "SYMBOLS", None))
        write_json(rdir / f"{name}-review.json", rrec)
    print("recipes written")


def build_wraps(scene):
    odir = HERE / "out"
    hold = scene.FRAMES - 1
    for variant, (w, h) in scene.VARIANTS.items():
        name = variant_name(scene, variant)
        kind = scene.KIND if variant == "regular" else f"{scene.KIND}-{variant}"
        for still in (False, True):
            spec = {"out": f"{name}{'-still' if still else ''}.svg", "kind": kind, "width": w, "height": h,
                    "scale": 2, "radius": 6, "title": scene.TITLE, "desc": scene.DESC}
            if still:
                spec["static"] = True
            spec["layers"] = [{"sheet": f"{name}/{name}.png", "atlas": f"{name}/{name}.atlas.json", "animation": name,
                               "recipe": f"../recipes/{name}.json", "x": 0, "y": 0, "still": hold}]
            write_json(odir / f"{name}{'-still' if still else ''}.wrap.json", spec, compact=False)
    print("wraps written")


def build_sources(scene):
    srcs = scene.sources() if hasattr(scene, "sources") else {}
    for stem, src in srcs.items():
        write_json(HERE / "out" / "fluids" / f"{stem}.fluid.json", src, compact=False)
    print(f"{len(srcs)} fluid sources written")


def main():
    scene = load_scene()
    stage = sys.argv[1]
    {"sources": build_sources, "recipes": build_recipes, "wraps": build_wraps}[stage](scene)


if __name__ == "__main__":
    main()
