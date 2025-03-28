# Smart Sensor Actuator

## Architecture Overview

The **Smart Sensor Actuator (SSA)** project builds on the **W3C Web of Things (WoT)** standard and proposes a **Thing Model (TM)** centric
framework for large-scale (I)IoT deployments.

The SSA architecture has two main components: the _Embedded Core_ and the _Edge Connector_.
- The Smart Sensor Actuator Embedded Core (SSA-EmbC) outlines a platform-agnostic interaction model and API for IoT end devices (typically low-power
embedded platforms). The main design philosophy for this component is to facilitate the development of applications that exchange information according
to WoT's Interaction Affordances API. Devices that run the SSA-EmbC are designated as SSA Things.
- The SSA Edge Connector (EdgeC) is meant to be deployed at network edge nodes to automate the discovery and configuration of (new) SSA Things and
to instantiate the Thing Descriptions of SSA Things based on the TM representing their functionality.

IoT networks that operate according to the benefit from the following feature set:
 - **Semantic interoperability of data**, facilitated by JSON-LD, RDF, and the WoT context.
 - **Standardized communication interfaces** between IoT devices powered by the WoT's properties-actions-events paradigm.
 - **Automated bootstrapping** of new devices into the network via the SSA Edge Connectors and the registration protocol.
 - **Over-the-air updates** of application code and/or device configuration using the tools provided by the SSA Embedded Core.

SSA IoT Networks also benefit from all the advantages of using Linked Data and the WoT. These include:
 - The ability to dynamically discover and filter devices connected to the networks based on their characteristics.
 - Easy data model extension via the JSON-LD context.
 - Compatibility with graph and linked data database engines. 
 - Data interoperability with external networks or services without compromising semantic integrity.

### SSA Network Components

Apart from the _EmbC_ and the _EdgeC_, a Smart Sensor Actuator network counts on some more building blocks to enable its operation.
TODO....


### Building blocks of an SSA Thing

While the TM is an (optional) extension of the WoT's TD, SSA Things must necessarily be associated with a valid Thing Model available to the network.
A Thing's thing model dictates what features the thing implements and provides a template for the instantiation of its unique TD during the registration 
phase.

The TM of an SSA Thing also dictates its basic characteristics and its supported feature set.

### SSA Thing Model Framework

An SSA Thing Model is a composition of 2 or more Thing Models. The Platform model, the Runtime/Core model, and one (or more) Application Models.
- The platform model describes the computational platform and peripherals of the SSA Thing.
- The runtime model represents the SSA-EmbC instance running on the SSA Thing and its core (immutable) feature set.
- The application model represents an instrumentation of the runtime of the SSA Thing to provide additional affordances and can be dynamically changed
at runtime by the SSA Network.

![Thing Model Class Diagram](uml/tm_relations.png)
