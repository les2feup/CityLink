# Micropython Embedded Core API Specification

This document outlines the external API specification for Micropython Embedded Core implementations.
This specification is based off the umqtt_core proof of concept implementation.

Compliant implementations will be compatible with application code written against this specification.

## Installation

Installing a compliant implementation should result in the following directory structure in the device's virtual filesystem:

```
/boot.py
/citylink
/citylink/core.py
/citylink/ext/
```
