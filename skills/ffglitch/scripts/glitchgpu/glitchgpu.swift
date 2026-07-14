// glitchgpu — Metal compute post-effects for the FFglitch pipeline.
//
// Reads raw BGRA frames on stdin, runs an MSL compute kernel per frame on the
// GPU, writes raw BGRA to stdout. Composable with ffmpeg/ffgac pipes, so it
// works directly on raw .m2v glitch masters (which AVFoundation can't open):
//
//   ffmpeg -i mosh.m2v -f rawvideo -pix_fmt bgra - \
//   | ./glitchgpu --size 320x240 --fx trails --decay 0.92 \
//   | ffmpeg -f rawvideo -pix_fmt bgra -s 320x240 -r 25 -i - \
//       -c:v prores_videotoolbox -profile:v hq out.mov
//
// Build:   swiftc -O glitchgpu.swift -o glitchgpu
//
// Effects (--fx):
//   chroma   RGB split, stronger toward frame edges         (--gain px)
//   trails   video-feedback ghosting: max(cur, hist*decay)  (--decay 0..1)
//   mvwarp   displace pixels by FFglitch motion vectors     (--mv mv.json --gain x)
//   scan     CRT scanlines + sine row jitter                (--gain strength)
//   sort     true per-scanline pixel sort: contiguous runs of pixels whose
//            luma falls in [--lo, --hi] are sorted by luma (bitonic sort in
//            threadgroup memory); everything outside a run stays put.
//            Max width 4096 (threadgroup memory limit).   (--lo 0.25 --hi 0.8)
//
// mvwarp consumes `ffedit -f mv -e mv.json` output directly — the glitch
// clip's own motion field, or any other clip's, driving a pixel-space warp.

import Foundation
import Metal

// ---------------------------------------------------------------- args

var width = 0, height = 0
var fx = "chroma"
var gain: Float = 1.0
var decay: Float = 0.9
var lo: Float = 0.25
var hi: Float = 0.80
var mvPath: String? = nil

var it = CommandLine.arguments.dropFirst().makeIterator()
while let arg = it.next() {
    func value() -> String {
        guard let v = it.next() else { die("missing value for \(arg)") }
        return v
    }
    switch arg {
    case "--size":
        let parts = value().split(separator: "x")
        guard parts.count == 2, let w = Int(parts[0]), let h = Int(parts[1])
        else { die("--size expects WxH") }
        width = w; height = h
    case "--fx": fx = value()
    case "--gain": gain = Float(value()) ?? 1.0
    case "--decay": decay = Float(value()) ?? 0.9
    case "--lo": lo = Float(value()) ?? 0.25
    case "--hi": hi = Float(value()) ?? 0.80
    case "--mv": mvPath = value()
    case "-h", "--help":
        FileHandle.standardError.write(Data("""
        usage: glitchgpu --size WxH --fx chroma|trails|mvwarp|scan|sort
                         [--gain F] [--decay F] [--lo F] [--hi F] [--mv mv.json]
        raw BGRA frames on stdin -> effect -> raw BGRA on stdout

        """.utf8))
        exit(0)
    default: die("unknown arg \(arg)")
    }
}

func die(_ msg: String) -> Never {
    FileHandle.standardError.write(Data("glitchgpu: \(msg)\n".utf8))
    exit(1)
}

guard width > 0, height > 0 else { die("--size WxH is required") }
let kernels = ["chroma", "trails", "mvwarp", "scan", "sort"]
guard kernels.contains(fx) else { die("--fx must be one of \(kernels.joined(separator: "|"))") }
if fx == "mvwarp" && mvPath == nil { die("mvwarp needs --mv mv.json") }
if fx == "sort" && width > 4096 { die("sort supports width <= 4096 (threadgroup memory)") }

// ---------------------------------------------------------------- MSL

let msl = """
#include <metal_stdlib>
using namespace metal;

struct Params { float gain; float decay; uint frame; float lo; float hi; uint n2; };

kernel void chroma(texture2d<float, access::sample> src [[texture(0)]],
                   texture2d<float, access::write>  dst [[texture(1)]],
                   constant Params& p [[buffer(0)]],
                   uint2 gid [[thread_position_in_grid]]) {
    if (gid.x >= dst.get_width() || gid.y >= dst.get_height()) return;
    constexpr sampler s(filter::linear, address::clamp_to_edge);
    float2 size = float2(dst.get_width(), dst.get_height());
    float2 uv = (float2(gid) + 0.5) / size;
    // shift in pixels, growing toward left/right edges
    float px = p.gain * 2.0 * (uv.x - 0.5);
    float2 off = float2(px / size.x, 0.0);
    float  r = src.sample(s, uv - off).r;
    float4 c = src.sample(s, uv);
    float  b = src.sample(s, uv + off).b;
    dst.write(float4(r, c.g, b, 1.0), gid);
}

kernel void trails(texture2d<float, access::read>  src  [[texture(0)]],
                   texture2d<float, access::write> dst  [[texture(1)]],
                   texture2d<float, access::read>  hist [[texture(2)]],
                   constant Params& p [[buffer(0)]],
                   uint2 gid [[thread_position_in_grid]]) {
    if (gid.x >= dst.get_width() || gid.y >= dst.get_height()) return;
    float4 cur = src.read(gid);
    float4 old = hist.read(gid) * p.decay;
    float4 outc = max(cur, old);          // classic video-feedback ghosting
    outc.a = 1.0;
    dst.write(outc, gid);
}

kernel void mvwarp(texture2d<float, access::sample> src [[texture(0)]],
                   texture2d<float, access::write>  dst [[texture(1)]],
                   texture2d<float, access::sample> mv  [[texture(2)]],
                   constant Params& p [[buffer(0)]],
                   uint2 gid [[thread_position_in_grid]]) {
    if (gid.x >= dst.get_width() || gid.y >= dst.get_height()) return;
    constexpr sampler s(filter::linear, address::clamp_to_edge);
    float2 size = float2(dst.get_width(), dst.get_height());
    float2 uv = (float2(gid) + 0.5) / size;
    float2 v = mv.sample(s, uv).rg * 0.5;   // half-pel -> pixels
    float2 duv = v * p.gain / size;
    dst.write(src.sample(s, uv + duv), gid);
}

// True pixel sort, one threadgroup per scanline. Trigger: luma in [lo, hi].
// Composite key = span_start * 65536 + luma keeps non-span pixels anchored at
// their own index while span pixels sort by luma within their span — a single
// bitonic sort per row does both. keys/colors in threadgroup memory
// (16 KB + 16 KB at the 4096-px cap).
kernel void sort(texture2d<float, access::read>  src [[texture(0)]],
                 texture2d<float, access::write> dst [[texture(1)]],
                 constant Params& p [[buffer(0)]],
                 threadgroup uint* keys   [[threadgroup(0)]],
                 threadgroup uint* colors [[threadgroup(1)]],
                 uint2 tpos [[thread_position_in_grid]],
                 uint2 tptg [[threads_per_threadgroup]]) {
    const uint W  = src.get_width();
    const uint n2 = p.n2;
    const uint tid = tpos.x, tcount = tptg.x;
    const uint row = tpos.y;

    // load row; pad to power-of-two with max-key sentinels (sort to the end)
    for (uint i = tid; i < n2; i += tcount) {
        if (i < W) {
            float4 c = src.read(uint2(i, row));
            colors[i] = (uint(c.a * 255.0) << 24) | (uint(c.r * 255.0) << 16)
                      | (uint(c.g * 255.0) << 8)  |  uint(c.b * 255.0);
        } else {
            colors[i] = 0;
        }
        keys[i] = 0xFFFFFFFFu;
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

    // serial span scan (one thread; W <= 4096 trivial ops)
    if (tid == 0) {
        int span_start = -1;
        for (uint i = 0; i < W; i++) {
            uint c = colors[i];
            float luma = (0.299 * float((c >> 16) & 0xFF)
                        + 0.587 * float((c >> 8) & 0xFF)
                        + 0.114 * float(c & 0xFF)) / 255.0;
            bool trig = (luma >= p.lo) && (luma <= p.hi);
            if (trig) {
                if (span_start < 0) span_start = int(i);
                keys[i] = uint(span_start) * 65536u + uint(luma * 255.0) + 1u;
            } else {
                span_start = -1;
                keys[i] = i * 65536u;
            }
        }
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

    // bitonic sort (ascending) over n2 elements, keys carry colors along
    for (uint k = 2; k <= n2; k <<= 1) {
        for (uint j = k >> 1; j > 0; j >>= 1) {
            for (uint i = tid; i < n2; i += tcount) {
                uint ixj = i ^ j;
                if (ixj > i) {
                    bool up = ((i & k) == 0);
                    uint ka = keys[i], kb = keys[ixj];
                    if ((up && ka > kb) || (!up && ka < kb)) {
                        keys[i] = kb; keys[ixj] = ka;
                        uint ca = colors[i];
                        colors[i] = colors[ixj]; colors[ixj] = ca;
                    }
                }
            }
            threadgroup_barrier(mem_flags::mem_threadgroup);
        }
    }

    for (uint i = tid; i < W; i += tcount) {
        uint c = colors[i];
        dst.write(float4(float((c >> 16) & 0xFF) / 255.0,
                         float((c >> 8) & 0xFF) / 255.0,
                         float(c & 0xFF) / 255.0, 1.0), uint2(i, row));
    }
}

kernel void scan(texture2d<float, access::sample> src [[texture(0)]],
                 texture2d<float, access::write>  dst [[texture(1)]],
                 constant Params& p [[buffer(0)]],
                 uint2 gid [[thread_position_in_grid]]) {
    if (gid.x >= dst.get_width() || gid.y >= dst.get_height()) return;
    constexpr sampler s(filter::linear, address::clamp_to_edge);
    float2 size = float2(dst.get_width(), dst.get_height());
    // sine row jitter, phase animated by frame number
    float jit = p.gain * sin(float(gid.y) * 0.35 + float(p.frame) * 0.2);
    float2 uv = (float2(gid) + float2(0.5 + jit, 0.5)) / size;
    float4 c = src.sample(s, uv);
    float dark = (gid.y % 2 == 0) ? 1.0 : max(0.0, 1.0 - 0.25 * p.gain);
    c.rgb *= dark;
    c.a = 1.0;
    dst.write(c, gid);
}
"""

// ---------------------------------------------------------------- Metal setup

guard let dev = MTLCreateSystemDefaultDevice() else { die("no Metal device") }
let lib: MTLLibrary
do { lib = try dev.makeLibrary(source: msl, options: nil) }
catch { die("MSL compile failed: \(error)") }
guard let fn = lib.makeFunction(name: fx) else { die("kernel \(fx) missing") }
let pso: MTLComputePipelineState
do { pso = try dev.makeComputePipelineState(function: fn) }
catch { die("pipeline failed: \(error)") }
guard let queue = dev.makeCommandQueue() else { die("no command queue") }

func makeTex(_ w: Int, _ h: Int, _ fmt: MTLPixelFormat,
             _ usage: MTLTextureUsage) -> MTLTexture {
    let d = MTLTextureDescriptor.texture2DDescriptor(
        pixelFormat: fmt, width: w, height: h, mipmapped: false)
    d.usage = usage
    d.storageMode = .shared   // unified memory: no blits for CPU I/O
    guard let t = dev.makeTexture(descriptor: d) else { die("texture alloc failed") }
    return t
}

let srcTex = makeTex(width, height, .bgra8Unorm, [.shaderRead])
let dstTex = makeTex(width, height, .bgra8Unorm, [.shaderWrite, .shaderRead])
let histTex = makeTex(width, height, .bgra8Unorm, [.shaderRead, .shaderWrite])

// ---------------------------------------------------------------- MV data

// Per-frame RG16Float textures, one texel per macroblock, values in half-pel.
struct MVFrames {
    var textures: [MTLTexture?] = []   // nil = no forward MVs (intra frame)
    var zero: MTLTexture
}
var mvFrames: MVFrames? = nil

if let path = mvPath {
    guard let jdata = FileManager.default.contents(atPath: path),
          let root = try? JSONSerialization.jsonObject(with: jdata) as? [String: Any],
          let streams = root["streams"] as? [[String: Any]],
          let frames = streams.first?["frames"] as? [[String: Any]]
    else { die("cannot parse \(path)") }

    var out = MVFrames(zero: makeTex(1, 1, .rg16Float, [.shaderRead]))
    let zeroPix = [Float16](repeating: 0, count: 2)
    zeroPix.withUnsafeBytes {
        out.zero.replace(region: MTLRegionMake2D(0, 0, 1, 1), mipmapLevel: 0,
                         withBytes: $0.baseAddress!, bytesPerRow: 4)
    }
    for f in frames {
        guard let mv = f["mv"] as? [String: Any],
              let grid = mv["forward"] as? [[Any]], !grid.isEmpty
        else { out.textures.append(nil); continue }
        let rows = grid.count, cols = grid[0].count
        var buf = [Float16](repeating: 0, count: rows * cols * 2)
        for (y, row) in grid.enumerated() {
            for (x, cell) in row.enumerated() {
                if let pair = cell as? [NSNumber], pair.count == 2 {
                    let i = (y * cols + x) * 2
                    buf[i]     = Float16(pair[0].floatValue)
                    buf[i + 1] = Float16(pair[1].floatValue)
                }
            }
        }
        let t = makeTex(cols, rows, .rg16Float, [.shaderRead])
        buf.withUnsafeBytes {
            t.replace(region: MTLRegionMake2D(0, 0, cols, rows), mipmapLevel: 0,
                      withBytes: $0.baseAddress!, bytesPerRow: cols * 4)
        }
        out.textures.append(t)
    }
    FileHandle.standardError.write(
        Data("glitchgpu: loaded \(out.textures.count) MV frames from \(path)\n".utf8))
    mvFrames = out
}

// ---------------------------------------------------------------- frame loop

let frameBytes = width * height * 4
let stdinFH = FileHandle.standardInput
let stdoutFH = FileHandle.standardOutput

func readFrame() -> Data? {
    var data = Data(capacity: frameBytes)
    while data.count < frameBytes {
        guard let chunk = try? stdinFH.read(upToCount: frameBytes - data.count),
              !chunk.isEmpty else {
            return nil   // EOF (drops a partial trailing frame)
        }
        data.append(chunk)
    }
    return data
}

struct Params {
    var gain: Float; var decay: Float; var frame: UInt32
    var lo: Float; var hi: Float; var n2: UInt32
}

// next power of two >= width, for the bitonic sort
var n2: UInt32 = 1
while n2 < UInt32(width) { n2 <<= 1 }

var outBuf = [UInt8](repeating: 0, count: frameBytes)
var frameNum: UInt32 = 0

while let frame = readFrame() {
    frame.withUnsafeBytes {
        srcTex.replace(region: MTLRegionMake2D(0, 0, width, height),
                       mipmapLevel: 0, withBytes: $0.baseAddress!,
                       bytesPerRow: width * 4)
    }

    guard let cb = queue.makeCommandBuffer(),
          let enc = cb.makeComputeCommandEncoder() else { die("encoder failed") }
    enc.setComputePipelineState(pso)
    enc.setTexture(srcTex, index: 0)
    enc.setTexture(dstTex, index: 1)
    if fx == "trails" { enc.setTexture(histTex, index: 2) }
    if fx == "mvwarp", let mvf = mvFrames {
        let n = Int(frameNum)
        let t = n < mvf.textures.count ? (mvf.textures[n] ?? mvf.zero) : mvf.zero
        enc.setTexture(t, index: 2)
    }
    var p = Params(gain: gain, decay: decay, frame: frameNum, lo: lo, hi: hi, n2: n2)
    enc.setBytes(&p, length: MemoryLayout<Params>.stride, index: 0)
    if fx == "sort" {
        // one threadgroup per scanline; keys + colors in threadgroup memory
        enc.setThreadgroupMemoryLength(Int(n2) * 4, index: 0)
        enc.setThreadgroupMemoryLength(Int(n2) * 4, index: 1)
        enc.dispatchThreadgroups(MTLSize(width: 1, height: height, depth: 1),
                                 threadsPerThreadgroup: MTLSize(width: 256, height: 1, depth: 1))
    } else {
        enc.dispatchThreads(MTLSize(width: width, height: height, depth: 1),
                            threadsPerThreadgroup: MTLSize(width: 16, height: 16, depth: 1))
    }
    enc.endEncoding()

    if fx == "trails" {   // dst becomes next frame's history
        guard let blit = cb.makeBlitCommandEncoder() else { die("blit failed") }
        blit.copy(from: dstTex, to: histTex)
        blit.endEncoding()
    }

    cb.commit()
    cb.waitUntilCompleted()

    dstTex.getBytes(&outBuf, bytesPerRow: width * 4,
                    from: MTLRegionMake2D(0, 0, width, height), mipmapLevel: 0)
    stdoutFH.write(Data(outBuf))
    frameNum += 1
}

FileHandle.standardError.write(Data("glitchgpu: processed \(frameNum) frames\n".utf8))
