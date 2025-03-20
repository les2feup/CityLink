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

export def gen_config_template [ dir: path = .,
       --json (-j),
       --msgpack (-m)
] {
    let secrets = {
        network : {
            ssid: SSID,
            password: PASSWORD
        }

        runtime.broker: {
            username: "optional-username",
            password: "optional-password"
        }
    }

    let config = {
        runtime: {
            broker: {
                hostname: "mqtt.eclipse.org",
                port: 1883,
                keepalive: 60,
            },
            connection: {
                retries: 3,
                timeout_ms: 1000
            }
        },
        tm: {
            name: "model_name",
            version: {
                instance: "1.0.0",
                model: "1.0.0"
            }
        }
    }

    if $json {
        $config | to json | save -f ($dir + "/config.json")
        $secrets | to json | save -f ($dir + "/secrets.json")
    }

    if $msgpack {
        $config | to msgpack | save -f ($dir + "/config.mpk")
        $secrets | to msgpack | save -f ($dir + "/secrets.mpk")
    }
}

export def flash_config [ dir: path = .,
       --json (-j),
       --msgpack (-m)
] {

    if $json {
        mpremote mkdir :config | ignore
        mpremote cp ($dir + "/config.json") :config/config.json
        mpremote cp ($dir + "/secrets.json") :config/secrets.json
    }

    if $msgpack {
        mpremote mkdir :config | ignore
        mpremote cp ($dir + "/config.mpk") :config/config.mpk
        mpremote cp ($dir + "/secrets.mpk") :config/secrets.mpk
    }
}
