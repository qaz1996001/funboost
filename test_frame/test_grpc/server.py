#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import grpc
from concurrent import futures
import time

# Import generated protobuf files
import hello_pb2
import hello_pb2_grpc


class HelloServicer(hello_pb2_grpc.HelloServiceServicer):
    """
    Implementation class for HelloService
    """

    def SayHello(self, request, context):
        """
        Implement SayHello method
        """
        message = f"Hello, {request.name}!"
        return hello_pb2.HelloResponse(message=message)


def serve():
    """
    Start gRPC server
    """
    # Create server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add service
    hello_pb2_grpc.add_HelloServiceServicer_to_server(HelloServicer(), server)

    # Bind port
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)

    # Start server
    server.start()
    print(f"gRPC server started, listening at: {listen_addr}")

    try:
        while True:
            time.sleep(86400)  # Keep server running
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop(0)


if __name__ == '__main__':
    serve()
