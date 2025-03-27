# SmartSensorActuator

## Architecture Overview

The **Smart Sensor Actuator (SSA)** project builds on the **W3C Web of Things (WoT)** standard and proposes a **Thing Model (TM)** centric
framework for large-scale (I)IoT deployments.

The SSA architecture has two main components: the _Embedded Core_ and the _Edge Connector_.
- The Smart Sensor Actuator Embedded Core (SSA-EmbC) outlines a platform-agnostic interaction model and API for IoT end devices (typically low
power embedded platforms).
The main design philosophy for this component is to facilitate the development of applications that exchange information according to the WoT's
Interaction Affordances API. Devices that run the SSA-EmbC are designated as SSA Things.
- The SSA Edge Connector is meant to be deployed at network edge nodes to automate the discovery and configuration of (new) SSA Things and
to instantiate the Thing Descriptions of SSA Things based on the TM representing their functionality.

## Thing Models for lifecycle management.

While the main focus of the W3C WoT Standard is the Thing Description, when dealing with the orchestration of large dynamic IoT systems, the TM can be
a powerful tool for managing the lifecycle of the agents in the network.

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
