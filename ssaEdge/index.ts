import { HttpServer } from "@node-wot/binding-http";
import { Servient } from "@node-wot/core";

// create Servient add HTTP binding with port configuration
const servient = new Servient();
servient.addServer(
	new HttpServer({
		port: 8081, // (default 8080)
	}),
);

let count;

servient.start().then((WoT) => {
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
		thing.setPropertyReadHandler("count", async () => count);
		thing.setPropertyWriteHandler("count", async (intOutput) => {
			count = await intOutput.value();
			return undefined;
		});

		// expose the thing
		thing.expose().then(() => {
			console.info(`${thing.getThingDescription().title} ready`);
			console.info(`TD : ${JSON.stringify(thing.getThingDescription())}`);
		});
	});
});
