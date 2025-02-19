import wot_core from "@node-wot/core";
import wot_http from "@node-wot/binding-http";

const { HttpClientFactory, HttpServer } = wot_http;
const { Servient } = wot_core;

function main() {
    const server = new Servient();
    server.addServer(
        new HttpServer({
            port: 8081, // (default 8080)
        }),
    );

    let count: number;

    server.start().then((WoT) => {
        WoT.produce({
            title: "MyCounter",
            properties: {
                count: {
                    type: "integer",
                },
            },
        }).then((thing) => {
            console.log(`Produced ${thing.getThingDescription().title}`);

            // init property value
            count = 0;
            // set property handlers (using async-await)
            // deno-lint-ignore require-await
            thing.setPropertyReadHandler("count", async () => count);
            thing.setPropertyWriteHandler("count", async (intOutput) => {
                const value = await intOutput.value();
                if (typeof value === "number") {
                    count = value;
                }

                return undefined;
            });

            // expose the thing
            thing.expose().then(() => {
                console.info(`${thing.getThingDescription().title} ready`);
                console.info(
                    `TD : ${
                        JSON.stringify(thing.getThingDescription(), null, 2)
                    }`,
                );
            });
        });
    });

    const client = new Servient();
    client.addClientFactory(new HttpClientFactory());
    client.start().then(async (WoT) => {
        try {
            const td = await WoT.requestThingDescription(
                "http://localhost:8081/mycounter",
            );

            const thing = await WoT.consume(td);
            console.info(`Consumed ${thing.getThingDescription().title}`);

            let i: number = 0;

            while (true) {
                // read property
                const count = await thing.readProperty("count");
                const count_value = await count.value();
                console.info(`count: ${count_value}`);

                // write property
                await thing.writeProperty("count", i++);

                // wait 2 seconds
                await new Promise((r) => setTimeout(r, 5000));
            }
        } catch (err) {
            console.error(err);
        }
    });
}

if (import.meta.main) {
    main();
}
