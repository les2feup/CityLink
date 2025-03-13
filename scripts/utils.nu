export def msgpack [example: path] {
    let script = open $example
    let crc32 = $script | crc32 | into int -r 16 | format number | get lowerhex

    {script: $script, crc32: $crc32 } | to msgpack
}
