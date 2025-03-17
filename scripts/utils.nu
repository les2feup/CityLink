let uuid = open ssaHAL/config/config.json | get runtime.broker.client_id
let model_name = open ssaHAL/config/config.json | get tm.name

let event_topic = $"ssa/($uuid)/events"
let action_topic = $"ssa/($uuid)/actions"
let property_topic = $"ssa/($uuid)/properties"

export def msgpack_pub [topic: string] {
    $in | to msgpack | mosquitto_pub -t $topic -s
}

export def msgpack_sub [topic: string,
                        --json (-j),
                        --ignore_n (-i): int = 0] {
    let file = mktemp XXXX.mpk
    try {
        loop {
            mosquitto_sub -C (1 + $ignore_n) -t $topic | save -f $file
            let data = open $file | skip $ignore_n | from msgpack --objects | get 0
            let $data = match $json {
                true => ($data | to json)
                false => $data
            }
            print $data
        }
    } catch {
        rm $file
    }
}
