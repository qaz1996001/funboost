#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import grpc

# Import generated protobuf files
import funboost_grpc_pb2
import funboost_grpc_pb2_grpc
import time

def run_client():
    """
    Run gRPC client
    """
    # Connect to server
    with grpc.insecure_channel('localhost:50051') as channel:
        # Create stub
        stub = funboost_grpc_pb2_grpc.FunboostBrokerServiceStub(channel)
        time_start = time.time()
        for i in range(10000):
            # Create request
            request = funboost_grpc_pb2.FunboostGrpcRequest(json_req='{"b":2}')
            
            try:
                # Call remote method
                response = stub.Call(request)
                print(f"Server response: {response.json_resp}")
            except grpc.RpcError as e:
                print(f"gRPC call failed: {e}")
        time_end = time.time()
        print(f"gRPC call duration: {time_end - time_start} seconds")







if __name__ == '__main__':
    print("=== gRPC Client Test ===")
    print("1. Simple test")
   
    run_client()
    
    # print("\n2. Interactive test")
    # interactive_client()
