#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import grpc

# Import generated protobuf files
import hello_pb2
import hello_pb2_grpc
import time

def run_client():
    """
    Run gRPC client
    """
    # Connect to the server
    with grpc.insecure_channel('localhost:50051') as channel:
        # Create stub
        stub = hello_pb2_grpc.HelloServiceStub(channel)
        time_start = time.time()
        for i in range(10000):
            # Create request
            request = hello_pb2.HelloRequest(name=f"World_{i}")

            try:
                # Call remote method
                response = stub.SayHello(request)
                # print(f"Server response: {response.message}")
            except grpc.RpcError as e:
                print(f"gRPC call failed: {e}")
        time_end = time.time()
        print(f"gRPC call time: {time_end - time_start} seconds")


def interactive_client():
    """
    Interactive client
    """
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.HelloServiceStub(channel)

        while True:
            name = input("Please enter your name (type 'quit' to exit): ")
            if name.lower() == 'quit':
                break

            request = hello_pb2.HelloRequest(name=name)

            try:
                response = stub.SayHello(request)
                print(f"Server response: {response.message}")
            except grpc.RpcError as e:
                print(f"gRPC call failed: {e}")
        



if __name__ == '__main__':
    print("=== gRPC Client Test ===")
    print("1. Simple test")
   
    run_client()
    
    # print("\n2. 交互式测试")
    # interactive_client()
