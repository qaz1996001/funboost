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
    Optimized implementation class for HelloService
    """

    def SayHello(self, request, context):
        """
        Implement SayHello method - optimized version
        """
        # Return directly, reducing string concatenation overhead
        return hello_pb2.HelloResponse(message=f"Hello, {request.name}!")


def serve():
    """
    Start the optimized gRPC server
    """
    # Optimized server options
    options = [
        ('grpc.keepalive_time_ms', 10000),
        ('grpc.keepalive_timeout_ms', 5000),
        ('grpc.keepalive_permit_without_calls', True),
        ('grpc.http2.max_pings_without_data', 0),
        ('grpc.http2.min_time_between_pings_ms', 10000),
        ('grpc.http2.min_ping_interval_without_data_ms', 300000),
        ('grpc.max_connection_idle_ms', 30000),
        ('grpc.max_receive_message_length', 1024 * 1024 * 4),  # 4MB
        ('grpc.max_send_message_length', 1024 * 1024 * 4),     # 4MB
    ]

    # Increase thread pool size to handle more concurrent requests
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=50),  # Increased to 50 worker threads
        options=options
    )

    # Add service
    hello_pb2_grpc.add_HelloServiceServicer_to_server(HelloServicer(), server)

    # Bind port
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)

    # Start server
    server.start()
    print(f"Optimized gRPC server started, listening at: {listen_addr}")
    print(f"Worker threads: 50")
    print("Press Ctrl+C to stop the server")

    try:
        while True:
            time.sleep(86400)  # Keep server running
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop(0)


if __name__ == '__main__':
    serve()
