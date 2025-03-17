export def msgpack [example: path] {
    let script = open $example
    let crc32 = $script | crc32 | into int -r 16 | format number | get lowerhex

    {script: $script, crc32: $crc32 } | to msgpack
}

export def msgpack_sub [topic?:string = "ssa/registration/umqtt_core"] {
    print "Subscribing to mosquitto topic 'ssa/registration/umqtt_core'..."
    mosquitto_sub -v -t $topic
    | each { |$it|
        # Split on the first space: topic is the first token,
        # the remainder is the raw (binary) message.
        let parts = $it | bytes split " "
        let topic = $parts.0 | decode
        let msg = $parts | skip 1 | reduce { |$it, $acc| $acc | bytes add $it --end}
        print ({topic: $topic, msg: ($msg | from msgpack --objects | get 0)} | to json)
    } | ignore
}

export def msgpack_pub [topic?:string = "ssa/registration/umqtt_core"] {
    $in | to msgpack | mosquitto_pub -t $topic -s
}
