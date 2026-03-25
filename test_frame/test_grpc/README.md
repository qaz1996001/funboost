# gRPC Demo

This is the simplest gRPC example, demonstrating how to create a gRPC server and client.

## File Descriptions

- `hello.proto` - Protobuf definition file, defining the service interface and message format
- `server.py` - gRPC server implementation
- `client.py` - gRPC client implementation
- `generate_pb.py` - Script for generating protobuf files
- `requirements.txt` - Python dependencies

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate protobuf files

```bash
python generate_pb.py
```

This will generate the `hello_pb2.py` and `hello_pb2_grpc.py` files.

### 3. Start the server

```bash
python server.py
```

The server will start listening on `localhost:50051`.

### 4. Run the client

In another terminal, run:

```bash
python client.py
```

## Example Output

**Server side:**
```
gRPC server started, listening on: [::]:50051
```

**Client side:**
```
=== gRPC Client Test ===
1. Simple test
Server response: Hello, World!

2. Interactive test
Enter your name (type 'quit' to exit): Alice
Server response: Hello, Alice!
Enter your name (type 'quit' to exit): quit
```

## How It Works

1. **Proto file definition**: Defines the `HelloService` service containing the `SayHello` method
2. **Server**: Implements `HelloService`, receives client requests, and returns a greeting message
3. **Client**: Connects to the server, sends a request, and receives the response

This is the most basic gRPC example, showing the fundamental gRPC workflow.
