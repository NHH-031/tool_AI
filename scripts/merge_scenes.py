#!/usr/bin/env python3
"""
多幕合并：把各场景的白板动画 MP4 按顺序硬切拼接成一条完整视频。

优先用系统 ffmpeg 无损拼接（-c copy，不重编码）；各片尺寸/编码不一致或无
ffmpeg 时，回退到 PyAV 逐帧重编码并缩放补边到第一段尺寸。单片仍保留。

用法：
  <ENV_PY> merge_scenes.py --inputs a.mp4 b.mp4 c.mp4 --output final.mp4
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _ffmpeg_concat_copy(inputs: list[Path], output: Path) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return False
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in inputs:
            f.write(f"file '{p.resolve().as_posix()}'\n")
        list_path = Path(f.name)
    try:
        res = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(list_path), "-c", "copy", str(output)],
            capture_output=True, text=True,
        )
        if res.returncode == 0:
            print(f"  ffmpeg 无损拼接完成: {output}")
            return True
        print(f"  [warn] ffmpeg -c copy 失败，尝试重编码: {res.stderr.strip()[:200]}")
        res = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(list_path), "-c:v", "libx264", "-crf", "20",
             "-pix_fmt", "yuv420p", "-vf", "scale='trunc(iw/2)*2':'trunc(ih/2)*2'", str(output)],
            capture_output=True, text=True,
        )
        if res.returncode == 0:
            print(f"  ffmpeg 重编码拼接完成: {output}")
            return True
        print(f"  [warn] ffmpeg 重编码也失败: {res.stderr.strip()[:200]}")
        return False
    finally:
        list_path.unlink(missing_ok=True)


def _pyav_concat(inputs: list[Path], output: Path) -> bool:
    try:
        import av
    except ImportError:
        return False
    from fractions import Fraction

    first = av.open(str(inputs[0]))
    vs = first.streams.video[0]
    w, h = vs.codec_context.width, vs.codec_context.height
    rate = vs.average_rate
    has_audio = len(first.streams.audio) > 0
    first.close()

    tb = Fraction(rate.denominator, rate.numerator)
    out = av.open(str(output), mode="w")
    v_out = out.add_stream("h264", rate=rate)
    v_out.width, v_out.height = w, h
    v_out.pix_fmt = "yuv420p"
    v_out.time_base = tb
    v_out.options = {"crf": "24", "preset": "medium"}

    a_out = None
    resampler = None
    if has_audio:
        a_out = out.add_stream("aac", rate=24000)
        a_out.format = "fltp"
        a_out.layout = "mono"
        resampler = av.AudioResampler(format="fltp", layout="mono", rate=24000)

    v_pts = 0
    a_pts = 0
    for p in inputs:
        cont = av.open(str(p))
        # 1. Decode & encode video frames
        for frame in cont.decode(video=0):
            if frame.width != w or frame.height != h:
                frame = frame.reformat(width=w, height=h)
            frame.pts = v_pts
            frame.time_base = tb
            v_pts += 1
            for pkt in v_out.encode(frame):
                out.mux(pkt)

        # 2. Decode & encode audio frames if available
        if has_audio and len(cont.streams.audio) > 0:
            cont.seek(0)
            for a_frame in cont.decode(audio=0):
                resampled_frames = resampler.resample(a_frame)
                for rf in resampled_frames:
                    rf.pts = a_pts
                    a_pts += rf.samples
                    for pkt in a_out.encode(rf):
                        out.mux(pkt)
        cont.close()

    for pkt in v_out.encode(None):
        out.mux(pkt)
    if a_out is not None:
        if resampler:
            for rf in resampler.resample(None):
                rf.pts = a_pts
                a_pts += rf.samples
                for pkt in a_out.encode(rf):
                    out.mux(pkt)
        for pkt in a_out.encode(None):
            out.mux(pkt)

    out.close()
    print(f"  PyAV audio/video concat complete: {output}")
    return True


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="按顺序合并多幕白板动画 MP4")
    p.add_argument("--inputs", nargs="+", required=True, help="按播放顺序的 MP4 列表")
    p.add_argument("--output", required=True, help="合并输出路径")
    args = p.parse_args(argv)

    inputs = [Path(x) for x in args.inputs]
    missing = [str(x) for x in inputs if not x.exists()]
    if missing:
        print(f"[err] 缺少输入文件: {', '.join(missing)}", file=sys.stderr)
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if _ffmpeg_concat_copy(inputs, output) or _pyav_concat(inputs, output):
        print(f"OUTPUT={output.resolve()}")
        return 0
    print("[err] 合并失败：系统无 ffmpeg 且 PyAV 不可用", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
