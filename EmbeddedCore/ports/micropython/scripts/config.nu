export-env {
    $env.citylink_config = {
        reg: {
            tm: "http://example.org/manifest.json",
        }
        network: {
            ssid: "myWiFi"
            password: "myWiFiPassword"
        }
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
    }
}

export def main --env [] {
    $env.citylink_config
}

export def set --env [] {
    let input = $in
    match ($input | describe -d | get type) {
        record => { $env.citylink_config = $input}
        _ => { }
    }
}

export def upload --env [] {
    let conf_file = mktemp --suffix .json
    $env.citylink_config | to json -r | save -f $conf_file
    mpremote cp $conf_file :config/config.json
    rm $conf_file
}
