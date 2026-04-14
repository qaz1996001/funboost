#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading

import grpc
from concurrent import futures
import time

# Import generated protobuf files
import funboost_grpc_pb2
import funboost_grpc_pb2_grpc


class FunboostGrpcServicer(funboost_grpc_pb2_grpc.FunboostBrokerServiceServicer):
    """
    HelloService implementation class
    """
    
    def Call(self, request, context):
        """
        Implement the SayHello method
        """
        event = threading.Event()
        res = process_msg(request.json_req,event)
        event.wait(600)

        return funboost_grpc_pb2.FunboostGrpcResponse(json_resp=res)


def process_msg(x,event:threading.Event):
    time.sleep(3)
    event.set()
    return f'{{"respx":{x}}}'


def serve():
    """
    Start the gRPC server
    """
    # Create server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add service
    funboost_grpc_pb2_grpc.add_FunboostBrokerServiceServicer_to_server(FunboostGrpcServicer(), server)
    
    # Bind port
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    
    # Start server
    server.start()
    print(f"gRPC server started, listening on: {listen_addr}")
    
    try:
        while True:
            time.sleep(86400)  # Keep server running
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop(0)


if __name__ == '__main__':
    serve()
