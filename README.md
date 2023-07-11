# FSMLua

This project aims to provide asynchronous execution to Factorio lua code. This is achieved by translating given Lua code, to an event-based finite state machine. This tool is primarily designed for Foyager.

## Background

The provided Factorio modding API and execution environment disables the use of coroutines in order to ensure determinism. For the vast majority of use cases, this is not a problem. In the case of Foyager, the LLM often needs to write scripts to control the player's actions-- some of which take several game ticks to finish. Therefore, some sort of asynchronous functionally is necessary.

In an effort to avoid writing a 3rd party wrapper around the entirety of the Factorio API, as well as providing the simplest possible interface for the LLM to write scripts, we implement a transpiler-like tool to leverage the provided event system from Factorio's modding API to generate functionally asynchronous code.

## Features

We aim to implement as many features in the Lua language as possible. Currently unsupported features are:
- Do/While/Forin/Fornum/Repeat/Break
- Labels & Gotos
- Methods & Invoking methods

# Installing
TODO

# Usage
TODO

