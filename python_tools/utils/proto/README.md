# Using the protobuf for the Beatgrids

The Beatgrids and Keys are defined using [protobuf](https://protobuf.dev/getting-started/pythontutorial/).

I took the [proto file used in Mixxx library](https://github.com/mixxxdj/mixxx/blob/main/src/proto/)

Then used the following commands to generate the corresponding Python file:

```
protoc --python_out=. beats.proto
protoc --python_out=. keys.proto
```