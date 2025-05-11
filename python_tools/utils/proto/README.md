# Using the protobuf for the Beatgrids

The Beatgrids and Keys are defined using [protobuf](https://protobuf.dev/getting-started/pythontutorial/).

I took the [proto file used in Mixxx library](https://github.com/mixxxdj/mixxx/blob/main/src/proto/)

Then used the command `protoc --python_out=. proto_file.proto` to generate the corresponding Python file.
